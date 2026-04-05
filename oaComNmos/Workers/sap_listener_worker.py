# FolderName/FileName.py
# Author: Gemini (Collaborator)
# Version: 20260405.1315.8

import socket
import struct
import time
import threading
import uuid
import json
import hashlib # Imported from utils, but good to have here if needed directly
import requests

from oaComNmos.Core.utils import gen_id, get_ip, hash_sdp, now_ts
from oaComNmos.Core.sdp_parser import parse_sdp
from oaComNmos.Core.nmos_builder import build_source, build_flow, build_sender
from oaComNmos.Managers.sender_cache_manager import find_existing_sender
from oaComNmos.Interface.connection_api import STREAMS # Access module-level global
from oaComNmos.Constants import settings

# These are global states managed by the orchestrator and passed to this worker.
# Example:
# GLOBAL_STATE = {
#     "NODE_ID": None,
#     "DEVICE_ID": None,
#     "NODE": {},
#     "DEVICE": {},
#     "SOURCES": {},
#     "FLOWS": {},
#     "SENDERS": {},
#     "STREAMS": {}, # Shared with Connection API
#     "REGISTRAR_URL": None,
#     "RUNNING": True,
# }

def extract_sdp_from_sap(data):
    """
    Extracts the SDP content from a SAP (Session Announcement Protocol) packet.
    SAP packets often preface SDP with 'application/sdp\x00'.

    Args:
        data (bytes): The raw SAP packet data.

    Returns:
        str or None: The extracted SDP content as a string, or None if not found.
    """
    marker = b"application/sdp\x00"
    idx = data.find(marker)
    if idx == -1:
        return None
    # Decode the SDP, ignoring potential errors for robustness
    return data[idx + len(marker):].decode(errors="ignore")

def register_new_stream(
    sdp_content,
    registrar_url,
    host_ip,
    node_id,
    device_id,
    SOURCES, FLOWS, SENDERS, STREAMS, # Pass mutable state dicts
    registration_manager # Object or module with post/register_all
):
    """
    Processes a new SDP stream, finding an existing sender or creating new NMOS resources.

    Args:
        sdp_content (str): The SDP content of the stream.
        registrar_url (str): The NMOS registrar URL.
        host_ip (str): The IP address of the host.
        node_id (str): The ID of the NMOS node.
        device_id (str): The ID of the NMOS device.
        SOURCES (dict): Global dict for NMOS sources.
        FLOWS (dict): Global dict for NMOS flows.
        SENDERS (dict): Global dict for NMOS senders.
        STREAMS (dict): Global dict for stream data (shared).
        registration_manager: An object/module with 'post' and 'register_all' methods.
    """
    sdp_hash = hash_sdp(sdp_content)

    # Check if this stream (by hash) is already known
    if sdp_hash in STREAMS:
        STREAMS[sdp_hash]["last"] = time.time() # Update last seen timestamp
        # print(f"[SAPListener] Stream already known, updated timestamp: {sdp_hash}")
        return

    # Try to find an existing NMOS sender that matches this SDP
    existing_sender_resource = find_existing_sender(sdp_content, registrar_url)

    if existing_sender_resource:
        sender_id = existing_sender_resource.get("id")
        print(f"[SAPListener] Found existing sender '{sender_id}' for stream.")
        STREAMS[sdp_hash] = {
            "sdp": sdp_content,
            "sender_id": sender_id,
            "last": time.time()
        }
        # No need to re-register sender if it already exists
        return

    # Create new NMOS resources if no existing sender is found
    print(f"[SAPListener] No existing sender found for stream, creating new NMOS resources.")
    
    # Generate unique IDs for new resources
    source_id = gen_id()
    flow_id = gen_id()
    sender_id = gen_id()

    # Parse SDP for building resources
    parsed_sdp_data = parse_sdp(sdp_content)

    # Build NMOS resources
    new_source = build_source(source_id, device_id, parsed_sdp_data)
    new_flow = build_flow(flow_id, source_id, device_id, parsed_sdp_data)
    new_sender = build_sender(
        sender_id,
        flow_id,
        device_id,
        parsed_sdp_data,
        host_ip,
        settings.PORT # Use the configured API port
    )

    # Update global state and register resources
    STREAMS[sdp_hash] = {
        "sdp": sdp_content,
        "sender_id": sender_id, # Link to the newly created sender
        "last": time.time()
    }
    SOURCES[source_id] = new_source
    FLOWS[flow_id] = new_flow
    SENDERS[sender_id] = new_sender

    # Update the device's sender list if this is a new sender
    if sender_id not in DEVICE.get("senders", []):
        DEVICE.get("senders", []).append(sender_id)
        DEVICE["version"] = now_ts()
        registration_manager.post(registrar_url, "device", DEVICE)

    # Register new resources with the NMOS registry
    registration_manager.post(registrar_url, "source", new_source)
    registration_manager.post(registrar_url, "flow", new_flow)
    registration_manager.post(registrar_url, "sender", new_sender)

def sap_listener_worker(registrar_url, node_id, device_id, host_ip, global_state, registration_manager):
    """
    Worker function to listen for SAP (Session Announcement Protocol) messages
    on a multicast group and register them as NMOS streams.

    Args:
        registrar_url (str): The NMOS registrar URL.
        node_id (str): The ID of the NMOS node.
        device_id (str): The ID of the NMOS device.
        host_ip (str): The IP address of the host machine.
        global_state (dict): Dictionary containing shared mutable states like
                             SOURCES, FLOWS, SENDERS, STREAMS, RUNNING.
        registration_manager: An object/module with 'post' method.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except OSError: # SO_REUSEPORT might not be available on all systems
        print("[SAPListener] SO_REUSEPORT not available, continuing without it.")

    try:
        sock.bind(("0.0.0.0", settings.SAP_PORT))
        print(f"[SAPListener] Bound to 0.0.0.0:{settings.SAP_PORT}")
    except OSError as e:
        print(f"[SAPListener] ERROR binding to port {settings.SAP_PORT}: {e}")
        return # Exit if port binding fails

    # Join the multicast group
    try:
        mreq = struct.pack("4sl", socket.inet_aton(settings.SAP_GROUP), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        print(f"[SAPListener] Joined multicast group {settings.SAP_GROUP}")
    except Exception as e:
        print(f"[SAPListener] ERROR joining multicast group {settings.SAP_GROUP}: {e}")
        # Continue, as SAP might not be strictly required or configured differently

    print(f"[SAPListener] Listening for SAP announcements on {settings.SAP_GROUP}:{settings.SAP_PORT}...")

    while global_state.get("RUNNING", True):
        try:
            # Set a timeout so the loop can check RUNNING flag periodically
            sock.settimeout(1.0) 
            data, _ = sock.recvfrom(2048)

            sdp = extract_sdp_from_sap(data)
            if sdp:
                register_new_stream(
                    sdp,
                    registrar_url,
                    host_ip,
                    node_id,
                    device_id,
                    global_state["SOURCES"],
                    global_state["FLOWS"],
                    global_state["SENDERS"],
                    global_state["STREAMS"],
                    registration_manager
                )
        except socket.timeout:
            # Timeout occurred, loop will check RUNNING flag and continue
            continue
        except Exception as e:
            print(f"[SAPListener] Error processing packet: {e}")
            # Continue listening even if one packet fails

    print("[SAPListener] Worker shutting down.")
    sock.close()


def heartbeat_worker(registrar_url, node_id, global_state, registration_manager):
    """
    Worker function that periodically sends heartbeat requests to the NMOS registrar
    to maintain the node's registration.

    Args:
        registrar_url (str): The NMOS registrar URL.
        node_id (str): The ID of the NMOS node to send heartbeats for.
        global_state (dict): Dictionary containing shared states like RUNNING.
        registration_manager: An object/module with 'register_all' method.
    """
    while global_state.get("RUNNING", True):
        try:
            health_check_url = f"{registrar_url}/health/nodes/{node_id}"
            print(f"[Heartbeat] Sending health check to {health_check_url}")
            response = requests.post(health_check_url, timeout=2)

            if response.status_code != 200:
                print(f"[Heartbeat] Health check failed ({response.status_code}) → Re-registering node.")
                registration_manager.register_all(registrar_url, global_state["NODE"], global_state["DEVICE"], global_state["SOURCES"], global_state["FLOWS"], global_state["SENDERS"])
            else:
                print("[Heartbeat] OK")
        except requests.exceptions.RequestException as e:
            print(f"[Heartbeat] Request exception ({e}) → Re-registering node.")
            registration_manager.register_all(registrar_url, global_state["NODE"], global_state["DEVICE"], global_state["SOURCES"], global_state["FLOWS"], global_state["SENDERS"])
        except Exception as e:
            print(f"[Heartbeat] Unexpected error ({e}) → Re-registering node.")
            registration_manager.register_all(registrar_url, global_state["NODE"], global_state["DEVICE"], global_state["SOURCES"], global_state["FLOWS"], global_state["SENDERS"])

        time.sleep(settings.HB_INTERVAL)
    
    print("[Heartbeat] Worker shutting down.")

