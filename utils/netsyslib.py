import sys

sys.path.append('..')
from utils import iplib, maclib, netlib
import json


class Node:
    MAX_ROUTING_COST = 15
    def __init__(self, name):
        self.name = name
        self.border = False
        self.interfaces = []
        self.arp_table = {}
        self.ip_table = {}

    def set_as_border(self):
        self.border = True

    def new_interface(self):
        pos = len(self.interfaces)
        i = {'name': 'nic' + str(pos), "ip": None, "mac": None, "net": None}
        self.interfaces.append(i)
        return pos

    def remove_interface(self, pos):
        if len(self.interfaces) > pos:
            del (self.interfaces[pos])

    def get_name(self):
        return self.name

    def get_interface(self, pos):
        if len(self.interfaces) > pos:
            return self.interfaces[pos]

    def set_ip(self, pos, ip):
        if len(self.interfaces) > pos:
            self.interfaces[pos]['ip'] = ip

    def set_mac(self, pos, mac):
        if len(self.interfaces) > pos:
            self.interfaces[pos]['mac'] = mac

    def set_net(self, pos, network):
        if len(self.interfaces) > pos:
            self.interfaces[pos]['net'] = network

    def get_number_of_interfaces(self):
        return len(self.interfaces)

    def __str__(self):
        description = ""
        description += f"- {self.name}:\n"
        for i in self.interfaces:
            description += f"\t{i['name']} - {i['mac']} | {i['ip']} ({i['net']['name']})\n"
        if self.border:
            description += f"\tThis node allows to connect to Internet\n"
        return description

    def add_to_arp_table(self, ip, mac):
        self.arp_table[ip] = mac

    def query_arp_table(self, ip):
        return self.arp_table.get(ip)

    def get_arp_table(self):
        return self.arp_table

    def create_ip_table(self, nets):
        self.ip_table = {}
        for n in nets:
            self.ip_table[n] = {'next step': None, 'cost': self.MAX_ROUTING_COST}
            if any(x['net'] == n for x in self.interfaces):
                self.ip_table[n] = {'cost': 1}


class NetSystemException(Exception):
    pass


class NetSystem:
    def __init__(self, filename):
        try:
            with open(filename) as f:
                data = json.load(f)
        except Exception as exc:
            raise NetSystemException(f"There is a problem reading the configuration file {filename}: {exc}")

        self.__analyze_nets(data)

    def __analyze_nets(self, d):
        if not d.get("configuration", None):
            raise NetSystemException("There is no configuration section in system description")

        try:
            self.system_net = netlib.Network(d["configuration"].get("IP", None),
                                             d["configuration"].get("mask", None))
        except netlib.NetworkException as exc:
            raise NetSystemException(f"The provided network is not valid ({exc})")

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
        for h in d.get("named nodes", []):
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
        else:
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
        self.__create_interfaces()
        if d['configuration']['type'] != 'Preconfigured':
            self.__assign_ips()

        border_router = d["configuration"].get("border router", None)
        self.has_Internet = False
        if border_router:
            for n in self.nodes:
                if n.get_name() == border_router:
                    n.set_as_border()
                    self.has_Internet = True
                    break


    def __create_interfaces(self):
        used_macs = []
        aux = self.nodes
        self.nodes = []
        for n in aux:
            self.nodes.append(Node(n['name']))
            if n.get('macs', None):
                used_macs += n['macs']
            else:
                n['macs'] = []

        free_mac = maclib.MACAddress('00:00:00:00:00:00')
        while str(free_mac) in used_macs:
            free_mac = free_mac.next_mac()

        for h, n in enumerate(aux):
            while len(n['macs']) < len(n['networks']):
                n['macs'].append(str(free_mac))
                used_macs.append(n['macs'][-1])
                while str(free_mac) in used_macs:
                    free_mac = free_mac.next_mac()
            for i in range(len(n['networks'])):
                pos = self.nodes[h].new_interface()
                self.nodes[h].set_mac(pos, maclib.MACAddress(n['macs'][i]))
                for net in self.networks:
                    if net['name'] == n['networks'][i]:
                        self.nodes[h].set_net(pos, net)

    def __assign_ips(self):
        for h in self.nodes:
            for p in range(h.get_number_of_interfaces()):
                interface = h.get_interface(p)
                if not interface['net'].get('first_ip_free', None):
                    ip = iplib.IPAddress(interface['net']['network'].get_id())
                    ip.from_number(ip.to_number()+1)
                    interface['net']['first_ip_free'] = ip
                interface['ip'] = iplib.IPAddress(str(interface['net']['first_ip_free']))
                ip = interface['net']['first_ip_free']
                ip.from_number(ip.to_number() + 1)

    @staticmethod
    def __min_power_of_2(n):
        bits = 1
        pow = 2
        while pow < n:
            bits += 1
            pow *= 2
        return bits

    def __str__(self):
        description = ""
        description += "Networks:\n"
        for n in self.networks:
            description += f"- {n['name']}\n"
            description += f"\t ID/Mask {n['network']}\n"
            description += f"\t Broadcast: {n['network'].get_broadcast()}\n"
            ip = iplib.IPAddress('0.0.0.0')
            ip.from_number(n['first_ip_free'].to_number() + n['hosts'] -1)
            description += f"\t Host: {n['first_ip_free']}-{ip}\n"
            description += f"\t MTU: {n['MTU']}\n"
        description += "Nodes:\n"
        for n in self.nodes:
            description += str(n)
        return description


if __name__ == '__main__':
    try:
        net = NetSystem('../tools/samples/networks.json')
    except NetSystemException as e:
        print(e)
    print(net)