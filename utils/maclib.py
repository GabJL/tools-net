import re
import requests

class MACAddressException(Exception):
    pass


class MACAddress():
    def __init__(self, mac):
        if not self.__check_mac(mac):
            raise MACAddressException("MAC incorrecta")
        self.mac = mac.replace("-",":").replace(".",":").lower()

    def __check_mac(self, mac):
        sep_counter = 0
        if mac.find(":") > 0:
            sep_counter += 1
        if mac.find(".") > 0:
            sep_counter += 1
        if mac.find("-") > 0:
            sep_counter += 1
        if sep_counter != 1:
            return False
        mac = mac.replace("-",":").replace(".",":").lower()
        return re.search(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$", mac)

    def __str__(self):
        return self.mac

    def get_vendor_id(self):
        vendor = self.mac[:len(self.mac)//2]
        vendor = vendor[0] + hex(int(vendor[1],16) & 0xc)[-1] + vendor[2:]
        return vendor

    def get_vendor_name(self):
        url = "https://macvendors.co/api/vendorname/"+self.get_vendor_id()
        response = requests.get(url)
        if response.status_code != 200:
            return None
        else:
            return response.text

    def get_serial_number(self):
        return self.mac[len(self.mac)//2 + 1:]

    def is_local(self):
        return int(self.mac[1], 16) & 0x2

    def is_global(self):
        return not self.is_local()

    def is_multicast(self):
        return int(self.mac[1], 16) & 0x1

    def is_unicast(self):
        return not self.is_multicast()

    def is_broadcast(self):
        return self.mac == "ff:ff:ff:ff:ff:ff"
