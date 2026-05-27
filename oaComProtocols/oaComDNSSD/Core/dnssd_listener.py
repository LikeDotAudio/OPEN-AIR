# oaComProtocols/oaComDNSSD/Core/dnssd_listener.py
# Author: Gemini (Collaborator)
# Version: 20260414.1200.1

import json  # For hashing payload
import socket

from zeroconf import ServiceBrowser, Zeroconf


class ServiceTypeListener:
    """
    Listens for service *types* being advertised via DNSSD's meta-service.
    Tells the main listener to start browsing for discovered types.
    """
    def __init__(self, listener):
        self.listener = listener

    def remove_service(self, zeroconf, type, name):
        # A service type is no longer advertised
        # For simplicity, we won't stop browsing for it, but one could add that logic here.
        print(f"🕵️ [DNSSD] Service type no longer advertised: {name}")

    def add_service(self, zeroconf, type, name):
        # `name` is the new service type found, e.g., "_googlecast._tcp.local."
        self.listener.add_service_type_to_browse(name)

    def update_service(self, zeroconf, type, name):
        # Not typically called for service type browsing
        pass

class DNSSDListener:
    """
    Listens for Bonjour/DNSSD announcements on the local network
    and bridges them to the MQTT Hub using the StandaloneMqttPublisher.
    """
    def __init__(self, mqtt_publisher, rx_callback=None):
        self.mqtt_publisher = mqtt_publisher
        self.rx_callback = rx_callback
        self.zeroconf = None
        self.known_services = {}
        self.browsers = [] # Holds all our service browsers
        self.services_being_browsed = set() # Tracks types we are already browsing

    def add_service_type_to_browse(self, type_):
        """Adds a new service type to the list of browsed services."""
        if type_ in self.services_being_browsed:
            return

        print(f"🕵️ [DNSSD] New service type found: {type_}. Adding to browser.")
        self.services_being_browsed.add(type_)
        browser = ServiceBrowser(self.zeroconf, type_, self)
        self.browsers.append(browser)

    def _create_topic(self, action, type, name):
        """Creates a hierarchical MQTT topic from the service type and name."""
        # type: _googlecast._tcp.local. -> googlecast/tcp/local
        type_path = type.strip('._').replace('._', '/').replace('.', '/')
        # name: My Device._googlecast._tcp.local. -> My_Device
        name_sanitized = name.replace(f".{type}", "").replace(" ", "_")
        return f"OpenAir/DNSSD/{action}/{type_path}/{name_sanitized}"

    def remove_service(self, zeroconf, type, name):
        topic = self._create_topic("Removed", type, name)
        payload = {
            "action": "removed",
            "type": type,
            "name": name,
            "origin_source": "oaComDNSSD"
        }
        self.known_services.pop(name, None)
        print(f"📉 [DNSSD] Removed: {name} ({type})")
        if self.rx_callback:
            # Pass name as source, and type as summary for clarity
            self.rx_callback(name, f"Removed {type}", payload)
        self.mqtt_publisher.publish(topic, payload)

    def add_service(self, zeroconf, type, name):
        # This is now only called for service *instances*, so this call is correct.
        info = zeroconf.get_service_info(type, name)
        if info:
            # Prefer parsed_addresses if available (handles IPv4/IPv6 correctly)
            addresses = info.parsed_addresses() if hasattr(info, 'parsed_addresses') else []
            # Fallback for older zeroconf versions or specific cases
            if not addresses and info.addresses:
                try:
                    addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
                except Exception as e:
                    print(f"⚠️ [DNSSD] Could not convert addresses for {name}: {e}")
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
                "origin_source": "oaComDNSSD"
            }

            payload_hash = hash(json.dumps(payload, sort_keys=True))
            if self.known_services.get(name) == payload_hash:
                return  # Skip republishing unchanged records
            self.known_services[name] = payload_hash

            topic = self._create_topic("Discovered", type, name)
            print(f"📈 [DNSSD] Discovered/Updated: {name} ({type}) at {addresses}:{info.port}") # Enhanced print statement
            if self.rx_callback:
                # Pass 'name' as source and 'type' as summary for better differentiation in the GUI
                self.rx_callback(name, type, payload)
            self.mqtt_publisher.publish(topic, payload)

    def update_service(self, zeroconf, type, name):
        self.add_service(zeroconf, type, name)

    def start(self):
        self.zeroconf = Zeroconf()
        # Start browsing for service *types*
        type_listener = ServiceTypeListener(self)
        type_browser = ServiceBrowser(self.zeroconf, "_services._dns-sd._udp.local.", type_listener)
        self.browsers.append(type_browser)
        print("🎧 [DNSSD] Listener started. Browsing for service types...")

    def stop(self):
        if self.zeroconf:
            self.zeroconf.close() # This closes all associated browsers
            print("🛑 [DNSSD] Listener stopped.")
