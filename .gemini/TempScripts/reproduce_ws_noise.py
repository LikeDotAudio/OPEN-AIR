# .gemini/TempScripts/reproduce_ws_noise.py
import os
import sys
import time

# Add project root to path
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaComProtocols.oaComWebsocket.Core.websocket_transport import WebSocketEventTransport

# Ensure we see DEBUG logs for this test
os.environ["DEBUG_MATRIX"] = "comms:websocket:DEBUG"

def test_reconnect_noise():
    transport = WebSocketEventTransport()
    params = {
        "connection_uri": "ws://localhost:9999", # Port that is hopefully closed
        "reconnect": True,
        "reconnect_interval": 1.0
    }

    print("--- Starting Connection Attempt 1 (Should see INFO and then DEBUG/WARNING) ---")
    transport.connect(params)

    print("--- Waiting for 3 seconds of background retries (Should see DEBUG logs only) ---")
    time.sleep(3.5)

    print("--- Shutting down ---")
    transport.disconnect()
    time.sleep(1)

if __name__ == "__main__":
    test_reconnect_noise()
