# Pequeños desarrollos basados en el contenido de la asignatura de Redes y Sistemas Distribuidos

En este repositorio voy a incluir algunas herramientas básicas que cubren algunos de los elementos vistos en la asignatura tales como direcciones MAC, IPs, redes, etc.

# Índice
* [MAC Analyzer](#mac-analyzer)

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