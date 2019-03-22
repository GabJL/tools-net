import sys
sys.path.append('..')
from utils import maclib


try:
    import psutil
    option = 1
except:
    try:
        import netifaces
        option = 2
    except:
        option = 3


def print_info(nic, mac, up):
    print(f"{nic}: {mac} - (", end="")
    if mac.is_local():
        print("local", end="")
    else:
        print("global", end="")
    print(f")- {up}")


def get_ifaces_with_netifaces():
    netifs = netifaces.interfaces()

    for nic in netifs:
        info = netifaces.ifaddresses(nic).get(netifaces.AF_LINK)
        if info:
            mac = maclib.MACAddress(info[0]['addr'])
            print_info(nic, mac, "up")


def get_ifaces_with_psutil():
    stats = psutil.net_if_stats()
    for nic, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == psutil.AF_LINK:
                mac = maclib.MACAddress(addr.address)
                up = "up"
                if nic in stats:
                    st = stats[nic]
                    if not st.isup:
                        up = "down"
                print_info(nic, mac, up)
                break


if __name__ == "__main__":
    if option == 1:
        get_ifaces_with_psutil()
    elif option == 2:
        get_ifaces_with_netifaces()
    else:
        print("netiface or psutil modules are required")

