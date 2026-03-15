#!/usr/bin/env python3
"""
PTP Traffic Sniffer and MQTT Reporter.

Purpose:
    Provide a diagnostic utility for sniffing and reporting PTP (Precision Time
    Protocol) traffic to the OPEN-AIR system via MQTT.

Primary Responsibilities:
    - Sniff PTP event and general messages (UDP 319/320).
    - Parse PTP packet headers using Scapy.
    - Publish captured data to an MQTT broker for application testing.
    - Provide a standalone CLI interface for real-time traffic monitoring.

Assumptions and Constraints:
    - Requires 'scapy' and 'paho-mqtt' libraries.
    - Must be executed with root/administrative privileges for packet sniffing.
    - Assumes a functional MQTT broker if reporting is desired.
    - Designed for Linux environments.
"""

import sys
import orjson
import time
import argparse

# Allow user configuration of broker and port for varied network environments.
parser = argparse.ArgumentParser(
    description="PTP Traffic Sniffer and MQTT Reporter"
)
parser.add_argument(
    "--broker", default="localhost", 
    help="MQTT Broker address (default: localhost)"
)
parser.add_argument(
    "--port", type=int, default=1883, 
    help="MQTT Broker port (default: 1883)"
)
args = parser.parse_args()

# Initialize MQTT communication to bridge packet data to the OPEN-AIR system.
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

MQTT_BROKER = args.broker
MQTT_PORT = args.port
MQTT_TOPIC = "OPEN-AIR/System/PTP/Capture"

mqtt_client = None
if MQTT_AVAILABLE:
    try:
        # Ensure compatibility with both legacy and modern Paho MQTT versions.
        try:
            mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        except AttributeError:
            mqtt_client = mqtt.Client()
            
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"Warning: Could not connect to MQTT broker "
              f"({MQTT_BROKER}:{MQTT_PORT}): {e}")
        mqtt_client = None

try:
    from scapy.all import (sniff, UDP, IP, Packet, ByteField, ShortField,
                           XShortField, LongField, StrFixedLenField, BitField,
                           bind_layers)
    # Attempt to load specialized PTP definitions from Scapy's contribution library.
    try:
        from scapy.contrib.ptp import PTP
        HAS_PTP = True
    except ImportError:
        # Provide a fallback PTP structure if the contrib module is unavailable.
        class PTP(Packet):
            """
            Define a minimal PTP (IEEE 1588) header for Scapy packet parsing.

            This class provides the packet structure for PTP headers when the
            standard Scapy PTP contribution is unavailable.

            Side-effects:
                Registers a new Scapy packet type in the local namespace.

            Thread-safety:
                Thread-safe; class instances are immutable representations of
                packet structures.
            """
            name = "PTP"
            fields_desc = [
                BitField("transportSpecific", 0, 4),
                BitField("messageType", 0, 4),
                BitField("reserved", 0, 4),
                BitField("versionPTP", 2, 4),
                ShortField("messageLength", 34),
                ByteField("domainNumber", 0),
                ByteField("reserved1", 0),
                XShortField("flagField", 0),
                LongField("correctionField", 0),
                ByteField("reserved2", 0),
                ByteField("reserved3", 0),
                ByteField("reserved4", 0),
                ByteField("reserved5", 0),
                StrFixedLenField("sourcePortIdentity", b"\x00"*10, 10),
                ShortField("sequenceId", 0),
                ByteField("controlField", 0),
                ByteField("logMessageInterval", 0)
            ]

            def guess_payload_class(self, payload):
                """
                Determine the next layer class based on the current payload.

                Args:
                    payload (bytes): Raw payload data following the PTP header.

                Returns:
                    Packet: The packet class responsible for the next layer.

                Thread-safety:
                    Thread-safe.
                """
                return Packet.guess_payload_class(self, payload)
        HAS_PTP = True
    
    # Enable Scapy's automatic protocol identification for PTP traffic.
    bind_layers(UDP, PTP, dport=319)
    bind_layers(UDP, PTP, dport=320)
    bind_layers(UDP, PTP, sport=319)
    bind_layers(UDP, PTP, sport=320)

except ImportError:
    print("Error: Scapy not installed. Run 'pip install scapy' "
          "(might need sudo/--break-system-packages)")
    sys.exit(1)

def packet_callback(pkt):
    """
    Process captured network packets and extract PTP-specific information.

    Analyze each packet to determine if it contains PTP data. If identified,
    the PTP fields are parsed and published to the configured MQTT broker
    as a JSON payload. Non-PTP UDP traffic on monitored ports is reported
    to stdout for diagnostic purposes.

    Args:
        pkt (scapy.packet.Packet): The packet object captured by Scapy's
            sniffing engine.

    Returns:
        None.

    Side-effects:
        - Prints packet summaries and PTP details to standard output.
        - Publishes JSON data to the MQTT broker if the client is connected.

    Thread-safety:
        Not thread-safe; relies on a global MQTT client which may not handle
        concurrent publish operations safely.
    """
    ptp_layer = None
    src = "Unknown"
    dport = 0

    if pkt.haslayer(UDP):
        src = pkt[IP].src if IP in pkt else "Unknown"
        dport = pkt[UDP].dport
        
        # Determine if the packet contains a recognized PTP layer.
        if pkt.haslayer(PTP):
            ptp_layer = pkt[PTP]
        else:
            # Attempt manual parsing if automatic layer identification failed.
            try:
                payload = bytes(pkt[UDP].payload)
                if len(payload) >= 34:
                    ptp_layer = PTP(payload)
            except Exception:
                pass

    if ptp_layer:
        print(f"\n[+] Captured PTP Packet from {src} on port {dport}")
        try:
            ptp_layer.show()
        except Exception:
            print("Could not show PTP layer details.")
        
        # Relay the captured metrics to the system-wide MQTT bus.
        if mqtt_client:
            try:
                # Prioritize direct field access to minimize processing latency.
                m_type = int(ptp_layer.messageType)
                domain = int(ptp_layer.domainNumber)
                seq_id = int(ptp_layer.sequenceId)
                port_id = ptp_layer.sourcePortIdentity
                
                # Convert raw port identity to readable hex format for JSON.
                clock_id = (port_id.hex(':') if isinstance(port_id, bytes) 
                            else str(port_id))

                data = {
                    "timestamp": time.time(),
                    "source_ip": src,
                    "udp_port": dport,
                    "message_type": m_type,
                    "domain": domain,
                    "sequence_id": seq_id,
                    "clock_identity": clock_id
                }
                mqtt_client.publish(MQTT_TOPIC, orjson.dumps(data).decode())
            except Exception as e:
                print(f"Error publishing PTP data: {e}")
    elif pkt.haslayer(UDP):
        # Provide diagnostic feedback for unexpected traffic on PTP ports.
        print(f"\n[+] Captured UDP Packet from {src} on port {dport}")
        payload = bytes(pkt[UDP].payload)
        print(f"Raw Payload (Hex): {payload.hex()}")
        print(f"Raw Payload (Length): {len(payload)} bytes")

# Notify the user of the sniffer's current operational state.
print("Listening for PTP traffic (UDP 319/320)...")
print(f"Scapy PTP Layer Status: {'Available' if HAS_PTP else 'Not Available'}")
print(f"MQTT Feedback: {'Active (' + MQTT_TOPIC + ')' if mqtt_client else 'Disabled'}")
print("Note: You likely need to run this with sudo: "
      "'sudo python3 managers/PTP/PTPtester.py'")

try:
    # Execute the packet capture engine with a filter for PTP ports.
    sniff(filter="udp port 319 or udp port 320", prn=packet_callback, store=0)
except PermissionError:
    print("Error: Permission denied. Packet sniffing requires root privileges. "
          "Try 'sudo'.")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Clean up communication resources upon script termination.
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
