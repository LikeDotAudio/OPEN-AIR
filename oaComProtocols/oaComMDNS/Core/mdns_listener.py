# oaComProtocols/oaComMDNS/Core/mdns_listener.py
# Author: Gemini (Collaborator)
# Version: 20260414.1100.1

import json  # For hashing payload
import socket

from zeroconf import ServiceBrowser, Zeroconf


class MDNSListener:
    """
    Listens for Bonjour/mDNS announcements on the local network
    and bridges them to the MQTT Hub using the StandaloneMqttPublisher.
    """
    def __init__(self, mqtt_publisher, rx_callback=None):
        self.mqtt_publisher = mqtt_publisher
        self.rx_callback = rx_callback
        self.zeroconf = None
        self.browser = None
        self.known_services = {}
        # Common media, control, NMOS, RAVENNA, Apple, and Printer services
        self.services = [
            "_http._tcp.local.",
            "_osc._udp.local.",
            "_nmos-query._tcp.local.",
            "_nmos-node._tcp.local.",
            "_apple-midi._udp.local.",
            "_companion-link._tcp.local.", # Apple TV / HomeKit
            "_ipps._tcp.local.",           # Secure Printer
            "_ipp._tcp.local.",            # Printer
            "_printer._tcp.local.",        # Generic Printer
            "_rdlink._tcp.local.",         # Apple Device Link
            "_homekit._tcp.local.",        # Apple HomeKit
            "_ravenna._tcp.local.",        # RAVENNA TCP
            "_ravenna._udp.local."         # RAVENNA UDP
        ]

    def remove_service(self, zeroconf, type, name):
        topic = f"OPEN-AIR/MDNS/Removed/{name.split('.')[0]}"
        payload = {
            "action": "removed",
            "type": type,
            "name": name,
            "origin_source": "oaComMDNS"
        }
        self.known_services.pop(name, None)
        print(f"📉 [MDNS] Removed: {name} ({type})")
        if self.rx_callback:
            # Pass name as source, and type as summary for clarity
            self.rx_callback(name, f"Removed {type}", payload)
        self.mqtt_publisher.publish(topic, payload)

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            # Prefer parsed_addresses if available (handles IPv4/IPv6 correctly)
            addresses = info.parsed_addresses() if hasattr(info, 'parsed_addresses') else []
            # Fallback for older zeroconf versions or specific cases
            if not addresses and info.addresses:
                try:
                    addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
                except Exception as e:
                    print(f"⚠️ [MDNS] Could not convert addresses for {name}: {e}")
                    addresses = [] # Ensure addresses is a list

            properties = {}
            if info.properties:
                for k, v in info.properties.items():
                    # Attempt decoding with UTF-16 as it's sometimes used for properties, fall back to UTF-8
                    try:
                        k_str = k.decode('utf-16') if isinstance(k, bytes) else str(k)
                        v_str = v.decode('utf-16', errors='ignore') if isinstance(v, bytes) else str(v)
                    except UnicodeDecodeError:
                        k_str = k.decode('utf-8') if isinstance(k, bytes) else str(k)
                        v_str = v.decode('utf-8', errors='ignore') if isinstance(v, bytes) else str(v)
                    properties[k_str] = v_str

            source_ip = addresses[0] if addresses else "Unknown"

            payload = {
                "action": "added",
                "type": type, # e.g. _http._tcp.local.
                "name": name, # e.g. MyRavennaDevice
                "server": info.server,
                "port": info.port,
                "addresses": addresses,
                "source_ip": source_ip,
                "properties": properties, # This is the TXT record payload ("package")
                "origin_source": "oaComMDNS"
            }

            payload_hash = hash(json.dumps(payload, sort_keys=True))
            if self.known_services.get(name) == payload_hash:
                return  # Skip republishing unchanged records
            self.known_services[name] = payload_hash

            # Topic differentiates by the first part of the service name (e.g., "MyRavennaDevice")
            topic = f"OPEN-AIR/MDNS/Discovered/{name.split('.')[0]}"
            print(f"📈 [MDNS] Discovered/Updated: {name} ({type}) at {addresses}:{info.port}") # Enhanced print statement
            if self.rx_callback:
                # Pass 'name' as source and 'type' as summary for better differentiation in the GUI
                self.rx_callback(name, type, payload)
            self.mqtt_publisher.publish(topic, payload)

    def update_service(self, zeroconf, type, name):
        self.add_service(zeroconf, type, name)

    def start(self):
        self.zeroconf = Zeroconf()
        self.browser = ServiceBrowser(self.zeroconf, self.services, self)
        print("🎧 [MDNS] Listener started. Browsing for services...")

    def stop(self):
        if self.zeroconf:
            self.zeroconf.close()
            print("🛑 [MDNS] Listener stopped.")
