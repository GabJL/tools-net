import sys

sys.path.append('..')
from utils import iplib, maclib, netlib
import json


class Node:
    def __init__(self, name):
        self.name = name
        self.interfaces = []
        self.arp_table = []
        self.ip_table = []

    def set_interface(self, name, ip, mac, net_name):
        if name not in self.interfaces:
            i = {'name': name, "ip": ip, "mac": mac, "net_name": net_name}
            self.interfaces.append(i)

    def remove_interface(self, name):
        for i in range(len(self.interfaces)):
            if self.interfaces[i]["name"] == name:
                del (self.interfaces[i])


class NetSystemException(Exception):
    pass


class NetSystem:
    def __init__(self, filename):
        try:
            with open(filename) as f:
                data = json.load(f)
        except Exception:
            raise NetSystemException(f"There is a problem reading the configuration file {filename}")

        self.__analyze_nets(data)

    def __analyze_nets(self, d):
        if not d.get("configuration", None):
            raise NetSystemException("There is no configuration section in system description")

        self.system_net = netlib.Network(d["configuration"].get("IP", None),
                                         d["configuration"].get("mask", None))

        if d["configuration"].get("type") not in ["VLSM", "MaxNets", "MinNets", "Preconfigured"]:
            raise NetSystemException(
                'Net configuration type is not valid (valid values are VLSM, MaxNet, MinNets or Preconfigured')

        if not d.get("networks", None) or len(d["networks"]) == 0:
            raise NetSystemException("There is no networks in the system description")

        self.networks = []
        for n in d["networks"]:
            if any(x['name'] == n["name"] for x in self.networks):
                raise NetSystemException(f"Network {n['name']} is repeated")

            self.networks.append(n)
            self.networks[-1]["ips needed"] = self.networks[-1]["hosts"] + 2
            self.networks[-1]["related hosts"] = []

        self.nodes = []
        for h in d.get("named nodes",[]):
            if not d.get("networks", []):
                raise NetSystemException(f"Node {h['name']} is not assigned to any network")
            for n in h["netowrks"]:
                for n1 in self.networks:
                    if n == n1['name']:
                        if h['name'] in n1['related hosts']:
                            raise NetSystemException(f"Node {h['name']} is repeated in network {n1['name']}")
                        n1["related host"].append(n)
                        n1["ips needed"] += 1
                        self.nodes.append(h)
                        break
                else:
                    raise NetSystemException(f"Node {h['name']} is assigned to unknown network ({n})")

        self.networks = sorted(self.networks, key=lambda k: k['ip needed'], reverse=True)

        min_nets = self.__min_power_of_2(len(self.networks))
        max_hosts = 0
        min_total_ips = 0
        for n in self.networks:
            n["bits"] = self.__min_power_of_2(n["ip needed"])
            min_total_ips += 2**n['bits']
            if n["bits"] > max_hosts:
                max_hosts = n["bits"]

        if min_total_ips > (self.system_net.get_number_of_hosts()+2):
            raise NetSystemException(
                f"The provided network {self.system_net} has a lower number of IPs than required {min_total_ips}")

        free_ip = self.system_net.get_id()
        if d["configuration"]["type"] == "VLSM":
            for n in self.networks:
                n['network'] = netlib.Network(free_ip, 32 - n["bits"])
                next_ip = iplib.IPAddress(n["network"].get_broadcast())
                next_ip = next_ip.from_number(next_ip.to_number()+1)
                free_ip = str(next_ip)
        elif d["configuration"]["type"] != "Preconfigured":
            if self.system_net.get_netprefix() + min_nets + max_hosts > 32:
                raise NetSystemException(
                    f"The number of available IPs doesnt allow to apply {d['configuration']['type']}. Try VLSM")
            if d["configuration"]["type"] == 'MinNets':
                prefix = self.system_net.get_netprefix() + min_nets
            else:
                prefix = 32 - max_hosts
            for n in self.networks:
                n['network'] = netlib.Network(free_ip, prefix)
                next_ip = iplib.IPAddress(n["network"].get_broadcast())
                next_ip = next_ip.from_number(next_ip.to_number()+1)
                free_ip = str(next_ip)


    @staticmethod
    def __min_power_of_2(n):
        bits = 1
        pow = 2
        while pow < n:
            bits += 1
            pow *= 2
        return bits