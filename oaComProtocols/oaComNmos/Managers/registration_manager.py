# FolderName/FileName.py
# Author: Gemini (Collaborator)
# Version: 20260405.1315.9

import requests
import time

# Dependencies on other modules/globals passed via orchestrator
# NODE, DEVICE, SOURCES, FLOWS, SENDERS, REGISTRAR_URL, NODE_ID, DEVICE_ID will be passed as arguments.

# --- Global Connectivity Flag ---
_registrar_available = True

def post_resource(registrar_url, resource_type, resource_data, timeout=2):
    """
    Posts a resource to the NMOS registry.
    """
    global _registrar_available
    resource_url = f"{registrar_url}/resource"
    payload = {"type": resource_type, "data": resource_data}
    
    try:
        response = requests.post(resource_url, json=payload, timeout=timeout)
        if response.status_code not in (200, 201):
            print(f"[RegistrationManager] ERROR posting {resource_type}: {response.status_code} - {response.text}")
            return False
        else:
            if not _registrar_available:
                print(f"[RegistrationManager] Connectivity restored to {registrar_url}")
                _registrar_available = True
            print(f"[RegistrationManager] Successfully posted {resource_type} (ID: {resource_data.get('id', 'N/A')})")
            return True
    except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
        if _registrar_available:
            print(f"⚠️ [RegistrationManager] Registrar unreachable at {registrar_url}. NMOS Registration is suspended.")
            _registrar_available = False
        return False
    except Exception as e:
        print(f"[RegistrationManager] Unexpected error posting {resource_type}: {e}")
        return False

def register_all_resources(
    registrar_url,
    node_resource,
    device_resource,
    sources_dict,
    flows_dict,
    senders_dict,
    timeout=2
):
    """
    Registers all core NMOS resources (Node, Device, Sources, Flows, Senders)
    with the NMOS registry.

    Args:
        registrar_url (str): The base URL of the NMOS registration API.
        node_resource (dict): The NMOS Node resource payload.
        device_resource (dict): The NMOS Device resource payload.
        sources_dict (dict): Dictionary of NMOS Source resources.
        flows_dict (dict): Dictionary of NMOS Flow resources.
        senders_dict (dict): Dictionary of NMOS Sender resources.
        timeout (int): Request timeout in seconds.
    """
    print(f"[RegistrationManager] Re-registering all resources with {registrar_url}...")

    # Register Node
    post_resource(registrar_url, "node", node_resource, timeout)
    
    # Register Device
    post_resource(registrar_url, "device", device_resource, timeout)
    
    # Register Sources
    for src_id, src_data in sources_dict.items():
        post_resource(registrar_url, "source", src_data, timeout)
        
    # Register Flows
    for flow_id, flow_data in flows_dict.items():
        post_resource(registrar_url, "flow", flow_data, timeout)
        
    # Register Senders
    for sender_id, sender_data in senders_dict.items():
        post_resource(registrar_url, "sender", sender_data, timeout)
        
    print("[RegistrationManager] Finished attempting to register all resources.")
