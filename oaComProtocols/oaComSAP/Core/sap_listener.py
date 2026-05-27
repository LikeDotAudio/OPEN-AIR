# oaComProtocols/oaComSAP/Core/sap_listener.py
# Author: Gemini (Collaborator)
# Version: 20260414.1010.1

import socket
import struct
import threading
import time


class SAPListener:
    """
    Listens for Session Announcement Protocol (SAP) streams on 239.255.255.255:9875
    and bridges them to the MQTT Hub using the StandaloneMqttPublisher.
    """
    def __init__(self, mqtt_publisher, mcast_grp='239.255.255.255', mcast_port=9875, rx_callback=None):
        self.mqtt_publisher = mqtt_publisher
        self.mcast_grp = mcast_grp
        self.mcast_port = mcast_port
        self.rx_callback = rx_callback
        self.running = False
        self.thread = None
        self.sock = None
        self.known_streams = {}

    def start(self):
        if self.running:
            return
        self.running = True

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                pass

        # Bind to 0.0.0.0 for broader multicast reception on Linux
        self.sock.bind(('0.0.0.0', self.mcast_port))

        # Determine the host IP for multicast registration if needed, or INADDR_ANY
        mreq = struct.pack("4sl", socket.inet_aton(self.mcast_grp), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print(f"🎧 [SAP] Listener started on {self.mcast_grp}:{self.mcast_port}")

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                self._parse_sap_packet(data, addr)
            except Exception as e:
                if self.running:
                    print(f"🛑 [SAP] Receive error: {e}")
                time.sleep(1)

    def _parse_sap_packet(self, data, addr):
        # Look for the standard SDP start marker "v=0"
        sdp_start = data.find(b"v=0")
        if sdp_start == -1:
            # Not a standard SDP payload or we missed it. Let's dump a debug if it's new.
            try:
                raw_text = data.decode('ascii', errors='ignore')
                print(f"⚠️ [SAP] Non-SDP packet from {addr[0]}: {raw_text[:50]}...")
            except:
                pass
            return

        try:
            sdp_payload = data[sdp_start:].decode('utf-8', errors='ignore')

            session_name = "Unknown_SAP_Stream"
            for line in sdp_payload.split('\n'):
                line = line.strip()
                if line.startswith('s='):
                    session_name = line[2:].strip()
                    break

            payload = {
                "source_ip": addr[0],
                "session_name": session_name,
                "sdp": sdp_payload,
                "origin_source": "oaComSAP"
            }

            import json
            payload_hash = hash(json.dumps(payload, sort_keys=True))
            if self.known_streams.get(session_name) == payload_hash:
                return # Skip republishing unchanged records
            self.known_streams[session_name] = payload_hash

            # Clean IP address for MQTT Topic path
            safe_ip = addr[0].replace('.', '_')
            topic = f"OpenAir/SAP/Discovered/{safe_ip}"

            print(f"📈 [SAP] Discovered/Updated: {session_name} from {addr[0]}")

            if self.rx_callback:
                self.rx_callback(addr[0], f"Stream: {session_name}", payload)

            self.mqtt_publisher.publish(topic, payload)
        except Exception as e:
            print(f"⚠️ [SAP] Parsing error: {e}")

    def stop(self):
        self.running = False
        if self.sock:
            try:
                mreq = struct.pack("4sl", socket.inet_aton(self.mcast_grp), socket.INADDR_ANY)
                self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)
            except:
                pass
            self.sock.close()
        if self.thread:
            self.thread.join(timeout=2)
        print("🛑 [SAP] Listener stopped.")
