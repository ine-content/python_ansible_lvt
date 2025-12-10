from tools.inventory_utils import load_devices_from_yaml
from tools.config_utils import push_config
import getpass
import os

# Load devices from YAML
devices = load_devices_from_yaml()

# Credentials
username = input("Username: ")
password = getpass.getpass("Password: ")

# Ask how to get config
print("\n✔ Choose a method to send configs to devices")
method = input("\n⭐1 = Manual Config, ⭐2 = File Config: ")

config = []

if method == "2":
    filename = input("Config filename: ")

    if os.path.isfile(filename):
        # Read from file
        with open(filename) as f:
            for line in f:
                line = line.strip()
                if line:
                    config.append(line)
    else:
        print("❌ File not found. Switching to manual entry.")
        method = "1"

if method == "1":
    print("\n⭐ Enter config (empty line to finish):")
    while True:
        line = input()
        if line == "":
            break
        config.append(line)

# Push config to each device
for d in devices:
    print(f"\n✅ Pushing config to {d['hostname']}...")
    push_config(d, config, username, password)
