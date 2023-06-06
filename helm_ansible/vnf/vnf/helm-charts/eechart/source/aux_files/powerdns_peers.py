# -*- coding: utf-8 -*-
# @Author: Rafael Direito
# @Date:   2022-08-16 19:04:59
# @Last Modified by:   Daniel Gomes
# @Last Modified time: 2023-02-15 14:30:52

import powerdns
from cryptography.fernet import Fernet
import dns.resolver
import dns.rdataclass
import time
import random
import logging
import json
import os
import sys
sys.path.append('/home/ubuntu/aux_files')
from wg_aux import WGAux
from publish_ts import WG_TS_Publishing
import constants as TS_Constants

# Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)


_vars = json.loads(os.environ.get('ANSIBLE_JSON'))

tunnel_peer_address = _vars['tunnel_peer_address']
save_config = _vars['save_config']
listen_port = _vars['listen_port']
public_key = _vars['public_key']
address = _vars['address']
tunnel_id = _vars['tunnel_id']
tunnel_public_address = _vars['tunnel_public_address']
tunnel_public_port = _vars['tunnel_public_port']
tunnel_allowed_networks = _vars['tunnel_allowed_networks']
netor_ip = _vars['netor_ip']
dns_ip = _vars['dns_ip']
dns_port = _vars['dns_port']
api_port = _vars['dns_api_port']
api_key = _vars['dns_api_key']
zone = _vars['dns_zone']
vsi_id = _vars['vsi_id']
domain = _vars['domain']
encryption_key = _vars['dns_encryption_key']
dns_service_type = _vars['dns_service_type']
dns_protocol = _vars['dns_protocol']
total_num_peers = int(_vars['dns_total_num_peers'])
max_waiting_time = int(_vars['max_waiting_time_for_other_peers_secs'])


class Wg_Peer_Info:

    def __init__(self, domain):
        self.domain = domain
        self.dns_srv_address = None
        self.public_ip = None
        self.public_port = None
        self.private_ip = None
        self.private_port = None
        self.public_key = None
        self.allowed_networks = None
        self.tunnel_peer_address= None
        self.peer_networks = None


class Wg_DNS_SD:

    def __init__(self, netor_ip, dns_ip, dns_port, api_port, api_key, zone,
                 encryption_key):
        self.netor_ip = netor_ip
        self.dns_ip = dns_ip
        self.dns_port = dns_port
        self.api_port = api_port
        self.api_key = api_key
        self.zone = zone
        self.encryption_key = encryption_key

        # DNS API
        self.api_endpoint = f"https://{netor_ip}/pdns_api/api/v1"
        self.api_client = powerdns.PDNSApiClient(
            api_endpoint=self.api_endpoint, api_key=self.api_key)
        self.api = powerdns.PDNSEndpoint(self.api_client)
        # DNS Resolver
        self.resolver = dns.resolver.Resolver()
        self.resolver.nameservers = [dns_ip]
        self.resolver.nameserver_ports = {
            dns_ip: int(dns_port)
        }
        self.resolver.timeout = 15
        self.ptr_record_key = None
        self.my_own_key = None
        # DNS Encryption
        self.fernet = Fernet(self.encryption_key)
        self.wg_aux = WGAux(vars=_vars)

    def register_myself_in_dns(self, dns_service_type, dns_protocol, peer_id,
                               peer_internal_ip, peer_external_ip,
                               peer_internal_port, peer_external_port,
                               peer_public_key, peer_allowed_networks,
                               tunnel_peer_address):

        logger.info("Peer will register itlsef in the DNS")

        # 1. Get DNS Zone
        zone_obj = self.api.servers[0].get_zone(self.zone)

        # 2. Create Record Key for the A, SRV, and TXT Records
        self.my_own_key = srv_record_key = txt_record_key = f"_{peer_id}."\
            f"_{dns_service_type}._{dns_protocol}.{zone_obj.name}"

        a_record_key = f"{peer_id}.{zone_obj.name}"

        # 3 - Create TXT Record
        encrypted_private_ip = self.fernet.encrypt(
            peer_internal_ip.encode()
            ).decode()
        encrypted_private_port = self.fernet.encrypt(
            peer_internal_port.encode()
            ).decode()
        encrypted_public_key = self.fernet.encrypt(
            peer_public_key.encode()
            ).decode()
        encrypted_networks_to_allow = self.fernet.encrypt(
            peer_allowed_networks.encode()
            ).decode()

        peer_networks = self.wg_aux.get_all_interface_ips()
        encrypted_peer_networks = self.fernet.encrypt(
            peer_networks.encode()
        ).decode()
        # useful for active monitoring, allowing peers to know the endpoint to test
        encrypted_tunnel_address = self.fernet.encrypt(
            tunnel_peer_address.encode()
        ).decode()

        TXT_record = f"\"peer_public_key={encrypted_public_key};"\
            f"allowed_networks={encrypted_networks_to_allow};"\
            f"peer_local_port={encrypted_private_port};"\
            f"peer_local_ip={encrypted_private_ip};"\
            f"peer_networks={encrypted_peer_networks};"\
            f"peer_tunnel_address={encrypted_tunnel_address}\""


        logger.info(f"Peer's TXT Record: {TXT_record}")

        # 4 - Create and Update PTR Records
        # You have to consider the already existing PTR Records under the same
        # key. We want to preserve them

        self.ptr_record_key = f"_{dns_service_type}._{dns_protocol}"\
            f".{zone_obj.name}"
        logger.info(f"Peer's PTR Record Value: {self.ptr_record_key}")
        sleep_time = random.randint(0, 5)
        time.sleep(sleep_time)
        all_ptr_records = self._get_all_ptr_records(
            record=self.ptr_record_key)
        logger.info(f"All ptr Records: {all_ptr_records}")
        new_ptr_records = [
            (x, False)
            for x
            in all_ptr_records
        ]
        new_ptr_records.append((srv_record_key, False))

        # 5 - Update all Peer's DNS Records
        new_records = [
            powerdns.RRSet(
                name=self.ptr_record_key,
                rtype="PTR",
                records=new_ptr_records
            ),
            powerdns.RRSet(
                a_record_key,
                'A',
                [(peer_external_ip, False)]
            ),
            powerdns.RRSet(
                txt_record_key,
                'TXT',
                [(TXT_record, False)]
            ),
            powerdns.RRSet(
                name=srv_record_key,
                rtype='SRV',
                changetype="REPLACE",
                records=[(f"0 0 {peer_external_port} {a_record_key}")]
            ),
        ]

        zone_obj.create_records(new_records)

        logger.info("Peer registered itself in DNS Server")
        logger.info(f"New records:\n {new_records}")
        logger.info(f"Writing allowed networks {peer_allowed_networks}")
        parsed_allowed_network = [ip.strip()
            for ip in peer_allowed_networks.split(",")]
        self.wg_aux.write_allowed_networks_to_file(
            parsed_allowed_network
        )
        logger.info("Wrote allowed network to file")

    def get_other_peers_info(self, total_num_peers, max_waiting_time_secs):

        logger.info("Peer is gathering information about the other " +
                     f"{total_num_peers-1} peers...")

        wg_peer_keys = [None]
        SLEEP_TIME = 20
        total_waiting_time = 0
        while len(wg_peer_keys) < total_num_peers:
            # Update the peers list
            wg_peer_keys = self._get_all_ptr_records(self.ptr_record_key)

            logger.info(f"Peers already found: {len(wg_peer_keys)-1}")

            # If max waiting time is exceeded, return None
            if total_waiting_time > max_waiting_time_secs:
                return

            # Sleep a bit before the other peers are registered
            total_waiting_time += SLEEP_TIME
            logger.info(f"I will wait {SLEEP_TIME} seconds before trying"
                         + "to get information on the peers!")
            time.sleep(SLEEP_TIME)

        logger.info(f"Found all {total_num_peers-1} peers!")

        # Delete my own key
        wg_peer_keys.remove(self.my_own_key)

        # Get information regarding the other peers
        peers = []
        for wg_peer_key in wg_peer_keys:
            # ignore my own information
            if wg_peer_key != self.my_own_key:
                wg_peer_record = Wg_Peer_Info(
                    domain=wg_peer_key
                )
                self._update_peer_according_srv_records(wg_peer_record)
                self._update_peer_according_a_records(wg_peer_record)
                self._update_peer_according_txt_records(
                    wg_peer_record,
                    only_public_info=False
                )
                peers.append(wg_peer_record)
        logger.info(f"Peers List -> {peers}")
        return peers

    def _get_all_ptr_records(self, record):
        try:
            return [
                str(r.target)
                for r
                in self.resolver.resolve(record, 'PTR', tcp=True)
            ]
        except Exception as e:
            logger.info(f"Exception: {e}")
            return []

    def _update_peer_according_srv_records(self, wg_peer):
        records = self.resolver.resolve(wg_peer.domain, 'SRV', tcp=True)
        for r in records:
            wg_peer.dns_srv_address = r.target.to_text()
            wg_peer.public_port = r.port

    def _update_peer_according_a_records(self, wg_peer):
        records = self.resolver.resolve(wg_peer.dns_srv_address, 'A', tcp=True)
        for r in records:
            wg_peer.public_ip = r.address

    def _update_peer_according_txt_records(self, wg_peer,
                                           only_public_info=False):
        records = self.resolver.resolve(wg_peer.domain, 'TXT', tcp=True)
        for r in records:
            txt_record_data = b''.join(r.strings).decode()
            data = self._parse_txt_record(txt_record_data)
            if not only_public_info:
                wg_peer.private_ip = data["peer_local_ip"]
                wg_peer.private_port = data["peer_local_port"]
                wg_peer.tunnel_peer_address = data['peer_tunnel_address']
            wg_peer.public_key = data["peer_public_key"]
            wg_peer.allowed_networks = data["allowed_networks"]
            wg_peer.peer_networks = data['peer_networks']

    def _parse_txt_record(self, txt_record):
        dic = {}
        for tup in txt_record.split(';'):
            key, value = tup.split('=', 1)
            decrypted_value = self._decrypt_value(value.encode())
            dic[key] = decrypted_value
        return dic

    def _decrypt_value(self, value):
        decrypted_value = self.fernet.decrypt(value).decode()
        return decrypted_value

    def parse_other_peers_infos(self, peers_info, peer_ts_publisher):
        peers_tunnel_addresses = {}
        # Store all peer networks to later on filter by the allowed networks
        peers_networks = {}
        for peer_info in peers_info:
            logger.warning(f"-> {peer_info.__dict__}")
            logger.info(f"Adding Peer {peer_info.__dict__['domain']}...")
            peers_tunnel_addresses[
                peer_info.__dict__["public_key"]] = peer_info.__dict__[
                'tunnel_peer_address']
            peers_networks[
                peer_info.__dict__["public_key"]] = peer_info.__dict__[
                'peer_networks']
            self.wg_aux.add_peer(
                peer_endpoint=peer_info.__dict__['public_ip'] +
                f":{peer_info.__dict__['public_port']}",
                peer_key=peer_info.__dict__["public_key"],
                allowed_networks=peer_info.__dict__["allowed_networks"]
            )
        self.wg_aux.write_tunnel_peer_address_to_file(peers_tunnel_addresses)
        self.wg_aux.write_all_peer_networks_to_file(peers_networks)
        peer_ts_publisher.publish_data(
            domain=domain,
            action=TS_Constants.CONNECTION_SUCCESS_TS,
        )
        # if ret:
        #     logger.info(f"Peer {peer_info.__dict__['domain']} Added!")


if __name__ == "__main__":
    peer_ts_publisher = WG_TS_Publishing(
            netor_ip=netor_ip,
            vsi_id=vsi_id,
    )
    peer_dns_sd = Wg_DNS_SD(
            netor_ip=netor_ip,
            dns_ip=dns_ip,
            dns_port=dns_port,
            api_port=api_port,
            api_key=api_key,
            zone=zone,
            encryption_key=encryption_key)
    peer_ts_publisher.publish_data(
            domain=domain,
            action=TS_Constants.DNS_SD_REGISTER_TS,
    )
    peer_dns_sd.register_myself_in_dns(
                dns_service_type=dns_service_type,
                dns_protocol=dns_protocol,
                peer_id=tunnel_id,
                peer_external_ip=tunnel_public_address,
                peer_internal_ip=str(address),
                peer_internal_port=str(listen_port),
                peer_external_port=tunnel_public_port,
                peer_public_key=str(public_key),
                peer_allowed_networks=tunnel_allowed_networks,
                tunnel_peer_address=tunnel_peer_address
            )

    logger.info(f"Peer '{tunnel_id}' is now " +
                 "registered in the DNS Server")
    peer_ts_publisher.publish_data(
            domain=domain,
            action=TS_Constants.WAITING_DNS_INFO_TS,
    )
    # Find the Other Peers
    logger.info(f"Peer '{tunnel_id}' will now " +
                 "try to find the other peers")
    
    peers_info = peer_dns_sd.get_other_peers_info(
        total_num_peers=total_num_peers,
        max_waiting_time_secs=max_waiting_time
    )

    logger.info("[x] Other Peers Info [x]")

    if not peers_info:
        logger.error("It was impossible to gather the peers' info!")
        exit()
    elif len(peers_info) < total_num_peers - 1:
        logger.warning("[!] It was only possible to gather some peers' info!")
    peer_ts_publisher.publish_data(
            domain=domain,
            action=TS_Constants.GOT_DNS_INFO_TS,
    )
    peer_dns_sd.parse_other_peers_infos(peers_info, peer_ts_publisher)
