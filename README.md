# Pequeños desarrollos basados en el contenido de la asignatura de Redes y Sistemas Distribuidos

En este repositorio voy a incluir algunas herramientas básicas que cubren algunos de los elementos vistos en la asignatura tales como direcciones MAC, IPs, redes, etc.

## Índice
* [Requisitos e Instalación](#requisitos-e-instalacin)
* [Herramientas](#herramientas)
    * [MAC Analyzer](#mac-analyzer)
    * [Network Interfaces](#network-interfaces)
* [Módulos interesantes](#mdulos-interesantes)

## Requisitos e instalación

Requiere Python 3.

Algunas herramientas requieren módulos adicionales.

No requiere instalación, solo descargue o clone el respositorio para utilizarlo.

## Herramientas

### MAC Analyzer

Esta herramienta recibe una MAC en el formato hexadecimal (usando como separador dos puntos, guiones o puntos) y si es válida nos devuelve la siguiente información:

* ID fabricante (incluyendo el nombre si es posible obtenerlo)
* Número de serie
* Si es localmente administrada o es global
* Si es unicat o multicast

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
lo: 00:00:00:00:00:00 - (global)- up
wlp2s0: a4:c5:cd:e1:cd:9d - (global)- up
```

## Módulos interesantes

* [netifaces](https://alastairs-place.net/projects/netifaces/): Nos permite consultar los interfaces de red disponibles en el equipo.
* [psutil](https://psutil.readthedocs.io/en/latest/): Ofrece información de los procesos y del sistema (incluyendo información de red).
* [ipaddress](https://docs.python.org/3/howto/ipaddress.html): Módulo para el manejo de direcciones IP y redes.