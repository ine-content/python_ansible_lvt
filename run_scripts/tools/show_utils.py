from tools.connect_utils import connect_device

def run_show_commands(device, commands):
    """Connect and run show commands."""

    # Pick hostname to display
    if "hostname" in device:
        hostname = device["hostname"]
    elif "host" in device:
        hostname = device["host"]
    else:
        hostname = "unknown"

    try:
        conn = connect_device(device)  # Open SSH

        for cmd in commands:
            output = conn.send_command(cmd)
            print(f"\n✅{hostname} - {cmd}\n{output}\n")

        conn.disconnect()              # Close SSH
    except Exception as error:
        print(f"\n❌ERROR running show commands on {hostname}: {error}\n")

