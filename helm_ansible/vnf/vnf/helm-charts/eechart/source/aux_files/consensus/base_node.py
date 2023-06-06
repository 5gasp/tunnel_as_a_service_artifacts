import wgconfig
import subprocess
from routes_wrapper import RoutesWrapper
from queue import Queue
from utils import publish_data
import time
from threading import Thread
from utils import (
    WG_LOCATION,
    WG_LOCATION,
    READY_STATUS,
    ABORT_STATUS,
)
import constants as TS_Constants


class BaseNode:
    def __init__(self, peer_ts_publisher, domain) -> None:
        self.wg = None
        self.peers = {}
        self.peers_addresses_path = "/home/ubuntu/aux_files/peers_addresses.txt"
        self.routes_mgmt = RoutesWrapper()
        self.added_routes_queue = Queue()
        # The data of the current peer we're in
        self.my_peer = None
        self.my_ip = None
        self.peer_ts_publisher = peer_ts_publisher
        self.domain = domain

    def parse_wireguard_conf(self, interface):
        wg_conf_location = f"{WG_LOCATION}/{interface}.conf"
        self.wg = wgconfig.WGConfig(wg_conf_location)

        self.wg.read_file()
        self.peers = self.wg.peers
        self.my_peer = self.wg.interface
        self.my_ip = self.get_vnf_ip(interface)
        self.added_routes_queue = Queue()
        self.parse_tunnel_peer_addresses()
        self.get_my_peer_pubkey()

    def get_my_peer_pubkey(self, path=f"{WG_LOCATION}/publickey"):
        with open(path, "r") as f:
            public_key = f.read().strip()
            self.my_peer["PublicKey"] = public_key

    def parse_tunnel_peer_addresses(self):
        with open(self.peers_addresses_path, "r") as f:
            for line in f:
                _line = line.strip()
                pub_key, tunnel_peer_address = _line.split(":")
                self.peers[pub_key]["tunnel_peer_address"] = tunnel_peer_address

    def get_vnf_ip(self, interface):
        print(f"interface {interface}")
        res = subprocess.run(
            f"ip addr show {interface} | grep inet | head -n1 | xargs ",
            shell=True,
            capture_output=True,
        )
        res = res.stdout.strip().decode()
        print(f"--- {res}")
        _vnf_ip = res.split(" ")[1].split("/")[0]
        return _vnf_ip

    def confirm_route(self):
        if not self.added_routes_queue.empty():
            _route = self.added_routes_queue.queue[0]
            routes = self.routes_mgmt.get_dest_network_routes(
                rta_dst=_route["dest_network"], interface_name=_route["interface"]
            )
            srt_routes = self.routes_mgmt.sorte_routes(routes=routes, reverse=True)
            if len(srt_routes) > 1:
                route_to_delete = srt_routes[0]
                print(srt_routes)
                print("Deleting previous route")
                rta_dst = route_to_delete.get_attr("RTA_DST")
                mask = route_to_delete["dst_len"]
                dest_network = f"{rta_dst}/{mask}"
                gateway = route_to_delete.get_attr("RTA_GATEWAY")
                priority = route_to_delete.get_attr("RTA_PRIORITY")
                proto = route_to_delete["proto"]
                scope = route_to_delete["scope"]
                self.routes_mgmt.remove_route(
                    dest_network=dest_network,
                    gateway=gateway,
                    interface_name="wg0",
                    proto=proto,
                    scope=scope,
                    weight=priority
                )
                print("route deleted...")
        else:
            print("No Routes were added. Nothing else to update..")

    def rollback_route(self):
        # TODO: check if queue is the best data
        #      structure to apply
        if not self.added_routes_queue.empty():
            data = self.added_routes_queue.get(0)
            print(f"Route to rollback {data}")
            self.routes_mgmt.remove_route(
                dest_network=data["dest_network"],
                gateway=data["gateway"],
                interface_name=data["interface"],
            )

            print("Route Rollbacked")
        else:
            print("No Route to rollback...")

    def prepare_task(
        self, route_data, ping_interface, ping_target, coordinator_ip=None
    ):
        self.peer_ts_publisher.publish_data(
            domain=self.domain,
            action=TS_Constants.PREPARE_CONSENSUS_TS,
        )
        th = Thread(
            target=self.prepare,
            args=(route_data, ping_interface, ping_target, coordinator_ip),
        )
        th.start()

    def prepare(self, data, ping_interface, ping_target, coordinator_ip=None):
        response = {"peer": self.my_peer["PublicKey"], "decision": None, "route": data}
        try:
            if data:
                self.routes_mgmt.manage_new_route(
                    dest_network=data["dest_network"],
                    gateway=data["gateway"],
                    interface_name=data["interface"],
                )
                self.added_routes_queue.put(data)
                # wait until all routes are applied..
                time.sleep(1)
                # self.routes_mgmt.check_route(
                #    interface=ping_interface, target=ping_target
                # )
            response["decision"] = READY_STATUS
        except Exception as e:
            print(f"Exception: {e}")
            response["decision"] = ABORT_STATUS
        # if the coordinator_ip  has not been passed as argument
        # then the prepare task is being held by the coordinator
        # we should only need to store in a variable the result
        if coordinator_ip:
            print(f"Sending decision {response['decision']} to coordinator")
            self.send_decision_to_coordinator(coordinator_ip, response)
        else:
            print(f"Coordinator decision {response['decision']}")
            self.my_peer["status"] = response["decision"]
        self.peer_ts_publisher.publish_data(
            domain=self.domain,
            action=TS_Constants.DECISON_CONSENSUS_TS,
        )
        return True

    def send_decision_to_coordinator(self, target, data):
        target_url = f"http://{target}:8080/decision"
        publish_data(target_url, data)
