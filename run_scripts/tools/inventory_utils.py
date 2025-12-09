import os
import yaml

def load_devices_from_yaml(filename="devices.yaml"):
    """Load devices from YAML and return the list."""

    # Folder where this file lives (e.g. tools/)
    base = os.path.dirname(__file__)
    path = os.path.join(base, filename)

    # Read YAML
    with open(path) as f:
        data = yaml.safe_load(f)

    # devices already have 'host' in YAML
    return data["devices"]

