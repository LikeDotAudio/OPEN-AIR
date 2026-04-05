# FolderName/FileName.py
# Author: Gemini (Collaborator)
# Version: 20260405.1315.7

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from oaComNmos.Core.utils import now_ts, get_ip
from oaComNmos.Core.sdp_parser import parse_sdp
from oaComNmos.Constants import settings

# --- Global State for NMOS Resources ---
# These will be managed and populated by the main orchestrator.
# They are made module-level globals here for simplicity of the handler.
NODE = {}
DEVICE = {}
SOURCES = {}
FLOWS = {}
SENDERS = {}
STREAMS = {} # Stores {hash: {"sdp": str, "sender_id": str, "last": float}}

def build_connection_active(sender_id):
    """
    Builds the NMOS Connection API 'active' payload for a given sender.

    Args:
        sender_id (str): The ID of the sender.

    Returns:
        dict or None: The active status payload or None if sender/stream not found.
    """
    sender_resource = SENDERS.get(sender_id)
    if not sender_resource:
        print(f"[ConnectionAPI] Sender not found for ID: {sender_id}")
        return None

    # Find the stream associated with this sender
    stream_data = next((s for s in STREAMS.values() if s.get("sender_id") == sender_id), None)
    if not stream_data:
        print(f"[ConnectionAPI] Stream data not found for sender ID: {sender_id}")
        return None

    sdp_content = stream_data.get("sdp")
    if not sdp_content:
        print(f"[ConnectionAPI] SDP content missing for sender ID: {sender_id}")
        return None

    parsed_sdp = parse_sdp(sdp_content)

    # Use IP from parsed SDP, fallback to host's IP if not available in SDP
    destination_ip = parsed_sdp.get("ip")
    if not destination_ip:
        print(f"[ConnectionAPI] Destination IP not found in SDP for sender {sender_id}, falling back.")
        # Fallback strategy: could use get_ip() if specific destination not in SDP,
        # but usually destination_ip is crucial for multicast.
        # For now, we'll assume it must be in SDP for valid transport params.
        # If it's truly missing, the transport params might be incomplete.
        pass 

    return {
        "activation": {
            "activation_time": now_ts(),
            "mode": None, # Auto-generated, no specific mode set here
            "requested_time": None # Not specified
        },
        "master_enable": True, # Assuming master enable is true by default
        "receiver_id": None, # No specific receiver is being targeted here
        "transport_params": [{
            "destination_port": parsed_sdp.get("port", 5004), # Default to 5004 if not in SDP
            "source_port": parsed_sdp.get("port", 5004), # Typically same as destination for multicast
            "source_ip": parsed_sdp.get("src_ip", get_ip()), # Use SDP source IP, fallback to host IP
            "destination_ip": destination_ip,
            "rtp_enabled": True
        }]
    }

class NmosConnectionApiHandler(BaseHTTPRequestHandler):
    """
    Handles incoming HTTP requests for the NMOS Connection API.
    Serves sender status and transport files.
    """
    def send_json(self, data, status_code=200):
        """Sends a JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=4).encode('utf-8'))

    def send_sdp(self, sdp_content):
        """Sends an SDP response."""
        self.send_response(200)
        self.send_header("Content-Type", "application/sdp")
        self.end_headers()
        self.wfile.write(sdp_content.encode('utf-8'))

    def do_GET(self):
        """Handles GET requests for NMOS API endpoints."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path.rstrip("/")

        # NMOS Node API Endpoints
        if path == "/x-nmos/node/v1.3":
            self.send_json(["self", "devices", "sources", "flows", "senders"])
        elif path == "/x-nmos/node/v1.3/self":
            self.send_json(NODE)
        elif path == "/x-nmos/node/v1.3/devices":
            self.send_json([DEVICE] if DEVICE else [])
        elif path == "/x-nmos/node/v1.3/sources":
            self.send_json(list(SOURCES.values()))
        elif path == "/x-nmos/node/v1.3/flows":
            self.send_json(list(FLOWS.values()))
        elif path == "/x-nmos/node/v1.3/senders":
            self.send_json(list(SENDERS.values()))

        # NMOS Connection API Endpoints
        elif path == "/x-nmos/connection/v1.1/single/senders":
            # List of sender IDs available via connection API
            self.send_json(list(SENDERS.keys()))

        elif path.startswith("/x-nmos/connection/v1.1/single/senders/"):
            sender_id = path.split('/')[-2] # Extract sender ID from path
            
            if path.endswith("/active"):
                # Get active status for a specific sender
                active_data = build_connection_active(sender_id)
                if active_data:
                    self.send_json(active_data)
                else:
                    self.send_response(404)
                    self.end_headers()
            
            elif path.endswith("/transportfile"):
                # Get the transport file (SDP) for a specific sender
                stream_data = next((s for s in STREAMS.values() if s.get("sender_id") == sender_id), None)
                if stream_data and stream_data.get("sdp"):
                    self.send_sdp(stream_data["sdp"])
                else:
                    self.send_response(404)
                    self.end_headers()
        
        # Manifest endpoints (often served by registration, but here for completeness if needed)
        # This part might be redundant if manifest_href points to registration,
        # but the original script served it.
        for stream_id, s in STREAMS.items():
            manifest_path = f"/x-manifest/senders/{s['sender_id']}/manifest"
            if path == manifest_path:
                self.send_sdp(s["sdp"])
                return

        # If no path matched
        self.send_response(404)
        self.end_headers()

def run_connection_api_server(host="0.0.0.0", port=settings.PORT):
    """Starts the NMOS Connection API HTTP server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, NmosConnectionApiHandler)
    print(f"[ConnectionAPI] Starting server on {host}:{port}...")
    try:
        httpd.serve_forever()
    except Exception as e:
        print(f"[ConnectionAPI] Server error: {e}")
    finally:
        httpd.server_close()
        print("[ConnectionAPI] Server stopped.")

