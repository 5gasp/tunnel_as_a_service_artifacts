from pyroute2 import IPRoute, netlink
from ping_wrapper import PingWrapper


# TODO: Change multiple args to **kwargs
class RoutesWrapper:
    def __init__(self) -> None:
        self.ipr = IPRoute()
        self.routes = []
        self.ping_mgmt = PingWrapper()

    def get_main_table_routes(self, rta_dst, oif):
        rta_dst = rta_dst.split("/")[0]
        self.routes = self.ipr.get_routes(
            table=254, family=netlink.AF_INET, rta_dst=rta_dst, oif=oif
        )
        return self.routes

    def get_dest_network_routes(self, rta_dst, interface_name):
        interface_index = self.ipr.link_lookup(ifname=interface_name)[0]
        return self.get_main_table_routes(rta_dst=rta_dst, oif=interface_index)

    def get_priority(self, route):
        return route.get_attr("RTA_PRIORITY") or 0

    def sorte_routes(self, routes, criteria="priority", reverse=False):
        key = None
        if criteria == "priority":
            key = self.get_priority
        return sorted(routes, key=key, reverse=reverse)

    def manage_new_route(self, dest_network, gateway, interface_name):
        # Get routes in a specific inteface, whose destination network is rta_dst
        routes = self.get_dest_network_routes(
            rta_dst=dest_network, interface_name=interface_name
        )
        print(f"Routes: {routes}")

        # sort them by priority(higher the metric, lower the priority)
        srt_routes = self.sorte_routes(routes=routes)
        print(f"Sorted Routes: {srt_routes}")
        weight = None
        if self.is_priority_zero(srt_routes):
            # add a temporary weight is the lowest metric is 0
            weight = 50
            # check if the gateway is a next-hop or an "directly-connected" network
            # if it is none, no gateway is specified when replace and removing the route
            original_gateway = srt_routes[0].get("RTA_GATEWAY")
            proto = srt_routes[0]["proto"]
            scope = srt_routes[0]["scope"]
            print(("Replacing original route's weight..."))
            self.replace_route_weight(
                dest_network=dest_network,
                gateway=original_gateway,
                interface_name=interface_name,
                weight=weight,
            )
            print(("Deleting default route...", original_gateway))
            # delete the 0 metric route
            self.remove_route(
                dest_network=dest_network,
                gateway=original_gateway,
                interface_name=interface_name,
                proto=proto,
                scope=scope,
            )
            weight = weight - int(0.30 * weight)
        else:
            weight = self.find_best_weight(srt_routes)
        # finally add the new route
        print("Adding route...")
        self.add_route(
            dest_network=dest_network,
            interface_name=interface_name,
            gateway=gateway,
            weight=weight,
        )

    def is_priority_zero(self, routes):
        r = routes[0]
        priority = r.get_attr("RTA_PRIORITY")
        return priority == None

    def check_route(self, interface, target):
        res = self.ping_mgmt.run_ping(interface=interface, destination=target)
        if self.ping_mgmt.check_success_connection(res):
            print("OK")
            return True
        else:
            raise Exception("The new route could not be applied")

    def find_best_weight(self, routes):
        prior_route = routes[0]
        higher_weight = prior_route.get_attr("RTA_PRIORITY")
        # Reduce 50% The Weight
        return higher_weight - int(0.30 * higher_weight)

    def add_route(self, dest_network, gateway, interface_name, weight):
        interface_index = self.ipr.link_lookup(ifname=interface_name)[0]
        print("gateway", gateway)
        self.ipr.route(
            "add",
            dst=dest_network,
            gateway=gateway,
            oif=interface_index,
            priority=weight,
            proto=4,
        )

    def remove_route(
        self, dest_network, gateway, interface_name, proto=None, scope=None, weight=None
    ):
        interface_index = self.ipr.link_lookup(ifname=interface_name)[0]
        print("parameters", dest_network, gateway, interface_name, weight)
        self.ipr.route(
            "delete",
            dst=dest_network,
            gateway=gateway,
            oif=interface_index,
            priority=weight,
            proto=proto,
            scope=scope,
        )

    def replace_route_weight(self, dest_network, gateway, interface_name, weight):
        interface_index = self.ipr.link_lookup(ifname=interface_name)[0]
        self.ipr.route(
            "replace",
            dst=dest_network,
            gateway=gateway,
            oif=interface_index,
            priority=weight,
            table=254,
            family=netlink.AF_INET,
        )
