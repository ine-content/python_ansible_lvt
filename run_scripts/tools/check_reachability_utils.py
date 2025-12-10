# check_reachability_utils.py
import os

# Try relative import (when tools is a package)
try:
    from .inventory_utils import load_devices_from_yaml
except ImportError:
    # Fallback: when running this file directly from inside tools/
    from inventory_utils import load_devices_from_yaml

def run_ping_check(ips):
    """Ping each IP once and print reachability."""
    for ip in ips:
        # -c 1 = send 1 ping, hide output
        result = os.system(f"ping -c 1 {ip} > /dev/null 2>&1")
        if result == 0:
            print(f"✅ {ip} is reachable.")
        else:
            print(f"❌ {ip} is NOT reachable.")


if __name__ == "__main__":
    print("\n=== Ping Reachability Check ===")

    # Load devices from YAML
    devices = load_devices_from_yaml()

    # Extract IP/host list
    ips = [dev["host"] for dev in devices]

    run_ping_check(ips)
