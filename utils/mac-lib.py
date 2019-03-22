import re

class MACAddressException(Exception):
    pass

class MACAddress():
    def __init__(self, mac):
        if not self.__check(mac):
            raise MACAddressException("MAC incorrecta")
        self.mac = mac.replace("-",":").replace(".",":")

    def __checkMAC(self, mac):
        ''' Explicación de la expresión regular
            [0-9a-f]{2}: dos dígitos hexadecimal
            [:-\.]: separadores validos
            \\1: nos referimos al primer grupo () y forzamos que sea el mismo luego'''
        return re.search(r"^[0-9a-f]{2}([:-\.])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$",mac.lower())
