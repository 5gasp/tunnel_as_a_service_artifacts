# @Author: Daniel Gomes
# @Date:   2023-02-13 16:50:49
# @Email:  dagomes@av.it.pt
# @Copyright: Insituto de Telecomunicações - Aveiro, Aveiro, Portugal
# @Last Modified by:   Daniel Gomes
# @Last Modified time: 2023-02-14 09:42:56

import os
import wgconfig
import json
# _path = os.environ.get('WgConfigLocalFilePath')
# tunnel_peer_address = os.environ.get('tunnel_peer_address')
# save_config = os.environ.get('save_config')
# listen_port = os.environ.get('listen_port')
# wg_pk = os.environ.get('wg_pk').strip()

_vars = json.loads(os.environ.get('ANSIBLE_JSON'))
_path = _vars['WgConfigLocalFilePath']
tunnel_peer_address = _vars['tunnel_peer_address']
save_config = _vars['save_config']
listen_port = _vars['listen_port']
wg_pk = _vars['wg_pk'].strip()

def create_config_file():
    if not os.path.exists(_path):
        if not os.path.exists("/tmp/wireguard"):
            os.mkdir("/tmp/wireguard")
        open(_path, 'a').close()


def write_to_file():
    m_wgconfig = wgconfig.WGConfig(_path)
    m_wgconfig.add_attr(None, 'Address', tunnel_peer_address + "/24")
    m_wgconfig.add_attr(None, 'SaveConfig', save_config)
    m_wgconfig.add_attr(None, 'ListenPort', listen_port)
    m_wgconfig.add_attr(None, 'PrivateKey', wg_pk)
    m_wgconfig.write_file()


if __name__ == "__main__":
    create_config_file()
    write_to_file()
