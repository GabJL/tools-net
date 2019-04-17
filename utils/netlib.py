import sys
import re
sys.path.append('..')
from utils import iplib


class NetworkException(Exception):
    pass


class Network():
    def __init__(self, ip, netmask):
        try:
            ipa = iplib.IPAddress(ip)
        except iplib.IPAddressException:
            raise NetworkException(f"{ip} is not a valid IP Address")

        mask = iplib.IPAddress("255.255.255.255")

        if type(netmask) is int:
            self.prefix = int(netmask)
            if netmask < 0 or netmask > 32:
                raise NetworkException("Netmask prefix should be a number between 0 and 32")
            self.wildcard = 32 - self.prefix
            n = mask.to_number()
            mask.from_number((n << self.wildcard) & n)
            self.netmask = mask
        elif type(netmask) is str:
            try:
                self.netmask = iplib.IPAddress(netmask)
                valid, self.prefix = self.__check_mask(self.netmask.to_number())
                if not valid:
                    raise NetworkException(f"{netmask} is not a valid network mask")
                self.wildcard = 32 - self.prefix
            except iplib.IPAddressException:
                raise NetworkException("Netmask is not valid (it should be a mask or a prefix)")
        else:
            raise NetworkException("Netmask is not valid (it should be a mask or a prefix)")

        ipa.from_number(ipa.to_number() & self.netmask.to_number())
        self.netid = ipa

    def __check_mask(self, mask):
        bin_str = '{0:032b}'.format(mask)
        regexp = re.search(r"^(1*)0*$", bin_str)
        if not regexp:
            return False,0
        return True, len(regexp.group(1))

    def get_id(self):
        return str(self.netid)

    def get_metmask(self):
        return str(self.netmask)

    def get_netprefix(self):
        return self.prefix

    def get_broadcast(self):
        ipa = iplib.IPAddress("0.0.0.0")
        ipa.from_number(self.netid.to_number() + 2**self.wildcard - 1)
        return str(ipa)

    def get_first_host_ip(self):
        ipa = iplib.IPAddress("0.0.0.0")
        ipa.from_number(self.netid.to_number() + 1)
        return str(ipa)

    def get_last_host_ip(self):
        ipa = iplib.IPAddress("0.0.0.0")
        ipa.from_number(self.netid.to_number() + 2**self.wildcard - 2)
        return str(ipa)

    def get_number_of_hosts(self):
        return 2**self.wildcard - 2

    def __str__(self):
        return str(self.netid) + '/' + str(self.prefix)

    def overlap(self, other: 'Network'):
        first1 = self.netid
        last1 = iplib.IPAddress(self.get_broadcast())
        first2 = other.netid
        last2 = iplib.IPAddress(other.get_broadcast())

        if last1 < first2:
            return False
        elif last2 < first1:
            return False
        else:
            return True
