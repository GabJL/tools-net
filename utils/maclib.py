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
        ''' Explicación de la expresión regular
            [0-9a-f]{2}: dos dígitos hexadecimal
            [:-\\.]: separadores validos
            \1: nos referimos al primer grupo () y forzamos que sea el mismo luego'''
        return re.search(r"^[0-9a-f]{2}([:-\\.])[0-9a-f]{2}(\1[0-9a-f]{2}){4}$",mac.lower())

    def __str__(self):
        return self.mac

    def get_vendor_id(self):
        return self.mac[:len(self.mac)//2]

    def get_vendor_name(self):
        url = "https://macvendors.co/api/vendorname/"+self.get_vendor_id()
        response = requests.get(url)
        if response.status_code != 200:
            return "Unknown"
        else:
            return response.text

    def get_serial_number(self):
        return self.mac[len(self.mac)//2 + 1:]

    def is_local(self):
        return hex(self.mac[1]) & 0x2

    def is_global(self):
        return not self.is_local()

    def is_multicast(self):
        return hex(self.mac[1]) & 0x1

    def is_unicast(self):
        return not self.is_multicast()

    def is_broadcast(self):
        return self.mac == "ff:ff:ff:ff:ff:ff"
