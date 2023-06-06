# -*- coding: utf-8 -*-
# @Author: Rafael Direito
# @Date:   2022-10-10 18:43:05
# @Last Modified by:   Rafael Direito
# @Last Modified time: 2022-10-10 19:05:58

from powerdns_peers import Wg_DNS_SD
import argparse
from aux import Constants
from random import randrange
import time


class Peer:

    def __init__(self, peer_id, peers_info):
        peer_params = peers_info[peer_id]["netslice-subnet"][0]
        peer_params = peer_params["additionalParamsForVnf"][0]
        peer_params = peer_params["additionalParams"]

        # These variables will be provided in the Charm
        self.dns_ip = peer_params["dns_ip"]
        self.dns_port = peer_params["dns_port"]
        self.api_port = peer_params["dns_api_port"]
        self.api_key = peer_params["dns_api_key"]
        self.dns_encryption_key = peer_params["dns_encryption_key"]
        self.dns_zone = peer_params["dns_zone"]
        self.total_num_peers = int(peer_params["dns_total_num_peers"])
        self.service_type = peer_params["dns_service_type"]
        self.protocol = peer_params["dns_protocol"]
        self.zone = peer_params["dns_zone"]
        self.peer_id = peer_params["tunnel_id"]
        self.peer_internal_ip = peer_params["tunnel_peer_address"]
        self.peer_external_ip = peer_params["tunnel_public_address"]
        self.peer_internal_port = "51820"
        self.peer_external_port = peer_params["tunnel_public_port"]
        self.peer_public_key = "aosfoajkansjfna"  # Generated in run-time
        self.peer_allowed_networks = peer_params["tunnel_allowed_networks"]
        self.max_waiting_time = int(peer_params["max_waiting_time_for_other_peers_secs"])

        self.peer_dns_sd = Wg_DNS_SD(
            dns_ip=self.dns_ip,
            dns_port=self.dns_port,
            api_port=self.api_port,
            api_key=self.api_key,
            zone=self.dns_zone,
            encryption_key=self.dns_encryption_key
        )

    def register_peer_in_dns(self):
        self.peer_dns_sd.register_myself_in_dns(
            dns_service_type=self.service_type,
            dns_protocol=self.protocol,
            peer_id=self.peer_id,
            peer_external_ip=self.peer_external_ip,
            peer_internal_ip=self.peer_internal_ip,
            peer_internal_port=self.peer_internal_port,
            peer_external_port=self.peer_external_port,
            peer_public_key=self.peer_public_key,
            peer_allowed_networks=self.peer_allowed_networks

        )

    def get_other_peers_info(self):
        peers_info = self.peer_dns_sd.get_other_peers_info(
            total_num_peers=self.total_num_peers,
            max_waiting_time_secs=self.max_waiting_time
        )

        print("[x] Other Peers Info [x]")
        if not peers_info:
            print("It was impossible to gather the peers' info!")
            return
        elif len(peers_info) < self.total_num_peers - 1:
            print("[!] It was only impossible to gather some peers' info! [!]")

        for peer_info in peers_info:
            print(f"-> {peer_info.__dict__}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser("dummy_peer.py")
    parser.add_argument("--peer_id", help="Peer's ID", type=str)
    args = parser.parse_args()

    Constants = Constants()

    # Add sleep time, to mimic realtime behaviour
    sleep = randrange(30)
    print(f"{args.peer_id} will sleep {sleep} seconds, before registering " +
          "in DNS.")
    time.sleep(sleep)

    # Configure Peer
    peer = Peer(args.peer_id, Constants.PEERS_INFO)
    peer.register_peer_in_dns()
    peer.get_other_peers_info()
