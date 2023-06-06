import pingparsing


class PingWrapper:
    def __init__(self) -> None:
        self.parser = pingparsing.PingParsing()
        self.transmitter = pingparsing.PingTransmitter()
        self.timeout = 2

    def run_ping(self, interface, destination):
        self.transmitter.ping_option
        self.transmitter.destination = destination
        self.transmitter.count = self.timeout
        self.transmitter.interface = interface
        res = self.transmitter.ping()
        res = self.parser.parse(res).as_dict()
        return res

    def check_success_connection(self, res):
        pass
