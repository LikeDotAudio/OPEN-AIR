# FolderName/FileName.py
# Author: Gemini (Collaborator)
# Version: 20260405.1315.3

import hashlib
import socket
import time
import uuid


def gen_id():
    """Generates a universally unique identifier."""
    return str(uuid.uuid4())

def now_ts():
    """Returns the current timestamp in seconds and nanoseconds."""
    ns = int(time.time_ns())
    return f"{ns // 1_000_000_000}:{ns % 1_000_000_000}"

def get_ip():
    """
    Retrieves the primary IP address of the local machine by attempting to connect
    to an external server (e.g., 8.8.8.8). This is a common technique to discover
    the IP address used for outgoing connections.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to an external server to discover the local IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"[Utils] Error getting local IP: {e}")
        return "127.0.0.1" # Fallback to localhost if unable to determine IP

def hash_sdp(s):
    """
    Computes the SHA-256 hash of a given string, typically used for SDP content.
    """
    return hashlib.sha256(s.encode()).hexdigest()
