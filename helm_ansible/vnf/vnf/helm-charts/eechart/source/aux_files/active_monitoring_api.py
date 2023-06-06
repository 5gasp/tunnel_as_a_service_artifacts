"""Active Monitoring exporter"""

import os
import selectors
import time
from prometheus_client import start_http_server, Gauge, Enum
import json
import socket
class AppMetrics:
    """
    Representation of Prometheus metrics and loop to fetch and transform
    network metrics into Prometheus metrics.
    """

    def __init__(self, polling_interval_seconds=5):
        self.polling_interval_seconds = polling_interval_seconds
        self.output_path = '/home/ubuntu/auxfiles'
        # Prometheus metrics to collect
        self.current_requests = Gauge('osm_my_metric', 'my metrics', ['link'])
        self.file_data = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _address = ('localhost', 12345)
        self.sock.bind(_address)
        self.sel = selectors.DefaultSelector()
    
    def handle_socket(self, sock, mask):
        try:
            conn, addr = self.sock.accept()
            print('accepted', conn, 'from', addr)
            # Receive data from the socket
            nBytes=conn.recv(5)
            if nBytes:
                nBytes=int(nBytes.decode('utf-8'))
                data=conn.recv(nBytes)
                if data:
                    data = data.decode('utf-8')
                    data = json.loads(data)
                    self.update_metric(data['link'], data['output'])
                    # Do something with the data, such as print it to the console
                    print('Received data: %s' % data)
            else:
                #self.sel.unregister(conn)
                conn.close()
        except Exception as e:
            pass
    def update_metric(self, link, value):
        self.current_requests.labels(link=link).set(
            value['rtt_avg'] 
        )

    def run_metrics_loop(self):
        self.sock.listen(100)
        self.sel.register(self.sock, selectors.EVENT_READ, self.handle_socket)
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask) 
       
def main():
    """Main entry point"""

    polling_interval_seconds = 2
    exporter_port = 9000

   
    start_http_server(exporter_port)
    app_metrics = AppMetrics(
        polling_interval_seconds=polling_interval_seconds
    )
    app_metrics.run_metrics_loop()

if __name__ == "__main__":
    main()
