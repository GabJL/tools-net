import sys
sys.path.append('..')
from utils import iplib


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <IP address>")
        exit(-1)

    try:
        ip = iplib.IPAddress(sys.argv[1])
    except:
        print(f"{sys.argv[1]} is not a valid IPv4 address")
        exit(-1)

    print(f"{sys.argv[1]} is from class {ip.get_class()}")
