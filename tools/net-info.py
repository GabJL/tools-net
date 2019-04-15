import sys
sys.path.append('..')
from utils import netlib


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <IP address> <Mask (IP or Prefix)>")
        exit(-1)

    try:
        try:
            mask = int(sys.argv[2])
        except Exception:
            mask = sys.argv[2]
        net = netlib.Network(sys.argv[1], mask)
        print(f"Network: {net}")
        print(f"- Network ID: {net.get_id()}")
        print(f"- Network Mask: {net.get_metmask()}")
        print(f"- Broadcast: {net.get_broadcast()}")
        print(f"- First Host: {net.get_first_host_ip()}")
        print(f"- Last Host: {net.get_last_host_ip()}")
        print(f"- Number of hosts: {net.get_number_of_hosts()}")
    except netlib.NetworkException as e:
        print(e)
