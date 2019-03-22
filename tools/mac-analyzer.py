import sys
sys.path.append('..')

from utils import maclib

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <MAC Address>")
        print("\tA valid MAC address is composed by 6 groups (bytes) of two hexadecimal digits separated by :, . or -")
    else:
        try:
            mac = maclib.MACAddress(sys.argv[1])
        except maclib.MACAddressException:
            print(f"{sys.argv[1]} is not a valid MAC")

