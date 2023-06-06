# @Author: Daniel Gomes
# @Date:   2023-02-14 14:05:53
# @Email:  dagomes@av.it.pt
# @Copyright: Insituto de Telecomunicações - Aveiro, Aveiro, Portugal
# @Last Modified by:   Daniel Gomes
# @Last Modified time: 2023-02-15 14:42:46
import wgconfig
import logging
import subprocess
import os
import sys
import netifaces
import ipaddress

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)

logger.addHandler(handler)


class WGAux:
    def __init__(self, vars) -> None:
        self.vars = vars

    def get_wg_config_to_local(self, forward_interface):
        config_dir = self.vars['WgConfigDestinationDir']
        source_file_vnf = f"{config_dir}/{forward_interface}.conf"
        destination_file_vnf = self.vars['WgConfigLocalDir']
        subprocess.run(['cp', source_file_vnf, destination_file_vnf])

    def update_wg_config_on_vnf(self, forward_interface):
        config_dir = self.vars['WgConfigDestinationDir']
        source_file_vnf = f"{self.vars['WgConfigLocalDir']}/{forward_interface}.conf"
        destination_file_vnf = config_dir
        subprocess.run(['cp', source_file_vnf, destination_file_vnf])

    # write in a file the tunnel_peer_addresses to later on be used in active monitoring
    def write_tunnel_peer_address_to_file(self, content: dict):
        file_path = f"{self.vars['aux_dir']}/peers_addresses.txt"
        if not os.path.exists(self.vars['aux_dir']):
            if not os.path.exists(file_path):
                os.mkdir(file_path)
        with open(file_path, 'a') as f:
            for k in content:
                f.write(f"{k}:{content[k]}\n")
            
    def check_network_in_interface(self, peer_network, interface):
        try:
            addrs = netifaces.ifaddresses(interface)
            ip = addrs[netifaces.AF_INET][0]['addr']
            subnet = ipaddress.IPv4Network(peer_network)
            network = ipaddress.ip_network(ip)
            if subnet.overlaps(network):
                return True
            else:
                return False
        except KeyError:
            return False
    # write in the network used by the peer to forward the data traffic
    def write_allowed_networks_to_file(self, allowed_networks):
        file_path = f"{self.vars['aux_dir']}/my_address.txt"
        if not os.path.exists(self.vars['aux_dir']):
            if not os.path.exists(file_path):
                os.mkdir(file_path)
        with open(file_path, 'a') as f:
            for net in allowed_networks:
                if not self.check_network_in_interface(net, 'wg0'):
                    f.write(net)
                    break
    
    def write_all_peer_networks_to_file(self, content):
        file_path = f"{self.vars['aux_dir']}/all_peer_networks.txt"
        if not os.path.exists(self.vars['aux_dir']):
            if not os.path.exists(file_path):
                os.mkdir(file_path)
        with open(file_path, 'a') as f:
            for k in content:
                f.write(f"{k}:{content[k]}\n")
            
    def get_all_interface_ips(self):
        res = subprocess.run(
            "ip addr show | awk '$1 == \"inet\" {print $2}' | cut -d/ -f1 | tr '\\n' ',' | sed 's/,$//'",
            shell=True,
            capture_output=True)
        res = res.stdout.strip().decode()
        return res

    def add_peer(self, peer_endpoint=None, peer_key=None,
                 allowed_networks=None):

        forward_interface = self.vars["forward_interface"]

        # When an action is executed
        if not (peer_endpoint and peer_key and allowed_networks):
            # TODO: Check how to run actions..
            pass
            # peer_key = event.params["peer_public_key"]
            # peer_endpoint = event.params["peer_endpoint"]
            # allowed_networks = []
            # if allowed_networks:
            #     allowed_networks = [
            #         net.strip() 
            #         for net 
            #         in list(event.params["allowed_networks"].split(",")) 
            #         if len(net.strip()) != 0
            #    ]
        # DNS SD Peer Adding
        else:
            allowed_networks = allowed_networks.split(",")
            # 1. Stop Wireguard
            subprocess.run(['wg-quick', 'down', forward_interface])

            # 2. Add peer
            # 2.1. Get wg config to local file
            self.get_wg_config_to_local(forward_interface)

            # 2.2. Add peer to wg local config
            logger.info("Updating local wireguard configuration file")
            file_path = f"{self.vars['WgConfigLocalDir']}/{forward_interface}"\
                        + ".conf"
            m_wgconfig = wgconfig.WGConfig(file_path)
            m_wgconfig.read_file()
            logger.info(f"Existing Peers: {m_wgconfig.peers}")
            # if peer already exists, remove it
            wg_existing_peers = m_wgconfig.peers
            if peer_key in wg_existing_peers:
                m_wgconfig.del_peer(peer_key)

            m_wgconfig.add_peer(peer_key)
            m_wgconfig.add_attr(
                peer_key,
                'AllowedIPs',
                ", ".join(allowed_networks)
            )
            m_wgconfig.add_attr(
                peer_key,
                'Endpoint',
                peer_endpoint
            )
            m_wgconfig.add_attr(
                peer_key,
                'PersistentKeepalive',
                15
            )
            m_wgconfig.write_file()
            self.update_wg_config_on_vnf(forward_interface)
