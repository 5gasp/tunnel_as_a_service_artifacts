# -*- coding: utf-8 -*-
# @Author: Daniel Gomes
# @Date:   2022-10-10 18:39:28
# @Last Modified by:   Daniel Gomes
# @Last Modified time: 2022-10-10 18:42:44

import configparser


class Constants:

    def __init__(self):

        config = configparser.RawConfigParser()
        config.read('netor.cfg')

        self.VSI_ID = config.get('NETOR', 'VSI_ID')
        self.DNS_IP = config.get('NETOR', 'DNS_IP')
        self.DNS_PORT = config.get('NETOR', 'DNS_PORT')
        self.DNS_API_PORT = config.get('NETOR', 'DNS_API_PORT')
        self.DNS_API_KEY = config.get('NETOR', 'DNS_API_KEY')
        self.DNS_ENCRYPTION_KEY = config.get('NETOR', 'DNS_ENCRYPTION_KEY')

        self.PEERS_INFO = {
            "peer_1": {
                "netslice-subnet": [
                    {
                        "id": "interdomain-tunnel-peer",
                        "additionalParamsForVnf": [
                            {
                                "member-vnf-index": "1",
                                "additionalParams": {
                                    "use_data_interfaces": "true",
                                    "tunnel_id": "wg1",
                                    "tunnel_peer_address": "10.100.100.1",
                                    "tunnel_address": "10.100.100.0/24",
                                    "ssh_username": "xxx",
                                    "ssh_password": "xxx",
                                    "vsi_id": self.VSI_ID,
                                    # New SD Params -> Added by NetOr
                                    "dns_ip": self.DNS_IP,
                                    "dns_port": self.DNS_PORT,
                                    "dns_api_port": self.DNS_API_PORT,
                                    "dns_api_key": self.DNS_API_KEY,
                                    "dns_encryption_key": self.DNS_ENCRYPTION_KEY,
                                    "dns_zone": f"vsi-{self.VSI_ID}.netor.",
                                    # New SD Params -> Added in the initial
                                    # config
                                    "dns_total_num_peers": "3",
                                    "dns_service_type": "wireguard",
                                    "dns_protocol": "udp",
                                    "tunnel_public_address": "193.167.1.2",
                                    "tunnel_public_port": "9000",
                                    "tunnel_allowed_networks": "10.100.100.0/24," +
                                    "10.100.101.0/24",
                                    "max_waiting_time_for_other_peers_secs": "120"
                                }
                            }
                        ]
                    }
                ]
            },
            "peer_2": {
                "netslice-subnet": [
                    {
                        "id": "interdomain-tunnel-peer",
                        "additionalParamsForVnf": [
                            {
                                "member-vnf-index": "1",
                                "additionalParams": {
                                    "use_data_interfaces": "true",
                                    "tunnel_id": "wg2",
                                    "tunnel_peer_address": "10.100.100.2",
                                    "tunnel_address": "10.100.100.0/24",
                                    "ssh_username": "xxx",
                                    "ssh_password": "xxx",
                                    "vsi_id": self.VSI_ID,
                                    # New SD Params -> Added by NetOr
                                    "dns_ip": self.DNS_IP,
                                    "dns_port": self.DNS_PORT,
                                    "dns_api_port": self.DNS_API_PORT,
                                    "dns_api_key": self.DNS_API_KEY,
                                    "dns_encryption_key": self.DNS_ENCRYPTION_KEY,
                                    "dns_zone": f"vsi-{self.VSI_ID}.netor.",
                                    # New SD Params -> Added in the initial
                                    # config
                                    "dns_total_num_peers": "3",
                                    "dns_service_type": "wireguard",
                                    "dns_protocol": "udp",
                                    "tunnel_public_address": "193.167.1.2",
                                    "tunnel_public_port": "9003",
                                    "tunnel_allowed_networks": "10.100.100.0/24," +
                                    "10.100.101.0/24",
                                    "max_waiting_time_for_other_peers_secs": "120"
                                }
                            }
                        ]
                    }
                ]
            },
            "peer_3": {
                "netslice-subnet": [
                    {
                        "id": "interdomain-tunnel-peer",
                        "additionalParamsForVnf": [
                            {
                                "member-vnf-index": "1",
                                "additionalParams": {
                                    "use_data_interfaces": "true",
                                    "tunnel_id": "wg3",
                                    "tunnel_peer_address": "10.100.100.2",
                                    "tunnel_address": "10.100.100.0/24",
                                    "ssh_username": "xxx",
                                    "ssh_password": "xxx",
                                    "vsi_id": self.VSI_ID,
                                    # New SD Params -> Added by NetOr
                                    "dns_ip": self.DNS_IP,
                                    "dns_port": self.DNS_PORT,
                                    "dns_api_port": self.DNS_API_PORT,
                                    "dns_api_key": self.DNS_API_KEY,
                                    "dns_encryption_key": self.DNS_ENCRYPTION_KEY,
                                    "dns_zone": f"vsi-{self.VSI_ID}.netor.",
                                    # New SD Params -> Added in the initial
                                    # config
                                    "dns_total_num_peers": "3",
                                    "dns_service_type": "wireguard",
                                    "dns_protocol": "udp",
                                    "tunnel_public_address": "193.167.1.2",
                                    "tunnel_public_port": "12345",
                                    "tunnel_allowed_networks": "10.100.100.0/24," +
                                    "10.100.101.0/24",
                                    "max_waiting_time_for_other_peers_secs": "120"
                                }
                            }
                        ]
                    }
                ]
            },
        }
