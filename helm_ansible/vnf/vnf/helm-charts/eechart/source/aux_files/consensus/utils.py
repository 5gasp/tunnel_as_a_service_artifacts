import requests
import json

WG_LOCATION = "/etc/wireguard"
PEER_ADDRESSES_LOCATION = "/home/ubuntu/aux_files/peers_addresses.txt"
PREPARE_STATUS = "PREPARE"
READY_STATUS = "READY"
ABORT_STATUS = "ABORT"
TIMEOUT_SECONDS = 10


def publish_data(endpoint, data):
    _json = json.dumps(data)
    try:
        r = requests.post(url=endpoint, json=_json)
        if r.status_code != 200 or r.status_code != 201:
            msg = r.json()["message"]
            print(f"Error publishing. Reason: {msg}")
        else:
            data = r.json()
            print(f"Success Publishing")
        return
    except Exception as e:
        print(f"Could not Publish result. Reason: {e}")
    return
