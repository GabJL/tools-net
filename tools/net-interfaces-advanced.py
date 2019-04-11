import sys, socket
sys.path.append('..')
from utils import maclib

try:
	import psutil
	option = 1
except:
	option = 2

def get_ifaces_with_psutil():
	addrs = psutil.net_if_addrs()
	stats = psutil.net_if_stats()

	for i in addrs:
		for t in addrs[i]:
			if t.family == socket.AF_INET:
				ip = t.address
				nm = t.netmask
				bc = t.broadcast

			if t.family == psutil.AF_LINK:
				try:
					mac = maclib.MACAddress(t.address)
					print(f"{i}: {mac}", end =" ")

					if mac.is_local():
						print("- (local)", end =" ")
					else:
						print("- (global)", end =" ")

					if stats[i].isup:
						print("- up")
					else:
						print("- down")

					if ip != None:
						print(f" IP: {ip}")
						print(f" Netmask: {nm}")
						print(f" Broadcast: {bc}")
					else:
						print(" IP: Unassigned")

					if stats[i].duplex == psutil.NIC_DUPLEX_FULL:
						print(" Duplex mode: FULL-DUPLEX")
					elif stats[i].duplex == psutil.NIC_DUPLEX_HALF:
						print(" Duplex mode: HALF-DUPLEX")
					else:
						print(" Duplex mode: Unknown")
					print(f" Speed (MB/s): {stats[i].speed}")
					print(f" MTU: {stats[i].mtu}")

					print()
					ip = None
					break
				except maclib.MACAddressException:
					pass

if __name__ == "__main__":
	if option == 1:
		get_ifaces_with_psutil()
	else:
		print("netifaces or psutil modules are required")


