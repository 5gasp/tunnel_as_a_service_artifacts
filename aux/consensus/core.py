import cherrypy
from base_node import BaseNode
from coordinator import Coordinator
from utils import ABORT_STATUS
import json
import logging
import sys


logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
handler.setFormatter(formatter)

logger.addHandler(handler)
# TODO:
#     my_peer: public key should be retrieved from the Wg Dir (Done)
#     Check Ping src and Target!
#     Remove routes (Sort of done)
#     Timeout to wait for replies of the nodes (Done)


class MyServer(object):
    def __init__(self) -> None:
        self.node = BaseNode()
        self.is_consensus_pending = False

    def reset(self):
        self.node = BaseNode()
        self.is_consensus_pending = False

    @cherrypy.expose
    def index(self):
        return "Hello world!"

    # Endpoint exposed to select the coordinator
    # - Sends a prepare message to the remaining nodes
    # - Since the coordinator it's a node itself, the coordinator
    #   needs to check if it can also apply the new route
    @cherrypy.expose
    def start_2pc(self):
        request_body = cherrypy.request.body.read()
        data = json.loads(request_body)
        interface = data["interface"]
        self.node = Coordinator()
        self.node.parse_wireguard_conf(interface)
        self.is_consensus_pending = True
        self.node.prepare_all_nodes(interface, data["routes"])
        return "2PC protocol started successfully"

    # The remaining nodes will expose the endpoint for the preparation phase
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def prepare(self):
        data = cherrypy.request.json
        data = json.loads(data)
        self.node.parse_wireguard_conf("wg0")
        print("DATA", data)
        coordinator_ip = data["coordinator_ip"]
        route_data = data["route"]
        self.node.prepare_task(
            coordinator_ip=coordinator_ip,
            route_data=route_data,
            ping_interface="x.x.x.x",
            ping_target="y.y.y.y",
        )
        return "OK"

    # Endpoint exposed by the coordinator to receive the decisions of the remaining nodes
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def decision(self):
        data = cherrypy.request.json
        data = json.loads(data)
        payload = self.node.reach_completion(data)
        if "completion" in payload:
            self.node.completion_to_all_nodes(payload)
            # coordinator node needs to confirm/rollback also the new route
            if payload["completion"] == ABORT_STATUS:
                self.node.rollback_route()
            else:
                self.node.confirm_route()
        return "OK"

    # Endpoint exposed by the remaining nodes to receive the completion messsage
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def completion(self):
        data = cherrypy.request.json
        data = json.loads(data)
        if data["completion"] == ABORT_STATUS:
            print("Received Instruction to rollback the new route")
            self.node.rollback_route()
        else:
            print("Received Instruction to confirm the new route")
            self.node.confirm_route()
        return "OK"


if __name__ == "__main__":
    cherrypy.server.socket_host = "0.0.0.0"
    cherrypy.quickstart(MyServer())
