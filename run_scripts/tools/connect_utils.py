from netmiko import ConnectHandler

def connect_device(device):
    """Open SSH to device and return Netmiko connection."""
    return ConnectHandler(
        device_type=device["device_type"],
        host=device["host"],
        username=device["username"],
        password=device["password"],
    )

