from tools.inventory_utils import load_devices_from_yaml
from tools.check_reachability_utils import run_ping_check

# Load devices from YAML
devices = load_devices_from_yaml()

# Build a list of IPs (host values)
ips = []
for d in devices:
    ips.append(d["host"])

# Run ping test
run_ping_check(ips)

