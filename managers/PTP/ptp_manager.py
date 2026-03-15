# managers/PTP/ptp_manager.py
# Modularized Precision Time Protocol (PTP) Monitor.
# Version 20260315.Modular.1

import threading
import time
import orjson
from scapy.all import sniff, UDP
from loguru import logger

# --- EXTRACTED CORE MODULES ---
from .core.ptp_packet_schema import PTP, SCAPY_AVAILABLE
from .core.ptp_packet_parser import PTPPacketParser
from .core.ptp_observer_registry import PTPObserverRegistry
from workers.Command_Router.mqtt.mqtt_message import MqttMessage

LOCAL_DEBUG = True

def register_ptp_callback(cb): PTPObserverRegistry.register(cb)
def unregister_ptp_callback(cb): PTPObserverRegistry.unregister(cb)

class PtpManager:
    """Manages background PTP traffic sniffing and modular data distribution."""

    def __init__(self, mqtt_connection_manager=None, subscriber_router=None):
        self.mqtt = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self.stop_event = threading.Event()
        self.sniffer_thread = None
        self.last_heartbeat = 0
        self.heartbeat_interval = 1.0

    def start(self):
        """Starts the sniffing worker and MQTT subscriptions."""
        if self.subscriber_router:
            self.subscriber_router.subscribe_to_topic("OPEN-AIR/System/PTP/Capture", self._on_external_data)
        
        if not SCAPY_AVAILABLE:
            if LOCAL_DEBUG: logger.warning("⚠️ Scapy not available. Local sniffing disabled.")
            return

        self.sniffer_thread = threading.Thread(target=self._run_sniffer, daemon=True, name="PTP_Sniffer")
        self.sniffer_thread.start()
        if LOCAL_DEBUG: logger.debug("⏱️ [PTP] Sniffer worker started.")

    def stop(self):
        self.stop_event.set()
        if self.sniffer_thread: self.sniffer_thread.join(timeout=1.0)

    def _on_external_data(self, msg: MqttMessage):
        """Bridge for PTP data received via MQTT (Core-to-UI)."""
        try:
            payload = msg.payload
            data = orjson.loads(payload) if isinstance(payload, (bytes, str)) else payload
            if isinstance(data.get("message_type"), int):
                data["message_type"] = PTPPacketParser.MSG_TYPES.get(data["message_type"], f"Unknown ({data['message_type']})")
            PTPObserverRegistry.notify(data)
        except Exception as e: logger.error(f"❌ PTP Bridge Error: {e}")

    def _run_sniffer(self):
        """Background loop for raw packet capture."""
        try:
            sniff(filter="udp port 319 or udp port 320", 
                  prn=self._process_packet, 
                  stop_filter=lambda x: self.stop_event.is_set(),
                  store=0)
        except Exception as e:
            if "Permission denied" in str(e): logger.warning("⏱️ PTP Sniffer: Permission denied (Run as root).")
            else: logger.exception("⏱️ PTP Sniffer: CRITICAL Error.")

    def _process_packet(self, pkt):
        """Dissects raw packets and distributes data."""
        if not pkt.haslayer(UDP): return
        try:
            ptp_layer = pkt[PTP] if pkt.haslayer(PTP) else PTP(bytes(pkt[UDP].payload))
            data = PTPPacketParser.tear_apart(pkt, ptp_layer)
            self._handle_heartbeat(data)
            PTPObserverRegistry.notify(data)
        except: pass

    def _handle_heartbeat(self, data):
        """Publishes activity status to MQTT at 1Hz."""
        now = time.time()
        if now - self.last_heartbeat >= self.heartbeat_interval:
            self.last_heartbeat = now
            if self.mqtt:
                payload = {"status": "alive", "last_ptp_message": data["message_type"], "timestamp": data["timestamp"]}
                self.mqtt.publish("OPEN-AIR/System/PTP/Heartbeat", orjson.dumps(payload).decode())
