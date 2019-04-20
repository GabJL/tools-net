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
        except Exception as e:
            raise NetSystemException(f"There is a problem reading the configuration file {filename}: {e}")

        self.__analyze_nets(data)

    def __analyze_nets(self, d):
        if not d.get("configuration", None):
            raise NetSystemException("There is no configuration section in system description")

        try:
            self.system_net = netlib.Network(d["configuration"].get("IP", None),
                                             d["configuration"].get("mask", None))
        except netlib.NetworkException as e:
            raise NetSystemException(f"The provided network is not valid ({e})")

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
            added = False
            for n in h["networks"]:
                for n1 in self.networks:
                    if n == n1['name']:
                        if h['name'] in n1['related hosts']:
                            raise NetSystemException(f"Node {h['name']} is repeated in network {n1['name']}")
                        n1["related hosts"].append(h['name'])
                        n1["ips needed"] += 1
                        if not added:
                            self.nodes.append(h)
                            added = True
                        break
                else:
                    raise NetSystemException(f"Node {h['name']} is assigned to unknown network ({n})")

        self.networks = sorted(self.networks, key=lambda k: k['ips needed'], reverse=True)

        min_nets = self.__min_power_of_2(len(self.networks))
        max_hosts = 0
        min_total_ips = 0
        for n in self.networks:
            n["bits"] = self.__min_power_of_2(n["ips needed"])
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
                next_ip.from_number(next_ip.to_number()+1)
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
                next_ip.from_number(next_ip.to_number()+1)
                free_ip = str(next_ip)
        else: # preconfigured
            for n in self.networks:
                try:
                    n["network"] = netlib.Network(n["netid"], n["netmask"])
                    if not self.system_net.is_in(n["network"]):
                        raise NetSystemException(f"Net {n['name']} is not inside of {self.system_net}")
                except Exception:
                    raise NetSystemException(f"Configuration of net {n['name']} is not correct.")
                for n1 in self.networks:
                    if n["name"] != n1["name"]:
                        if __name__ == '__main__':
                            if n["network"].overlap(n1["network"]):
                                raise NetSystemException(f"{n['name']} and {n1['name']} are overlapping nets.")
        self.__assign_macs()

    def __assign_macs(self):
        used_macs = []
        for n in self.nodes:
            if n.get('macs', None):
                used_macs += n['macs']
            else:
                n['macs'] = []

        free_mac = maclib.MACAddress('00:00:00:00:00:00')
        while str(free_mac) in used_macs:
            free_mac = free_mac.next_mac()

        for n in self.nodes:
            while len(n['macs']) < len(n['networks']):
                n['macs'].append(str(free_mac))
                used_macs.append(n['macs'][-1])
                while str(free_mac) in used_macs:
                    free_mac = free_mac.next_mac()

    @staticmethod
    def __min_power_of_2(n):
        bits = 1
        pow = 2
        while pow < n:
            bits += 1
            pow *= 2
        return bits
