# config_utils.py

from getpass import getpass

# Dual-mode imports
try:
    # When imported as: from tools.config_utils import push_config
    from .inventory_utils import load_devices_from_yaml
    from .connect_utils import get_netmiko_connection
except ImportError:
    # When running inside tools/: python config_utils.py
    from inventory_utils import load_devices_from_yaml
    from connect_utils import get_netmiko_connection

def push_config(device, config_lines, username, password):
    """Connect and push config commands using Netmiko connection helper."""
    hostname = device.get("hostname", device.get("host", "unknown"))
    host = device["host"]
    device_type = device.get("device_type", "cisco_ios")

    conn = None
    try:
        conn = get_netmiko_connection(host, username, password, device_type)
        output = conn.send_config_set(config_lines)
        print(f"\n✅ Config pushed to {hostname}:\n{output}\n")
    except Exception as error:
        print(f"\n❌ ERROR pushing config to {hostname}: {error}\n")
    finally:
        if conn:
            conn.disconnect()


if __name__ == "__main__":
    print("\n=== Push Config to Multiple Devices ===")
    username = input("Enter username: ")
    password = getpass("Enter password: ")

    # Load devices from YAML
    devices = load_devices_from_yaml()

    # Example config lines (edit as needed)
    config_lines = [
        "interface Loopback123",
        "description Configured by config_utils.py",
    ]

    for dev in devices:
        push_config(dev, config_lines, username, password)
