import os
import yaml

def run_ping_check(ips):
    """Ping each IP once and print reachability."""
    for ip in ips:
        # -c 1 = send 1 ping, hide output
        result = os.system(f"ping -c 1 {ip} > /dev/null 2>&1")
        if result == 0:
            print(f"✅{ip} is reachable.")
        else:
            print(f"❌{ip} is NOT reachable.")

if __name__ == "__main__":
    # Read devices from YAML (under tools/)
    with open("tools/devices.yaml") as f:
        data = yaml.safe_load(f)

    # Use 'host' from YAML
    ips = []
    for dev in data["devices"]:
        ips.append(dev["host"])

    run_ping_check(ips)

