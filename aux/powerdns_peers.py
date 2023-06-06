# -*- coding: utf-8 -*-
# @Author: Rafael Direito
# @Date:   2022-08-16 19:04:59
# @Last Modified by:   Rafael Direito
# @Last Modified time: 2022-10-10 19:20:15

import powerdns
from cryptography.fernet import Fernet
import dns.resolver
import dns.rdataclass
import time


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


class Wg_DNS_SD:

    def __init__(self, dns_ip, dns_port, api_port, api_key, zone,
                 encryption_key):
        self.dns_ip = dns_ip
        self.dns_port = dns_port
        self.api_port = api_port
        self.api_key = api_key
        self.zone = zone
        self.encryption_key = encryption_key
        # DNS API
        self.api_endpoint = f"http://{dns_ip}:{api_port}/api/v1"
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

    def register_myself_in_dns(self, dns_service_type, dns_protocol, peer_id,
                               peer_internal_ip, peer_external_ip,
                               peer_internal_port, peer_external_port,
                               peer_public_key, peer_allowed_networks):

        print("Peer will register itlsef in the DNS")

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

        TXT_record = f"\"peer_public_key={encrypted_public_key};"\
            f"allowed_networks={encrypted_networks_to_allow};"\
            f"peer_local_port={encrypted_private_port};"\
            f"peer_local_ip={encrypted_private_ip}\""

        print(f"Peer's TXT Record: {TXT_record}")

        # 4 - Create and Update PTR Records
        # You have to consider the already existing PTR Records under the same
        # key. We want to preserve them

        self.ptr_record_key = f"_{dns_service_type}._{dns_protocol}"\
            f".{zone_obj.name}"
        print(f"Peer's PTR Record Value: {self.ptr_record_key}")

        new_ptr_records = [
            (x, False)
            for x
            in self._get_all_ptr_records(record=self.ptr_record_key)
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

        print("Peer registered itself in DNS Server")
        print(f"New records:\n {new_records}")

    def get_other_peers_info(self, total_num_peers, max_waiting_time_secs):

        print("Peer is gathering information about the other " +
              f"{total_num_peers-1} peers...")

        wg_peer_keys = [None]
        SLEEP_TIME = 20
        total_waiting_time = 0
        while len(wg_peer_keys) < total_num_peers:
            # Update the peers list
            wg_peer_keys = self._get_all_ptr_records(self.ptr_record_key)

            print(f"Peers already found: {len(wg_peer_keys)-1}")

            # If max waiting time is exceeded, return None
            if total_waiting_time > max_waiting_time_secs:
                return

            # Sleep a bit before the other peers are registered
            total_waiting_time += SLEEP_TIME
            print(f"I will wait {SLEEP_TIME} seconds before trying to get " +
                  "information on the peers!")
            time.sleep(SLEEP_TIME)

        print(f"Found all {total_num_peers-1} peers!")

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
        return peers

    def _get_all_ptr_records(self, record):
        try:
            return [
                str(r.target)
                for r
                in self.resolver.resolve(record, 'PTR')
            ]
        except Exception as e:
            print(f"Exception: {e}")
            return []

    def _update_peer_according_srv_records(self, wg_peer):
        records = self.resolver.resolve(wg_peer.domain, 'SRV')
        for r in records:
            wg_peer.dns_srv_address = r.target.to_text()
            wg_peer.public_port = r.port

    def _update_peer_according_a_records(self, wg_peer):
        records = self.resolver.resolve(wg_peer.dns_srv_address, 'A')
        for r in records:
            wg_peer.public_ip = r.address

    def _update_peer_according_txt_records(self, wg_peer,
                                           only_public_info=False):
        records = self.resolver.resolve(wg_peer.domain, 'TXT')
        for r in records:
            txt_record_data = b''.join(r.strings).decode()
            data = self._parse_txt_record(txt_record_data)
            if not only_public_info:
                wg_peer.private_ip = data["peer_local_ip"]
                wg_peer.private_port = data["peer_local_port"]
            wg_peer.public_key = data["peer_public_key"]
            wg_peer.allowed_networks = data["allowed_networks"]

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
