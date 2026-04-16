# Methods/PTPtester.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2255.1
#
# Description: !/usr/bin/env python3

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
import os
import inspect
import orjson
import time
import argparse
import importlib.util
from pathlib import Path

# --- Project Path Setup ---
current_dir = Path(__file__).parent.absolute()
project_root = current_dir
while project_root.parent != project_root:
    if (project_root / "GEMINI.md").exists():
        break
    project_root = project_root.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oaLogging.Methods.matrix_gate import matrix_log

def packet_callback(pkt, PTP, mqtt_client, MQTT_TOPIC):
    """
    Process captured network packets and extract PTP-specific information.
    """
    from scapy.all import UDP, IP
    ptp_layer = None
    source = "Unknown"
    dport = 0

    if pkt.haslayer(UDP):
        source = pkt[IP].src if IP in pkt else "Unknown"
        dport = pkt[UDP].dport
        
        # Determine if the packet contains a recognized PTP layer.
        if pkt.haslayer(PTP):
            ptp_layer = pkt[PTP]
        else:
            # Attempt manual parsing if automatic layer identification failed.
            payload = bytes(pkt[UDP].payload)
            if len(payload) >= 34:
                ptp_layer = PTP(payload)

    if ptp_layer:
        matrix_log("CORE", "PTP", inspect.currentframe().f_code.co_name, f"\n[+] Captured PTP Packet from {source} on port {dport}", level="INFO")
        ptp_layer.show()
        
        # Relay the captured metrics to the system-wide MQTT bus.
        if mqtt_client:
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
                "source_ip": source,
                "udp_port": dport,
                "message_type": m_type,
                "domain": domain,
                "sequence_id": seq_id,
                "clock_identity": clock_id
            }
            mqtt_client.publish(MQTT_TOPIC, orjson.dumps(data).decode())
    elif pkt.haslayer(UDP):
        # Provide diagnostic feedback for unexpected traffic on PTP ports.
        matrix_log("CORE", "PTP", inspect.currentframe().f_code.co_name, f"\n[+] Captured UDP Packet from {source} on port {dport}", level="INFO")
        payload = bytes(pkt[UDP].payload)
        matrix_log("CORE", "PTP", inspect.currentframe().f_code.co_name, f"Raw Payload (Hex): {payload.hex()}", level="INFO")
        matrix_log("CORE", "PTP", inspect.currentframe().f_code.co_name, f"Raw Payload (Length): {len(payload)} bytes", level="INFO")

def main():
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

    # ⚡ PRIVILEGE VALIDATION: Root check
    if os.geteuid() != 0:
        matrix_log("CORE", "PTP", "main", "Error: Permission denied. Packet sniffing requires root privileges. "
              "Try 'sudo python3 oaPTP/Methods/PTPtester.py'", level="INFO")
        sys.exit(1)

    # Initialize MQTT communication to bridge packet data to the OPEN-AIR system.
    MQTT_AVAILABLE = importlib.util.find_spec("paho.mqtt") is not None

    MQTT_BROKER = args.broker
    MQTT_PORT = args.port
    MQTT_TOPIC = "OPEN-AIR/System/PTP/Capture"

    mqtt_client = None
    if MQTT_AVAILABLE:
        import paho.mqtt.client as mqtt
        # Ensure compatibility with both legacy and modern Paho MQTT versions.
        if hasattr(mqtt, "CallbackAPIVersion"):
            mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        else:
            mqtt_client = mqtt.Client()
            
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()

    # ⚡ DEPENDENCY RESOLUTION: Scapy check
    SCAPY_SPEC = importlib.util.find_spec("scapy")
    if SCAPY_SPEC is None:
        matrix_log("CORE", "PTP", "main", "Error: Scapy not installed. Run 'pip install scapy' ", level="INFO")
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
        sys.exit(1)

    from scapy.all import (sniff, UDP, Packet, ByteField, ShortField,
                            XShortField, LongField, StrFixedLenField, BitField,
                            bind_layers)

    # Attempt to load specialized PTP definitions from Scapy's contribution library.
    PTP_SPEC = importlib.util.find_spec("scapy.contrib.ptp")
    if PTP_SPEC:
        from scapy.contrib.ptp import PTP
        HAS_PTP = True
    else:
        # Provide a fallback PTP structure if the contrib module is unavailable.
        class PTP(Packet):
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
                return Packet.guess_payload_class(self, payload)
        HAS_PTP = True

    # Enable Scapy's automatic protocol identification for PTP traffic.
    bind_layers(UDP, PTP, dport=319)
    bind_layers(UDP, PTP, dport=320)
    bind_layers(UDP, PTP, sport=319)
    bind_layers(UDP, PTP, sport=320)

    # Notify the user of the sniffer's current operational state.
    matrix_log("CORE", "PTP", "main", "Listening for PTP traffic (UDP 319/320)...", level="INFO")
    matrix_log("CORE", "PTP", "main", f"Scapy PTP Layer Status: {'Available' if HAS_PTP else 'Not Available'}", level="INFO")
    
    mqtt_status = f"Active ({MQTT_TOPIC})" if mqtt_client else "Disabled"
    matrix_log("CORE", "PTP", "main", f"MQTT Feedback: {mqtt_status}", level="INFO")

    # Execute the packet capture engine with a filter for PTP ports.
    try:
        sniff(filter="udp port 319 or udp port 320", 
              prn=lambda pkt: packet_callback(pkt, PTP, mqtt_client, MQTT_TOPIC), 
              store=0)
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up communication resources upon script termination.
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()

if __name__ == "__main__":
    main()
