from tools.inventory_utils import load_devices_from_yaml
from tools.show_utils import run_show_commands
import getpass

# Load devices
devices = load_devices_from_yaml()

# Ask for login credentials
username = input("Username: ")
password = getpass.getpass("Password: ")

# Ask user for show command
cmd = input("Enter show command: ")
commands = [cmd]  # show_utils expects a list

# Run on every device
for d in devices:
    print(f"\n✅ Running '{cmd}' on {d['hostname']}...")
    run_show_commands(d, commands, username, password)
