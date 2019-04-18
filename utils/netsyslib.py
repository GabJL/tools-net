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
