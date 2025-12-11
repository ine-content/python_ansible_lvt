i#!/usr/bin/env python3
"""
Interactive NETCONF script for Cisco IOS-XE with emoji status output.

Flow:
- Ask for username and password (password via getpass).
- Ask for IP or a list of IPs (comma-separated).
- Ask if you want to "show" data or make "changes".
- If "show":
    - Option 1: Get FULL running-config (no filter).
    - Option 2: Custom XML subtree filter (get-config from running).
- If "changes":
    - Ask for the full <config> XML payload (multi-line, end with 'END').
    - Automatically normalizes Tail-f:
        xmlns="http://tail-f.com/ns/config/1.0"
      to NETCONF base:
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
      on the outer <config>.
    - Use candidate datastore:
        - lock candidate
        - edit-config candidate
        - validate (if :validate supported)
        - ask via menu: commit or rollback (discard-changes)
        - unlock candidate
- Every major step pauses and waits for Enter to proceed.
"""

import getpass
import socket
from contextlib import closing

from ncclient import manager
from ncclient.operations import RPCError
from ncclient.transport.errors import SSHError, SessionCloseError
from ncclient.xml_ import XMLError

# ------------- Emoji / print helpers ------------- #

ICON_OK = "✔"
ICON_FAIL = "✘"
ICON_INFO = "➡"
ICON_STEP = "⏳"
ICON_LOCK = "🔒"
ICON_UNLOCK = "🔓"
ICON_XML = "📄"
ICON_VALIDATE = "🔍"
ICON_CAPS = "🧪"
ICON_CLOSE = "🚪"


def pause(step_desc=None):
    """
    Pause execution and wait for Enter.

    Args:
        step_desc (str | None): Optional human description of the upcoming step.
    """
    if step_desc:
        print(f"\n{ICON_STEP} {step_desc}")
    input("Press Enter to continue...\n")


def ok(msg="OK"):
    """Print a success message with a green tick."""
    print(f"{ICON_OK} {msg}")


def fail(msg="ERROR"):
    """Print an error message with a red X."""
    print(f"{ICON_FAIL} {msg}")


def info(msg):
    """Print an informational message."""
    print(f"{ICON_INFO} {msg}")


# ------------- Basic NETCONF helpers ------------- #

def port_open(host, port, timeout=3):
    """
    Check if a TCP port is open.

    Returns:
        bool: True if port is open, False otherwise.
    """
    try:
        with closing(socket.create_connection((host, port), timeout=timeout)):
            return True
    except OSError:
        return False


def connect_netconf(host, username, password, ports=(830, 22)):
    """
    Try to connect to NETCONF over SSH on the given ports (in order).

    Returns:
        (m, used_port): ncclient manager session and port used.

    Raises:
        Exception if no connection succeeds.
    """
    for port in ports:
        info(f"Checking TCP {host}:{port} ...")
        if not port_open(host, port):
            fail(f"TCP {host}:{port} is CLOSED")
            continue

        ok(f"TCP {host}:{port} is OPEN")
        info(f"Attempting NETCONF over SSH to {host}:{port} ...")
        try:
            m = manager.connect(
                host=host,
                port=port,
                username=username,
                password=password,
                hostkey_verify=False,
                allow_agent=False,
                look_for_keys=False,
                timeout=60,
            )
            ok(f"Connected via NETCONF on port {port} to {host}")
            return m, port
        except (SessionCloseError, SSHError) as e:
            fail(f"SSH/NETCONF failed on port {port}: {e}")
        except Exception as e:
            fail(f"Unexpected error on port {port}: {e}")

    raise Exception(f"Could not connect to {host} on any NETCONF port (tried {ports}).")


def get_custom_show(m, filter_xml):
    """
    Perform a get-config on running with a user-provided subtree filter.

    Args:
        m: ncclient manager
        filter_xml (str): XML subtree filter.
    """
    reply = m.get_config(source="running", filter=("subtree", filter_xml))
    return reply.xml


def normalize_config_xml(xml_text: str) -> str:
    """
    Normalize a <config> payload so that the outer <config> element
    uses the NETCONF base namespace instead of the Tail-f namespace.

    This lets you paste output from 'show run | format netconf-xml'
    directly without manually editing the xmlns.

    - If it finds: xmlns="http://tail-f.com/ns/config/1.0"
      it replaces the FIRST occurrence with:
      xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
    """
    if not xml_text:
        return xml_text

    xml_text = xml_text.strip()

    tailf = 'xmlns="http://tail-f.com/ns/config/1.0"'
    netconf_base = 'xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"'

    if tailf in xml_text:
        xml_text = xml_text.replace(tailf, netconf_base, 1)
        info("Normalized <config> namespace from Tail-f to NETCONF base.")

    return xml_text


# ------------- Config change helpers ------------- #

def apply_candidate_changes(m, config_xml):
    """
    Apply the given <config> XML to the candidate datastore.

    Args:
        m: ncclient manager
        config_xml (str): Full <config> XML payload.

    Raises:
        RPCError / XMLError on failures.
    """
    info("Sending edit-config to candidate datastore...")
    print(f"{ICON_XML} Outgoing <config> payload:")
    print(config_xml)
    m.edit_config(target="candidate", config=config_xml, default_operation="merge")
    ok("edit-config to candidate OK")


def validate_candidate(m, has_validate):
    """
    Validate candidate datastore if :validate is supported.

    Args:
        m: ncclient manager
        has_validate (bool): Whether :validate capability is advertised.

    Raises:
        RPCError if validation fails.
    """
    if not has_validate:
        info("Device does not support :validate capability, skipping validate RPC.")
        return

    info(f"{ICON_VALIDATE} Validating candidate configuration with <validate>...")
    m.validate(source="candidate")
    ok("Candidate validation successful")


def commit_or_rollback(m):
    """
    Ask user via menu whether to commit candidate to running or roll back.

    Returns:
        str: "commit" or "rollback"
    """
    while True:
        print("\nWhat would you like to do with the candidate configuration?")
        print(f"  1) {ICON_OK} Commit candidate to running")
        print(f"  2) {ICON_FAIL} Rollback (discard-changes)")
        choice = input("Choose an option [1/2]: ").strip()
        if choice == "1":
            return "commit"
        if choice == "2":
            return "rollback"
        fail("Invalid choice. Please enter 1 or 2.")


# ------------- Main program ------------- #

def main():
    print("=== NETCONF IOS-XE Interactive Orchestrator ===\n")

    # --- Credentials ---
    info("Collecting credentials")
    username = input("Enter username: ").strip()
    password = getpass.getpass("Enter password: ")

    # --- Devices ---
    info("Collecting device IPs")
    ip_input = input("Enter IP or list of IPs (comma-separated): ").strip()
    devices = [d.strip() for d in ip_input.split(",") if d.strip()]

    if not devices:
        fail("No valid IPs entered. Exiting.")
        return

    # --- Mode: show vs changes ---
    print("\nMode options:")
    print("  1) Show data")
    print("  2) Make configuration changes")
    mode_choice = input("Do you want to 'show' data or make 'changes'? [1/2] (default: 1): ").strip()

    if mode_choice == "2":
        mode = "changes"
    else:
        mode = "show"

    show_mode = None
    show_filter_xml = None
    config_xml = None

    # --- If SHOW: ask what to show ---
    if mode == "show":
        print("\nShow options:")
        print("  1) Full running-config (get-config source=running)")
        print("  2) Custom XML subtree filter (get-config from running)")
        show_mode = input("What do you want to show? [1/2] (default: 1): ").strip()

        if show_mode not in ("1", "2"):
            show_mode = "1"

        if show_mode == "2":
            print("\nEnter your XML subtree filter for get-config (running).")
            print("Do NOT wrap it in <config> – just the filter subtree (e.g. <native ...>...).")
            print("End input with a line containing only 'END'.")
            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            show_filter_xml = "\n".join(lines).strip()

            if not show_filter_xml:
                fail("Empty filter entered; falling back to full running-config (option 1).")
                show_mode = "1"

    # --- If CHANGES: ask for XML payload ---
    if mode == "changes":
        print("\nYou selected to make configuration changes.")
        print("Please paste the full <config> XML payload to send to the candidate datastore.")
        print("You can paste output from 'show run | format netconf-xml' here.")
        print("The script will automatically normalize the <config> namespace if needed.")
        print("End input with a line containing only 'END'.")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        config_xml = "\n".join(lines).strip()

        # Basic validation: must contain "<config"
        if "<config" not in config_xml:
            fail("The XML payload does not seem to contain a <config> element.")
            info("Aborting to prevent sending invalid data.")
            return

        # Normalize Tail-f <config> to NETCONF base <config>
        config_xml = normalize_config_xml(config_xml)

        print("\n=== Normalized <config> payload that will be sent ===")
        print(config_xml)
        print("=== End normalized payload ===\n")

    # --- Iterate over each device ---
    for host in devices:
        print("\n========================================================")
        print(f"=== Working on device: {host} ===")
        print("========================================================")

        pause(f"Ready to CONNECT to {host}")

        # --- Connect ---
        try:
            m, used_port = connect_netconf(host, username, password)
        except Exception as e:
            fail(f"Connection failed for {host}: {e}")
            continue

        info(f"NETCONF session established on port {used_port} for {host}")

        # Optional keepalive
        try:
            m.session.set_keepalive(30)
            ok("Keepalive set to 30s")
        except Exception:
            info("Keepalive not supported (safe to ignore)")

        pause("Proceed to CAPABILITY CHECK")

        # --- Capabilities ---
        caps = list(m.server_capabilities)
        has_candidate = any(":candidate" in c for c in caps)
        has_validate = any(":validate" in c for c in caps)

        print(f"{ICON_CAPS} Device supports candidate datastore: {has_candidate}")
        print(f"{ICON_CAPS} Device supports validate capability : {has_validate}")

        # For SHOW, candidate not required; for CHANGES, it is.
        if mode == "changes" and not has_candidate:
            fail("Device does NOT advertise ':candidate'; cannot safely use changes mode.")
            pause("About to CLOSE session for this device (no candidate support)")
            m.close_session()
            ok(f"Session closed for {host}")
            continue

        # --- SHOW mode ---
        if mode == "show":
            pause("Proceed to SHOW operation")

            if show_mode == "1":
                # Show FULL running-config
                info(f"Retrieving full running-config from {host} ...")
                try:
                    reply = m.get_config(source="running")
                    xml = reply.xml
                    print("\n--- Full Running-Config XML ---")
                    print(xml)
                    print("--- End of XML ---")
                    ok(f"Retrieved running-config from {host}")
                except RPCError as e:
                    fail(f"Failed to retrieve running-config on {host}: {e}")

            elif show_mode == "2":
                # Custom filter
                info(f"Performing get-config (running) with custom subtree filter on {host} ...")
                try:
                    xml = get_custom_show(m, show_filter_xml)
                    print("\n--- Filtered Running-Config XML ---")
                    print(xml)
                    print("--- End of XML ---")
                    ok(f"Filtered running-config retrieved from {host}")
                except RPCError as e:
                    fail(f"get-config failed on {host}: {e}")

            pause(f"SHOW complete for {host}, about to CLOSE session")
            m.close_session()
            ok(f"Session closed for {host}")
            continue

        # --- CHANGES mode ---
        if mode == "changes":
            pause(f"Proceed to APPLY candidate changes on {host}")

            # Lock candidate
            info(f"{ICON_LOCK} Locking candidate datastore on {host}...")
            try:
                m.lock(target="candidate")
                ok("candidate locked")
            except RPCError as e:
                fail(f"Failed to lock candidate on {host}: {e}")
                pause("About to CLOSE session after lock failure")
                m.close_session()
                ok(f"Session closed for {host}")
                continue

            try:
                # Send edit-config to candidate
                pause("About to SEND edit-config to candidate")
                try:
                    apply_candidate_changes(m, config_xml)
                except (RPCError, XMLError) as e:
                    fail(f"edit-config to candidate FAILED on {host}: {e}")
                    # If edit-config failed, discard and unlock
                    pause("About to DISCARD changes due to failure")
                    try:
                        m.discard_changes()
                        ok("discard-changes OK after edit-config failure")
                    except Exception as de:
                        fail(f"discard-changes failed after edit-config failure: {de}")
                    pause("About to UNLOCK candidate after failure")
                    try:
                        m.unlock(target="candidate")
                        ok("candidate unlocked after failure")
                    except Exception as ue:
                        fail(f"Unlock candidate failed on {host}: {ue}")
                    pause("About to CLOSE session after failure")
                    m.close_session()
                    ok(f"Session closed for {host}")
                    continue

                # Validate candidate
                pause("About to VALIDATE candidate configuration")
                try:
                    validate_candidate(m, has_validate)
                except RPCError as e:
                    fail(f"Candidate validation FAILED on {host}: {e}")
                    info("Because validation failed, commit is NOT recommended.")

                    # Ask commit or rollback via menu
                    choice = commit_or_rollback(m)
                    if choice == "commit":
                        pause("About to COMMIT candidate (despite validation failure)")
                        try:
                            m.commit()
                            ok("Commit completed (WARNING: validation previously failed)")
                        except RPCError as ce:
                            fail(f"Commit FAILED on {host}: {ce}")
                    else:
                        pause("About to ROLLBACK (discard-changes) after validation failure")
                        try:
                            m.discard_changes()
                            ok("Discard-changes OK")
                        except RPCError as de:
                            fail(f"discard-changes FAILED on {host}: {de}")

                    pause("About to UNLOCK candidate after validation failure flow")
                    try:
                        m.unlock(target="candidate")
                        ok("candidate unlocked")
                    except Exception as ue:
                        fail(f"Unlock candidate failed on {host}: {ue}")

                    pause("About to CLOSE session after validation failure flow")
                    m.close_session()
                    ok(f"Session closed for {host}")
                    continue

                # If validation succeeded or was skipped, ask commit or rollback
                choice = commit_or_rollback(m)
                if choice == "commit":
                    pause("About to COMMIT candidate to running")
                    try:
                        m.commit()
                        ok("Commit OK")
                    except RPCError as e:
                        fail(f"Commit FAILED on {host}: {e}")
                else:
                    pause("About to ROLLBACK (discard-changes)")
                    try:
                        m.discard_changes()
                        ok("Discard-changes OK")
                    except RPCError as e:
                        fail(f"discard-changes FAILED on {host}: {e}")

                pause("About to UNLOCK candidate datastore")
                try:
                    m.unlock(target="candidate")
                    ok("candidate unlocked")
                except RPCError as e:
                    fail(f"Unlock candidate FAILED on {host}: {e}")

            finally:
                pause(f"All done for {host}, about to CLOSE NETCONF session")
                try:
                    m.close_session()
                    ok(f"Session closed for {host}")
                except Exception as e:
                    fail(f"Error closing session for {host}: {e}")

    print(f"\n{ICON_CLOSE} All devices processed. Exiting.")


if __name__ == "__main__":
    main()

