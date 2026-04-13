# Methods/network_utils.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import socket

def get_local_ip():
    """
    Finds the primary local IP address of the machine.
    Uses a UDP connection to a non-routable address to determine the outgoing interface.
    """
    network_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not actually send data
        network_socket.connect(("10.255.255.255", 1))
        IP = network_socket.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        network_socket.close()
    return IP
