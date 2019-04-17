import re

class IPAddressException(Exception):
    pass


class IPAddress():
    def __init__(self, ip):
        if not self.__check_ip(ip):
            raise IPAddressException("Incorrect IP")
        self.ip = ip

    def __check_ip(self, ip):
        if not re.search(r"^([0-9]{1,3}.){3}[0-9]{1,3}$", ip):
            return False
        values = ip.split(".")
        if len(values) != 4:
            return False
        try:
            for v in values:
                v = int(v)
                if v < 0 or v > 255:
                    return False
        except:
            return False
        return True

    def __str__(self):
        return self.ip

    def get_class(self):
        first_byte = int(self.ip.split(".")[0])

        if not first_byte & 0x80:
            return 'A'
        elif not first_byte & 0x40:
            return 'B'
        elif not first_byte & 0x20:
            return 'C'
        elif not first_byte & 0x10:
            return 'D'
        else:
            return 'E'

    def to_number(self):
        values = self.ip.split(".")
        number = 0
        for byte in values:
            number = number*256 + int(byte)

        return number

    def from_number(self, number):
        self.ip = str(number % 256)
        number = number // 256
        for i in range(3):
            self.ip = str(number % 256) + '.' + self.ip
            number = number // 256

    def __lt__(self, other):
        return self.to_number() < other.to_number()

    def __le__(self, other):
        return self.to_number() <= other.to_number()

    def __eq__(self, other):
        return self.to_number() == other.to_number()

    def __ne__(self, other):
        return self.to_number() != other.to_number()

    def __gt__(self, other):
        return self.to_number() > other.to_number()

    def __ge__(self, other):
        return self.to_number() >= other.to_number()