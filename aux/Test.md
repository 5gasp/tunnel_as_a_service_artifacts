
Start by opening 4 terminals.
In each terminal, you should activate the venv, install the requirements, and be at the *aux* directory.

Then, execute the following steps:

1. On Terminal 1, run

```bash
python3 dummy_netor.py --operation delete_zone
python3 dummy_netor.py --operation create_zone
```

1. On Terminal 2, run

`python3  dummy_peer.py --peer_id peer_1`

3. On Terminal 3, run

`python3  dummy_peer.py --peer_id peer_2`

4. On Terminal 4, run

`python3  dummy_peer.py --peer_id peer_3`
