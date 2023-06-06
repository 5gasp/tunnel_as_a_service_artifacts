import wgconfig
import subprocess
import pingparsing
from os import environ
from threading import Thread
import json
PING_TIMEOUT = 5
import socket
import ipaddress
from time import sleep
class PingWrapperThread(Thread):
    def __init__(self, target, parser, transmitter, link):
        super().__init__()
        self.target = target
        self.parser = parser
        self.transmitter = transmitter
        self.link = link
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_addr = ('localhost', 12345)
    
    def send_message(self, payload):
        encoded_payload = payload.encode('utf-8')
        msgsize=str(len(encoded_payload))
        msgsize="{:>5}".format(msgsize)
        msgsize=msgsize.encode('utf-8')
        #Before sending the message itself,send first the size of it with
        self.client_sock.send(msgsize)
        #now we can send the message
        self.client_sock.send(encoded_payload)
    
    def run(self):
       
        self.transmitter.destination = self.target
        self.transmitter.count = PING_TIMEOUT
        res = self.transmitter.ping()
        self.client_sock.connect(self.server_addr)
        res = self.parser.parse(res).as_dict()
        payload = {'link': self.link, 'output': res}
        payload = json.dumps(payload)
        self.send_message(payload)
        self.client_sock.close()

class WGActiveMonitoringDaemon:
    def __init__(self, interface) -> None:
        self.wg = wgconfig.WGConfig(f'/etc/wireguard/{interface}.conf')
        self.peers = {}
        self.interface = interface
        self.peers_addresses_path = "/home/ubuntu/aux_files/peers_addresses.txt"
        self.peer_networks_path = "/home/ubuntu/aux_files/all_peer_networks.txt"
        self.vnf_ip = self.set_vnf_ip()
        #self.vm_local_ip = self.set_vm_local_ip()
    def parse_tunnel_peer_addresses(self):
        with open(self.peers_addresses_path, 'r') as f:
            for line in f:
                _line = line.strip()
                print(_line.split(":"))
                pub_key, tunnel_peer_address = _line.split(":")
                self.peers[pub_key]['tunnel_peer_address'] = tunnel_peer_address
                print(self.peers[pub_key]['tunnel_peer_address'])
    def parse_peer_networks(self):
        with open(self.peer_networks_path, 'r') as f:
            for line in f:
                _line = line.strip()
                print(_line.split(":"))
                pub_key, peer_networks = _line.split(":")
                self.peers[pub_key]['peer_networks'] = peer_networks.split(",")
                self.peers[pub_key]['target'] = self.get_ping_target(
                    self.peers[pub_key]['peer_networks'],
                    self.peers[pub_key]['AllowedIPs'],
                    self.peers[pub_key]['tunnel_peer_address']
                    )
    def set_vnf_ip(self):
        _vnf_ip = environ.get('VNF_IP', None)
        if not _vnf_ip:
            res = subprocess.run(f'ip addr show {self.interface} | grep inet | head -n1 | xargs ',
                                 shell=True,
                                 capture_output=True)
            res = res.stdout.strip().decode()
            print(res)
            _vnf_ip = res.split(' ')[1].split('/')[0]
            environ['VNF_IP'] = _vnf_ip
        return _vnf_ip

    def get_ping_target(self, all_networks, ips, tunnel_peer_address):
        
        for ip in ips:
            if ip == tunnel_peer_address:
                continue
            for network in all_networks:
                print("---")
                print(network, ip)
                print("----")
                if ipaddress.ip_address(network) in ipaddress.ip_network(ip):
                    return network
   
    def parse_config(self):
        self.wg.read_file()
        self.peers = self.wg.peers
    
    def ping_test(self):
        threads = []
        ping_parser = pingparsing.PingParsing()
        transmiter = pingparsing.PingTransmitter()
        for peer in self.peers:
            target = self.peers[peer]['tunnel_peer_address']
            ping_target = self.peers[peer]['target']
            link_name = f"{self.vnf_ip}_{target}"
            print(f"link {link_name}")
            print(f"ping target {ping_target}")
            thread = PingWrapperThread(
                target=ping_target,
                parser=ping_parser,
                transmitter=transmiter,
                link=link_name)
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
def main():
    while True:
        print("Starting new active monitoring test...")
        try:
            wg_daemon = WGActiveMonitoringDaemon('wg0')
            wg_daemon.parse_config()
            wg_daemon.parse_tunnel_peer_addresses()
            wg_daemon.parse_peer_networks()
            wg_daemon.ping_test()
        except Exception as e:
            print(f"Error occured: {e}")
        sleep(PING_TIMEOUT)
if __name__ == "__main__":
    main()