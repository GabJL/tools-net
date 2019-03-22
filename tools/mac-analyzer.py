import sys
sys.path.append('..')
from utils import maclib


def print_report(mac):
    print(f"Complete MAC: {mac}")
    print("Vendor:")
    print(f"    ID: {mac.get_vendor_id()}")
    vendor = mac.get_vendor_name()
    if vendor is not None:
        print(f"    Name: {vendor}")
    print(f"Serial Number: {mac.get_serial_number()}")
    if mac.is_local():
        print("This address is locally administered")
    else:
        print("This address is global")
    print("This address is ",end="")
    if mac.is_unicast():
        print("unicast")
    elif mac.is_broadcast():
        print("broadcast")
    else:
        print("multicast")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <MAC Address>")
        print("\tA valid MAC address is composed by 6 groups (bytes) of two hexadecimal digits separated by :, . or -")
    else:
        try:
            mac = maclib.MACAddress(sys.argv[1])
            print_report(mac)
        except maclib.MACAddressException:
            print(f"{sys.argv[1]} is not a valid MAC")

