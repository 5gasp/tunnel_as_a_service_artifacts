from base_node import BaseNode
from threading import Timer
from utils import publish_data
from utils import PREPARE_STATUS, READY_STATUS, ABORT_STATUS, TIMEOUT_SECONDS


class Coordinator(BaseNode):
    def __init__(self, peer_ts_publisher, domain) -> None:
        super().__init__(
            peer_ts_publisher=peer_ts_publisher,
            domain=domain)
        self.timer = None

    def is_consensus_reached(self):
        # check if all peers have already decided
        # whether they can or not apply the new route
        print([self.peers[x]["status"] != PREPARE_STATUS for x in self.peers])
        return all([self.peers[x]["status"] != PREPARE_STATUS for x in self.peers])

    def has_coordinator_failed(self, consider_timeout=False):
        if consider_timeout:
            return (
                self.my_peer["status"] == ABORT_STATUS
                or self.my_peer["status"] == PREPARE_STATUS
            )
        else:
            return self.my_peer["status"] == ABORT_STATUS

    def reach_completion(self, data):
        status = data["decision"]
        print(f"Reach completion, decision received from {data['peer']} : {status} ")
        response = {}
        self.peers[data["peer"]]["status"] = READY_STATUS
        if status == ABORT_STATUS or self.has_coordinator_failed():
            response["completion"] = ABORT_STATUS
        elif self.is_consensus_reached():
            response["completion"] = READY_STATUS
        return response

    def consensus_timeout_callback(self):
        response = {}
        has_failed = True
        print("Callback called")
        if not self.is_consensus_reached():
            # if the remaining nodes haven't sent their decision
            # the consensus should fail
            response["completion"] = ABORT_STATUS
        elif self.has_coordinator_failed(consider_timeout=True):
            # if the coordinator has failed the consensus should fail too
            response["completion"] = ABORT_STATUS
        else:
            # Probably this condition won't ever happen
            # the coordinator hasn't failed thus, a consensus should be reached
            has_failed = True
            response["completion"] = READY_STATUS
        print(f"Completion State Decided: {response['completion']}")
        self.completion_to_all_nodes(data=response)
        # The coordinator has to reset its routes too
        if has_failed:
            self.rollback_route()

    def set_consensus_timeout(self, callback, timeout=TIMEOUT_SECONDS):
        print("Timer Set..")
        self.timer = Timer(timeout, callback)
        self.timer.start()

    def send_prepare_message(self, target, data):
        target_url = f"http://{target}:8080/prepare"
        publish_data(target_url, data)

    def send_completion_message(self, target, data):
        target_url = f"http://{target}:8080/completion"
        publish_data(target_url, data)

    def prepare_all_nodes(self, interface, data):
        print("Coordinator Node preparing...")
        self.my_peer["status"] = PREPARE_STATUS
         # and perform the preparation task
        route_data = data[self.my_ip]
        self.prepare_task(
            coordinator_ip=None,
            route_data=route_data,
            ping_interface="x.x.x.x",
            ping_target="y.y.y.y",
        )
        self.set_consensus_timeout(self.consensus_timeout_callback)
        # set task on background to verify the consensus status
        # after some time
        for peer in self.peers:
            target = self.peers[peer]["tunnel_peer_address"]
            # The peers will now be in the prepare statuss
            self.peers[peer]["status"] = PREPARE_STATUS
            payload = {
                    "route": {},
                    "coordinator_ip": self.my_ip,
             }
            if target in data:
                payload['route'] = data[target]
            
            print(f"Sending prepare message to peer {target}")
            self.send_prepare_message(target=target, data=payload)
        # # The coordinator Peer will be in the prepare status too

        #

    def completion_to_all_nodes(self, data):
        for peer in self.peers:
            target = self.peers[peer]["tunnel_peer_address"]
            print(f"Sending completion message to peer {target}")
            self.send_completion_message(target=target, data=data)
        self.timer.cancel()
