# managers/PTP/ptp_manager.py
#
# Monitors Precision Time Protocol (PTP) traffic on the network.
#
# Primary Responsibilities:
# - Sniffing PTP packets (IEEE 1588) on UDP ports 319 and 320.
# - Parsing PTP headers to extract domain, sequence ID, and message type.
# - Distributing parsed data to registered observers and MQTT.
# - Providing a system heartbeat based on PTP traffic activity.
#
# Assumptions and Constraints:
# - Requires 'scapy' for packet sniffing and parsing.
# - Packet sniffing typically requires root/administrative privileges.
# - Optimized for Linux environments where libpcap is available.
# - Sniffing is isolated to a background thread to avoid blocking the UI.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260218.Optimization.1

import threading
import time
import orjson
import socket
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from workers.Command_Router.mqtt.mqtt_message import MqttMessage

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file

# Try to import scapy
try:
    from scapy.all import (sniff, UDP, IP, Ether, Packet, ByteField, ShortField,
                           XShortField, LongField, StrFixedLenField, BitField)
    try:
        from scapy.contrib.ptp import PTP
        SCAPY_AVAILABLE = True
    except ImportError:
        class PTP(Packet):
            """
            Defines the PTP (Precision Time Protocol) packet structure if scapy
            contrib is missing.
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
                return Packet.guess_payload_class(self, payload)
        SCAPY_AVAILABLE = True
    
    from scapy.all import bind_layers
    # Bind PTP to UDP ports 319 (event) and 320 (general)
    bind_layers(UDP, PTP, dport=319)
    bind_layers(UDP, PTP, dport=320)
    bind_layers(UDP, PTP, sport=319)
    bind_layers(UDP, PTP, sport=320)
except ImportError:
    SCAPY_AVAILABLE = False

_ptp_observers = []

def register_ptp_callback(callback_func):
    """
    Registers a callback function to receive parsed PTP packet data.

    Parameters:
    - callback_func: A callable that accepts a single dictionary argument
      containing PTP data. Must be non-NULL.

    Returns:
    - None.

    Side Effects & Thread-Safety:
    - Modifies the global `_ptp_observers` list.
    - Not explicitly thread-safe; should be called during initialization.
    """
    if callback_func not in _ptp_observers:
        _ptp_observers.append(callback_func)
        if LOCAL_DEBUG:
            logger.success("✅✅✅ [SUCCESS] PTP Monitor GUI registered.")

def unregister_ptp_callback(callback_func):
    """
    Unregisters a previously registered PTP callback function.

    Parameters:
    - callback_func: The callable to remove from the observer list.

    Returns:
    - None.

    Side Effects & Thread-Safety:
    - Modifies the global `_ptp_observers` list.
    """
    if callback_func in _ptp_observers:
        _ptp_observers.remove(callback_func)

class PtpManager:
    """
    Manages background PTP traffic sniffing and data distribution.
    """
    def __init__(self, mqtt_connection_manager=None, subscriber_router=None):
        """
        Initializes the PTP manager instance.

        Parameters:
        - mqtt_connection_manager: Optional instance for publishing heartbeats.
        - subscriber_router: Optional instance for subscribing to external data.

        Returns:
        - A new PtpManager instance.

        Side Effects & Thread-Safety:
        - Initializes threading events and internal state.
        """
        self.mqtt = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self.stop_event = threading.Event()
        self.sniffer_thread = None
        self.last_heartbeat = 0
        self.heartbeat_interval = 1.0

    def start(self):
        """
        Starts the PTP sniffing worker thread and subscribes to MQTT topics.

        Returns:
        - None.

        Side Effects & Thread-Safety:
        - Spawns a new daemon thread 'PTP_Sniffer_Worker'.
        - Registers a subscription in the `subscriber_router` if provided.
        """
        if self.subscriber_router:
            self.subscriber_router.subscribe_to_topic(
                "OPEN-AIR/System/PTP/Capture",
                self._on_external_ptp_router_data
            )
        if not SCAPY_AVAILABLE:
            return
        self.sniffer_thread = threading.Thread(
            target=self._run_sniffer,
            daemon=True,
            name="PTP_Sniffer_Worker"
        )
        self.sniffer_thread.start()
        if LOCAL_DEBUG:
            logger.debug("⏱️🕒🔗 [PTP] PTP Manager started (Isolated Worker).")

    def _on_external_ptp_router_data(self, msg: MqttMessage):
        """
        Processes PTP data received via MQTT rather than local sniffing.

        Parameters:
        - msg: An MqttMessage object containing the PTP payload.

        Returns:
        - None.

        Side Effects & Thread-Safety:
        - Invokes all registered callback functions.
        """
        try:
            payload = msg.payload
            if isinstance(payload, (bytes, str)):
                data = orjson.loads(payload)
            else:
                data = payload
                
            msg_types = {
                0: "Sync", 1: "Delay_Req", 2: "Pdelay_Req", 3: "Pdelay_Resp",
                8: "Follow_Up", 9: "Delay_Resp", 10: "Pdelay_Resp_Follow_Up",
                11: "Announce", 12: "Signaling", 13: "Management"
            }
            if isinstance(data.get("message_type"), int):
                data["message_type"] = msg_types.get(
                    data["message_type"],
                    f"Unknown ({data['message_type']})"
                )
            for cb in _ptp_observers: 
                try:
                    cb(data)
                except Exception as e:
                    # Gravity of Errors: Non-gated failure.
                    logger.error(f"⏱️🕒🔗 [PTP] ERROR: Callback failed: {e}")
        except Exception:
            # Forensic capture for external data processing failure.
            import traceback
            logger.error(f"⏱️🕒🔗 [PTP] ERROR: Failed to process PTP message."
                         f" Forensic Report:\n{traceback.format_exc()}")

    def stop(self):
        """
        Signals the sniffer thread to stop and waits for it to exit.

        Returns:
        - None.

        Side Effects & Thread-Safety:
        - Sets the `stop_event`.
        - Joins the sniffer thread with a 1-second timeout.
        """
        self.stop_event.set()
        if self.sniffer_thread:
            self.sniffer_thread.join(timeout=1.0)

    def _run_sniffer(self):
        """
        Executes the packet sniffing loop in a background thread.

        Returns:
        - None.

        Side Effects & Thread-Safety:
        - Continuous I/O operation (sniffing).
        - May fail silently if sufficient privileges are not available.
        """
        try:
            # Filters for PTP event and general messages
            sniff(filter="udp port 319 or udp port 320", 
                  prn=self._process_packet, 
                  stop_filter=lambda x: self.stop_event.is_set(),
                  store=0)
        except Exception as e:
            # Non-root users often hit permission errors here
            if "Permission denied" in str(e) or "[Errno 1]" in str(e):
                if LOCAL_DEBUG:
                    logger.debug("⏱️🕒🔗 [PTP] WARNING: Sniffer permission "
                                 "denied. Internal sniffer disabled.")
            else:
                # Gravity of Errors: Non-gated failure reporting.
                import traceback
                logger.exception(f"⏱️🕒🔗 [PTP] CRITICAL: Sniffer Error. "
                                 f"Forensic Report:\n{traceback.format_exc()}")

    def _process_packet(self, pkt):
        """
        Analyzes a single captured packet to determine if it is a PTP message.

        Parameters:
        - pkt: The scapy packet object to process.

        Returns:
        - None.

        Side Effects & Thread-Safety:
        - Invokes callbacks and heartbeat handler.
        """
        if not pkt.haslayer(UDP):
            return
        try:
            # Force PTP parsing even if layer binding failed
            ptp_layer = (pkt[PTP] if pkt.haslayer(PTP)
                         else PTP(bytes(pkt[UDP].payload)))
            
            data = self._tear_apart_ptp(pkt, ptp_layer)
            self._handle_heartbeat(data)
            for cb in _ptp_observers:
                try:
                    cb(data)
                except:
                    pass
        except:
            pass

    def _tear_apart_ptp(self, pkt, ptp):
        """
        Extracts specific PTP fields into a flattened dictionary.

        Parameters:
        - pkt: The original scapy packet.
        - ptp: The identified PTP layer.

        Returns:
        - A dictionary containing timestamp, IPs, ports, and PTP header data.

        Side Effects & Thread-Safety:
        - None (Pure function).
        """
        msg_types = {
            0: "Sync", 1: "Delay_Req", 2: "Pdelay_Req", 3: "Pdelay_Resp",
            8: "Follow_Up", 9: "Delay_Resp", 10: "Pdelay_Resp_Follow_Up",
            11: "Announce", 12: "Signaling", 13: "Management"
        }
        
        # Access scapy fields directly to avoid slow getattr() calls
        try: 
            m_id = ptp.messageType
            m_type = msg_types.get(m_id, f"Unknown ({m_id})")
        except: 
            m_type = "Unknown"
        
        try:
            domain = ptp.domainNumber
        except:
            domain = 0
        
        try:
            seq_id = ptp.sequenceId
        except:
            seq_id = 0
        
        try:
            port_id = ptp.sourcePortIdentity
        except:
            port_id = b""

        return {
            "timestamp": time.time(),
            "source_ip": pkt[IP].src if IP in pkt else "Unknown",
            "dest_ip": pkt[IP].dst if IP in pkt else "Unknown",
            "udp_port": pkt[UDP].dport,
            "message_type": m_type,
            "domain": domain,
            "sequence_id": seq_id,
            "clock_identity": self._format_clock_id(port_id),
        }

    def _format_clock_id(self, raw):
        """
        Converts raw sourcePortIdentity bytes into a readable string.

        Parameters:
        - raw: The 10-byte sourcePortIdentity field.

        Returns:
        - A formatted string containing the EUI-64 identity and port number.
        """
        if isinstance(raw, bytes):
            # The first 8 bytes are the Clock Identity (EUI-64)
            hex_part = raw[:8].hex(':') if len(raw) >= 8 else raw.hex(':')
            # The last 2 bytes are the Port Number
            port_part = int.from_bytes(raw[8:], 'big') if len(raw) > 8 else 0
            return f"{hex_part} (Port {port_part})"
        return str(raw)

    def _handle_heartbeat(self, data):
        """
        Publishes a status message to MQTT at a controlled interval.

        Parameters:
        - data: The dictionary of parsed PTP information.

        Returns:
        - None.

        Side Effects & Thread-Safety:
        - Performs network I/O via MQTT.
        - Updates the `last_heartbeat` timestamp.
        """
        now = time.time()
        # Rate limit heartbeats to 1Hz to avoid flooding MQTT
        if now - self.last_heartbeat >= self.heartbeat_interval:
            self.last_heartbeat = now
            if self.mqtt:
                status_payload = {
                    "status": "alive",
                    "last_ptp_message": data["message_type"],
                    "timestamp": data["timestamp"]
                }
                self.mqtt.publish(
                    "OPEN-AIR/System/PTP/Heartbeat",
                    orjson.dumps(status_payload).decode()
                )
