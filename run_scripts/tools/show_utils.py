# show_utils.py

from getpass import getpass

# Dual-mode imports: works inside tools/ and when imported as tools.show_utils
try:
    # When tools is a package (imported as tools.show_utils)
    from .inventory_utils import load_devices_from_yaml
    from .cisco_data_fetchers import get_netmiko_connection
except ImportError:
    # When running this file directly from inside tools/
    from inventory_utils import load_devices_from_yaml
    from cisco_data_fetchers import get_netmiko_connection


def run_show_commands(device, commands, username, password):
    """Connect and run show commands using Netmiko connection helper."""
    hostname = device.get("hostname", device.get("host", "unknown"))
    host = device["host"]
    device_type = device.get("device_type", "cisco_ios")

    conn = None
    try:
        conn = get_netmiko_connection(host, username, password, device_type)

        for cmd in commands:
            output = conn.send_command(cmd)
            print(f"\n✅ {hostname} - {cmd}\n{output}\n")

    except Exception as error:
        print(f"\n❌ ERROR running show commands on {hostname}: {error}\n")
    finally:
        if conn:
            conn.disconnect()


if __name__ == "__main__":
    print("\n=== Run Show Commands on Multiple Devices ===")
    username = input("Enter username: ")
    password = getpass("Enter password: ")

    # Load devices from YAML
    devices = load_devices_from_yaml()

    # Example show commands (edit as needed)
    commands = [
        "show ip interface brief",
        "show version",
    ]

    for dev in devices:
        run_show_commands(dev, commands, username, password)
