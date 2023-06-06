# @Author: Daniel Gomes
# @Date:   2022-11-12 10:29:52
# @Email:  dagomes@av.it.pt
# @Copyright: Insituto de Telecomunicações - Aveiro, Aveiro, Portugal
# @Last Modified by:   Daniel Gomes
# @Last Modified time: 2022-11-16 17:32:11
import requests
import logging
from datetime import datetime
# Logger
logger = logging.getLogger(__name__)


class WG_TS_Publishing:
    def __init__(self, netor_ip, vsi_id, tunnel_charm) -> None:
        self.ip = netor_ip
        self.vsi_id = vsi_id
        self.url = f"https://{self.ip}/tests/timestamp"
        self.tunnel_charm = tunnel_charm

    def publish_data(self, domain, action, event):
        if self.tunnel_charm.model.unit.is_leader():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            logger.info(f"Publishing timestamp for action {action} to {self.url}")
            _json = {
                "action": action,
                "timestamp": timestamp,
                "domain": domain
            }
            try:
                r = requests.post(
                    url=f"{self.url}/{self.vsi_id}",
                    json=_json
                )
                if r.status_code != 200:
                    msg = r.json()['message']
                    logging.error(f"Error publishing. Reason: {msg}")
                else:
                    _ = r.json()
                    logging.info(f"Success Publishing result for action {action}")
                return
            except Exception as e:
                logging.error(f"Could not Publish result. Reason: {e}")
            return
        else:
            event.fail("Unit is not leader")

