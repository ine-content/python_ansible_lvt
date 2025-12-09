from netmiko import ConnectHandler
from getpass import getpass

username = input("Username: ")
password = getpass("Password: ")

router_ips = ["10.0.0.51", "10.0.0.52"]
output_folder = "/Users/rohitp/Scripts/Bootcamp_Network_Automation_Python_Ansible/python_ansible_lvt/basic_scripts/"

for ip in router_ips:
    try:
        print(f"✅ Connecting to {ip}...")
        conn = ConnectHandler(
            device_type="cisco_ios",
            host=ip,
            username=username,
           	password=password
        )
        hostname = conn.send_command("show run | inc hostname").split()[-1]

        # Example IF: Only save configs from hostnames starting with R
        if not hostname.startswith("CORE"):
            print(f"Skipping {hostname}: does not meet hostname rule.")
            conn.disconnect()
            continue
        
        config = conn.send_command("show run")
        file_path = f"{output_folder}{hostname}.cfg"

        with open(file_path, "w") as f:
            f.write(config)

        print(f"💾 Saved: {file_path}")

        # Example IF: If BGP is configured, save only BGP config too
        if "router bgp" in config:
            print("📡 BGP config found — saving BGP section.")
            bgp_config = conn.send_command("show run | section router bgp")
            with open(f"{output_folder}{hostname}_BGP.cfg", "w") as b:
                b.write(bgp_config)

        if "router eigrp" in config:
            print("📡 EIGRP config found — saving EIGRP section.")
            eigrp_config = conn.send_command("show run | section router eigrp")
            with open(f"{output_folder}{hostname}_EIGRP.cfg", "w") as e:
                e.write(eigrp_config)
        
        if "ip route" in config:
            print("📡 Static Routes config found — saving Static Routes section.")
            static_routes_config = conn.send_command("show run | section ip route")
            with open(f"{output_folder}{hostname}_StaticRoutes.cfg", "w") as s:
                s.write(static_routes_config)

        conn.disconnect()

    except Exception as e:
        print(f"❗Error with {ip}: {e}")


