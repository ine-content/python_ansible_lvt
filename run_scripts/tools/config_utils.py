from tools.connect_utils import connect_device

def push_config(device, config_lines):
    """Connect and push config commands."""

    # Pick hostname to display
    if "hostname" in device:
        hostname = device["hostname"]
    elif "host" in device:
        hostname = device["host"]
    else:
        hostname = "unknown"

    try:
        conn = connect_device(device)                 # Open SSH
        output = conn.send_config_set(config_lines)   # Send config
        print(f"\n✅Config pushed to {hostname}:\n{output}\n")
        conn.disconnect()                             # Close SSH
    except Exception as error:
        print(f"\n❌ERROR pushing config to {hostname}: {error}\n")

