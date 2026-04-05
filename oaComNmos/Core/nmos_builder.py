# FolderName/FileName.py
# Author: Gemini (Collaborator)
# Version: 20260405.1315.5

from oaComNmos.Core.utils import gen_id, now_ts, get_ip
from oaComNmos.Core.sdp_parser import parse_sdp
from oaComNmos.Constants import settings

def build_node(node_id, host_ip, port):
    """
    Builds the NMOS Node resource payload.

    Args:
        node_id (str): The unique identifier for the node.
        host_ip (str): The IP address of the host machine.
        port (int): The port the NMOS API is listening on.

    Returns:
        dict: The NMOS Node resource payload.
    """
    return {
        "id": node_id,
        "version": now_ts(),
        "label": "SAP-2-NMOS",
        "description": "SAP Auto-discovered Node",
        "tags": {},
        "href": f"http://{host_ip}:{port}/x-nmos/node/v1.3/",
        "hostname": "sap-auto",
        "api": {
            "versions": ["v1.3"],
            "endpoints": [{
                "host": host_ip,
                "port": port,
                "protocol": "http"
            }]
        },
        "caps": {},
        "services": [],
        "clocks": [{"name": "clk0", "ref_type": "internal"}],
        "interfaces": [{
            "name": "eth0",
            "chassis_id": "00-00-00-00-00-00",
            "port_id": "00-00-00-00-00-00"
        }]
    }

def build_device(device_id, node_id, host_ip, port):
    """
    Builds the NMOS Device resource payload.

    Args:
        device_id (str): The unique identifier for the device.
        node_id (str): The ID of the node this device belongs to.
        host_ip (str): The IP address of the host machine.
        port (int): The port the NMOS API is listening on.

    Returns:
        dict: The NMOS Device resource payload.
    """
    return {
        "id": device_id,
        "version": now_ts(),
        "label": "SAP-2-NMOS",
        "description": "Auto-discovered device",
        "tags": {},
        "type": "urn:x-nmos:device:generic",
        "node_id": node_id,
        "senders": [],
        "receivers": [],
        "controls": [{
            "href": f"http://{host_ip}:{port}/x-nmos/connection/v1.1/",
            "type": "urn:x-nmos:control:sr-ctrl/v1.1"
        }]
    }

def build_source(source_id, device_id, sdp_data):
    """
    Builds the NMOS Source resource payload from parsed SDP data.

    Args:
        source_id (str): The unique identifier for the source.
        device_id (str): The ID of the device this source belongs to.
        sdp_data (dict): Parsed SDP data from oaComNmos.Core.sdp_parser.parse_sdp.

    Returns:
        dict: The NMOS Source resource payload.
    """
    name = sdp_data.get("name", f"SAP Source {source_id[:4]}")
    ch = sdp_data.get("ch", 2) # Default to 2 channels if not specified

    return {
        "id": source_id,
        "version": now_ts(),
        "label": name,
        "description": "SAP discovered source",
        "tags": {},
        "device_id": device_id,
        "format": "urn:x-nmos:format:audio",
        "grain_rate": {"numerator": 25, "denominator": 1}, # Assuming a common grain rate
        "clock_name": "clk0", # Default clock
        "channels": [{"label": f"Ch{i}"} for i in range(ch)],
        "parents": [],
        "caps": {}
    }

def build_flow(flow_id, source_id, device_id, sdp_data):
    """
    Builds the NMOS Flow resource payload from parsed SDP data.

    Args:
        flow_id (str): The unique identifier for the flow.
        source_id (str): The ID of the source this flow belongs to.
        device_id (str): The ID of the device this flow belongs to.
        sdp_data (dict): Parsed SDP data from oaComNmos.Core.sdp_parser.parse_sdp.

    Returns:
        dict: The NMOS Flow resource payload.
    """
    name = sdp_data.get("name", f"SAP Flow {flow_id[:4]}")
    bit_depth = sdp_data.get("bit", 24)
    sample_rate_num = sdp_data.get("rate", 48000)

    return {
        "id": flow_id,
        "version": now_ts(),
        "label": name,
        "description": "SAP flow",
        "tags": {},
        "device_id": device_id,
        "source_id": source_id,
        "format": "urn:x-nmos:format:audio",
        "media_type": "audio/L24", # Assuming L24 based on common SDPs
        "bit_depth": bit_depth,
        "grain_rate": {"numerator": 25, "denominator": 1}, # Assuming a common grain rate
        "sample_rate": {"numerator": sample_rate_num, "denominator": 1},
        "parents": []
    }

def build_sender(sender_id, flow_id, device_id, sdp_data, host_ip, port):
    """
    Builds the NMOS Sender resource payload.

    Args:
        sender_id (str): The unique identifier for the sender.
        flow_id (str): The ID of the flow this sender represents.
        device_id (str): The ID of the device this sender belongs to.
        sdp_data (dict): Parsed SDP data from oaComNmos.Core.sdp_parser.parse_sdp.
        host_ip (str): The IP address of the host machine.
        port (int): The port the NMOS API is listening on.

    Returns:
        dict: The NMOS Sender resource payload.
    """
    name = sdp_data.get("name", f"SAP Sender {sender_id[:4]}")

    return {
        "id": sender_id,
        "version": now_ts(),
        "label": name,
        "description": "SAP sender",
        "tags": {},
        "device_id": device_id,
        "flow_id": flow_id,
        "transport": "urn:x-nmos:transport:rtp.mcast",
        "manifest_href": f"http://{host_ip}:{port}/x-manifest/senders/{sender_id}/manifest",
        "interface_bindings": ["eth0"], # Default interface binding
        "subscription": {"active": True, "receiver_id": None}
    }
