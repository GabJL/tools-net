# Pequeños desarrollos basados en el contenido de la asignatura de Redes y Sistemas Distribuidos

En este repositorio voy a incluir algunas herramientas básicas que cubren algunos de los elementos vistos en la asignatura tales como direcciones MAC, IPs, redes, etc.

## Índice
* [Requisitos e Instalación](#requisitos-e-instalacin)
* [Herramientas](#herramientas)
    * [MAC Analyzer](#mac-analyzer)
    * [Network Interfaces](#network-interfaces)
    * [Network Interfaces: Advanced](#network-interfaces-advanced)
    * [My public IP](#get-my-public-ip)
    * [IP Class](#ip-class)
* [Otros](#otros)
    * [Parseo de resúmenes generados con tshark](#anlisis-de-la-salida-de-tshark)
* [Módulos interesantes](#mdulos-interesantes)
* [APIs interesantes](#apis-interesantes)
* [Anexo: Uso de tshark básico](#anexo-uso-bsico-de-tshark)
* [Futuros desarrollos](#prximos-desarrollos) 

## Requisitos e instalación

Requiere Python 3.

Algunas herramientas requieren módulos adicionales. Se ha incluido el fichero *requirements.txt* para facilitar su instalación
de la siguiente forma:

```console
user@computer:path-tools-net$ pip3 install -r requirements.txt
```

No requiere instalación, solo descargue o clone el respositorio para utilizarlo.

## Herramientas

### MAC Analyzer

Esta herramienta recibe una MAC en el formato hexadecimal (usando como separador dos puntos, guiones o puntos) y si es válida nos devuelve la siguiente información:

* ID fabricante (incluyendo el nombre si es posible obtenerlo)
* Número de serie
* Si es localmente administrada o es global
* Si es unicat o multicast

El nombre del fabricante lo obtiene haciendo uso del API [MA:CV:en:do:rs](https://macvendors.com/)

Un ejemplo de funcionamiento:

```console
user@computer:~/path-tools-net$ python3 -m tools.mac-analyzer 03:11:22:33:44:55
Complete MAC: 03:11:22:33:44:55
Vendor:
    ID: 00:11:22
    Name: CIMSYS Inc
Serial Number: 33:44:55
This address is locally administered
This address is multicast
```

### Network Interfaces

Esta herramienta muestra los interfaces de red disponibles en el equipo y cierta información del interfaz.

Esta herramienta necesita tener instalados el módulo netifaces o psutil.

Un ejemplo de funcionamiento:

```console
user@Gcomputer:~/path-tools-net$ python3 -m tools.net-interfaces
lo: 00:00:00:00:00:00 - (global) - up
wlp2s0: a4:c5:cd:e1:cd:9d - (global) - up
```

### Network Interfaces: Advanced

Esta herramienta muestra los interfaces de red disponibles en el equipo y la siguiente información de cada interfaz:
* IP, máscara de red y dirección de broadcast (si están asignadas)
* El modo de dúplex
* La velocidad en MB/s (0 si no puede ser determinada)
* El MTU

Esta herramienta necesita tener instalados el módulo netifaces o psutil.

Un ejemplo de funcionamiento:

```console
user@Gcomputer:~/path-tools-net$ python3 -m tools.net-interfaces-advanced
lo: 00:00:00:00:00:00 - (global) - up
 IP: 127.0.0.1
 Netmask: 255.0.0.0
 Broadcast: None
 Duplex mode: Unknown
 Speed (MB/s): 0
 MTU: 65536

ens33: 00:0c:29:0e:f9:e2 - (global) - up
 IP: 172.16.157.162
 Netmask: 255.255.255.0
 Broadcast: 172.16.157.255
 Duplex mode: FULL-DUPLEX
 Speed (MB/s): 1000
 MTU: 1500
```

### Get My Public IP

Este herramienta muestra tu IP pública. Para ello usa el API de [ipify](https://www.ipify.org/).

Un ejemplo de funcionamientoo

```console
user@Gcomputer:~/path-tools-net$ python3 -m tools.get-my-ip
Your public is 37.134.241.2
```


### IP Class

Este programa recibe como parámetro una IPv4 válida (en formato decimal-punto) y nos indica a qué clase (A a F) pertenece.

Un ejemplo de funcionamientoo

```console
user@Gcomputer:~/path-tools-net$ python3 -m tools.ip-class 150.214.56.9
150.214.56.9 is from class B
```

## Otros

Ejemplos de uso de python para otros usos relacionados con la red.

### Análisis de la salida de tshark

Un elemento interesa es ser capaz de analizar las trazas de Wireshark de forma automática para extraer información o
comportamientos anormales. Una forma sencilla de hacer esto es siguiendo los siguientes pasos:

1. Usando **tshark** obtener los campos interesantes de las trazas que nos convenga
2. Crear un programa que analice esos datos de forma automática

En este ejemplo se sigue este proceso y en concreto, queremos ver la cantidad de bytes que se envían desde cada  dirección 
mac. Para ello haremos los dos siguientes pasos:

* Exportar con **tshark** las mac y tamaños de todas las tramas: 
```console
user@computer:path-net-tools$ tshark -r others/samples/traza.pcapng -T fields -e eth.dst -e eth.src -e frame.len > others/samples/datos.txt
```
* Ir recorriendo el fichero, acumulando los tamaños de las tramas atendiendo a su mac origen. Luego lo mostramos ordenados 
según cantidad de envíos:
```console
user@Gcomputer:path-tools-net$ python3 -m others.tshark-output-analysis others/samples/datos.txt 
959732 bytes send by 00:0c:29:80:d8:b3
226497 bytes send by 00:11:bc:1b:50:00
53172 bytes send by 8c:dc:d4:37:0b:69
46038 bytes send by 40:61:86:c7:c4:5d
11578 bytes send by 00:1f:5b:f6:a3:fb
3524 bytes send by c8:9c:dc:2a:28:68
...
```

## Módulos interesantes

* [ipaddress](https://docs.python.org/3/howto/ipaddress.html): Módulo para el manejo de direcciones IP y redes.
* [netifaces](https://alastairs-place.net/projects/netifaces/): Nos permite consultar los interfaces de red disponibles en el equipo.
* [psutil](https://psutil.readthedocs.io/en/latest/): Ofrece información de los procesos y del sistema (incluyendo información de red).
* [pyshark](https://kiminewt.github.io/pyshark/): Wrapper para utilizar **tshark** desde python (tanto la captura como el análisis de ficheros pcapng).
* [requests](http://docs.python-requests.org/en/master/): Módulo para hacer peticiones HTTP de forma sencilla.

## APIs interesantes

* [MA:CV:en:do:rs](https://macvendors.com/): Obtener el fabricante de un interfaz de red a partir de su mac
* [ipify](https://www.ipify.org/): Obtener la IP pública

## Anexo: Uso básico de tshark

[tshark](https://www.wireshark.org/docs/man-pages/tshark.html) es un programa incluido en la suite de Wireshark. Al 
igual que Wireshark es una herramienta para capturar y analizar tráfico de la red, pero en este caso en modo texto. Una
funcionalidad interesante que dispone es que es capaz de volcar ciertos campos de algunas tramas en un formato que es 
automatizable de forma sencilla.

Las principales opciones para conseguir esto son los siguientes:

* **-r fichero**: indica la traza a analizar
* **-Y filtro**: condiciones que deben cumplir los tramas a ser exportadas 
* **-T formato**: formato en el que se exportará. Para exportar diferentes campos en modo texto se usa la opción **-T fields**
que debe ser utilizada en conjunto con una o varias **-e** y con cero o varias **-E**:
    * **-e campo**: campo a mostrar en la exportación (se debe añadir una opción de este tipo por campo)
    * **-E opcion**: opciones sobre el formato de la exportación. 
    
A continuación se indica un ejemplo:

```console
user@Gcomputer:path-tools-net/others/samples$ tshark -r traza.pcapng -e eth.dst -e eth.src -e frame.len -e eth.ig -e eth.lg -e eth.type -T fields -E separator=/s -E aggregator=/s -Y eth.type
ff:ff:ff:ff:ff:ff 40:61:86:c7:c4:d0 92 1 0 1 0 0x00000800
ff:ff:ff:ff:ff:ff 0c:4d:e9:b8:74:97 92 1 0 1 0 0x00000800
ff:ff:ff:ff:ff:ff 0c:4d:e9:b8:74:97 92 1 0 1 0 0x00000800
01:00:5e:7f:ff:fa 40:61:86:c7:c4:83 216 1 0 0 0 0x00000800
ff:ff:ff:ff:ff:ff 40:61:86:c7:c5:a7 92 1 0 1 0 0x00000800
ff:ff:ff:ff:ff:ff 40:61:86:c7:c4:d0 92 1 0 1 0 0x00000800
...
```

En ese ejemplo se analiza el fichero *traza.pcapng*, se van a exportar ciertos campos (*-T fields*), en concreto la mac 
destino (*-e eth.dst*), la origen (*-e eth.src*)... Se filtra mostrando solo aquellas tramas que tengan tipo asignado en 
la trama ethernet (*-Y eth.type*). Finalmente, los campos se separan con espacions (*-E separator=/s*) y los campos con 
varios valores (por ejemplo, *-e eth.ig*), también se separan con espacios (*-E aggregator=/s*).

## Próximos desarrollos

Ideas que tengo en mente añadir en algún momento (aseguro que saldrán antes que el Half-Life 3). El orden del listado es
aleatorio sin ninguna relación del orden de implementación:

* Simulador de protocolos de control de flujo/error (stop & wait, go-back-n, repeat selection)
* Datos de una red (dada una iP/máscara indicar identificador, broadcast, rango de ips para hosts...)
* Redes: Dada el esquema de redes (segmentos -num equipos y mtu- y routers)
    * Asignación de IPs usando VLSM
    * Simulación de fragmentación
    * Simulación de paquetes ARP generados por un envío
* Parseo de ficheros pcapng con pyshark o scapy
* Análisis de tráfico en directo con pyshark o scapy
* Envío de algo (ARP? ICMP?) con scapy
* Ejemplo de sockets con python (tcp y udps)
* Otros módulos de nivel de aplicación en python: paramiko (ssh), telnet, poplib, smtplib, imaplib, ftplib