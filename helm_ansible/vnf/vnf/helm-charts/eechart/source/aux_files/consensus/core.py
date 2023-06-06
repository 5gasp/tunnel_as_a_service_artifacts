import cherrypy
from base_node import BaseNode
from coordinator import Coordinator
from utils import ABORT_STATUS
import json
from publish_ts import WG_TS_Publishing
import constants as TS_Constants
import os
import logging
# TODO:
#     my_peer: public key should be retrieved from the Wg Dir (Done)
#     Check Ping src and Target!
#     Remove routes (Sort of done)
#     Timeout to wait for replies of the nodes (Done)


class MyServer(object):
    def __init__(self, netor_ip, vsi_id, domain) -> None:
        
        self.is_consensus_pending = False
        self.vsi_id = vsi_id
        self.domain = domain
        self.peer_ts_publisher = WG_TS_Publishing(
            netor_ip=netor_ip,
            vsi_id=vsi_id,
        )
        self.node = BaseNode(
            peer_ts_publisher=self.peer_ts_publisher,
            domain=domain)

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
        #data = cherrypy.request.json
        #print("data", data)
        request_body = cherrypy.request.body.read()
        print(f"request_body {request_body}")
        request_body = str(request_body).replace("\n","")
        request_body = request_body[2:-1]
        print(request_body)
        data = json.loads(request_body)
        interface = data["interface"]
        self.node = Coordinator(peer_ts_publisher=self.peer_ts_publisher,
                                domain=self.domain)
        self.node.parse_wireguard_conf(interface)
        self.is_consensus_pending = True
        self.node.prepare_all_nodes(interface, data["routes"])
        
        self.peer_ts_publisher.publish_data(
            domain=self.domain,
            action=TS_Constants.WAITING_DNS_INFO_TS,
        )
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
            res = self.node.completion_to_all_nodes(payload)
            self.peer_ts_publisher.publish_data(
                domain=self.domain,
                action=TS_Constants.COMPLETION_CONSENSUS_TS,
            )
            if not res:
                return "NO DECISION YET"
            # coordinator node needs to confirm/rollback also the new route
            if payload["completion"] == ABORT_STATUS:
                print(f"Rollbacking... {payload['completion']}")
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
        print(f"Completion Data {data['completion']}")
        if data["completion"] == ABORT_STATUS:
            print("Received Instruction to rollback the new route")
            self.node.rollback_route()
        else:
            print("Received Instruction to confirm the new route")
            self.node.confirm_route()
        self.peer_ts_publisher.publish_data(
                domain=self.domain,
                action=TS_Constants.COMPLETION_CONSENSUS_TS,
        )
        return "OK"


if __name__ == "__main__":
    cherrypy.server.socket_host = "0.0.0.0"
    netor_ip = str(os.environ.get('NETOR_IP'))
    vsi_id = str(os.environ.get('VSI_ID'))
    domain = str(os.environ.get('DOMAIN'))
    logger = logging.getLogger(__name__)
    logging.info(f"-- {netor_ip}, {vsi_id}, {domain}")
    cherrypy.quickstart(MyServer(
        netor_ip=netor_ip,
        vsi_id=vsi_id,
        domain=domain))




