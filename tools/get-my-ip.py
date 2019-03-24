import requests


if __name__ == "__main__":
    ip = requests.get("https://api.ipify.org")
    if ip.status_code != 200:
        print("Your public IP cann't obtained")
    else:
        print(f"Your public IP is {ip.text}")