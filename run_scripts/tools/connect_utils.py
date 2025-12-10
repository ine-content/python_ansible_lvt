# connect_utils.py

import requests
import urllib3
from netmiko import ConnectHandler
from ncclient import manager

urllib3.disable_warnings()


# -------------------------------------------------------------
# 1) NETMIKO - RETURN CONNECTION ONLY
# -------------------------------------------------------------
def get_netmiko_connection(host, username, password, device_type="cisco_ios"):
    """
    Returns an active Netmiko SSH connection.
    Caller must run conn.disconnect().
    """
    device = {
        "device_type": device_type,
        "host": host,     # Always use 'host' for Netmiko
        "username": username,
        "password": password,
    }

    conn = ConnectHandler(**device)
    return conn


# -------------------------------------------------------------
# 2) RESTCONF - API (JSON)
# -------------------------------------------------------------
def get_restconf(host, username, password, path):
    """
    Returns raw RESTCONF response text.
    Example path: 'ietf-interfaces:interfaces'
    """
    url = f"https://{host}/restconf/data/{path}"
    headers = {"Accept": "application/yang-data+json"}

    resp = requests.get(
        url,
        auth=(username, password),
        headers=headers,
        verify=False,
        timeout=10
    )
    return resp.text


# -------------------------------------------------------------
# 3) NETCONF - RPC (XML)
# -------------------------------------------------------------
def get_netconf(host, username, password, source="running"):
    """
    Returns raw NETCONF XML for the requested datastore.
    """
    with manager.connect(
        host=host,
        username=username,
        password=password,
        hostkey_verify=False
    ) as m:
        reply = m.get_config(source=source)
        return reply.xml


# -------------------------------------------------------------
# 4) GENERIC API CALL - ANY HTTP API
# -------------------------------------------------------------
def get_api_call(url, headers=None, token=None):
    """
    Performs a raw HTTP GET request.
    For Cisco DNA Center, Meraki, Webex APIs, etc.
    """
    if token:
        headers = headers or {}
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(url, headers=headers, verify=False, timeout=10)
    return resp.text
