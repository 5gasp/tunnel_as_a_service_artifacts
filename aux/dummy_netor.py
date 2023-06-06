# @Author: Daniel Gomes
# @Date:   2022-10-04 14:29:42
# @Email:  dagomes@av.it.pt
# @Copyright: Insituto de Telecomunicações - Aveiro, Aveiro, Portugal
# @Last Modified by:   Rafael Direito
# @Last Modified time: 2022-10-10 19:29:35

from powerdns_netor import Netor_DNS_SD
import argparse
import aux
from enum import Enum


class NetOr:

    def __init__(self):
        Constants = aux.Constants()

        self.netor_wrapper = Netor_DNS_SD(
            dns_ip=Constants.DNS_IP,
            api_port=Constants.DNS_API_PORT,
            api_key=Constants.DNS_API_KEY,
            vsi_id=Constants.VSI_ID
        )

    def create_zone(self):
        self.netor_wrapper.create_zone()

    def delete_zone(self):
        try:
            self.netor_wrapper.delete_zone()
        except Exception as e:
            pass


class Operation(Enum):
    create_zone = 'create_zone'
    delete_zone = 'delete_zone'

    def __str__(self):
        return self.value


if __name__ == "__main__":
    parser = argparse.ArgumentParser("dummy_netor.py")
    parser.add_argument(
        "--operation",
        help="(create_zone or delete_zone)",
        type=Operation
    )
    args = parser.parse_args()

    print(args.operation)
    netor = NetOr()
    if args.operation.value == "create_zone":
        netor.create_zone()
    elif args.operation.value == "delete_zone":
        netor.delete_zone()
