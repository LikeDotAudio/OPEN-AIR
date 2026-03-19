# workers/Command_Router/OSC/osc.py
#
# Dedicated orchestrator for OSC (Open Sound Control) traffic.
# Logic-heavy architecture for Centralized Command Hub.
#
# Author: Anthony P. Kuzub(Refactored)
# Version 20260309.Harden.3

import threading
import time
import orjson
import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from loguru import logger
from oaConfiguration.config_reader import Config
from .osc_rx_server import OscRxServer
from .osc_tx_client import OscTxClient
from oaOchestration.network_utils import get_local_ip

app_constants = Config.get_instance()
# ⚡ SUBSYSTEM: OSC_BRIDGE
osc_logger = logger.bind(category="OSC")

class OSCManager:
    """
    Manages bidirectional OSC communication.
    Centralizes all OSC logic away from the UI.
    """

    def __init__(self, state_cache_manager=None, mqtt_connection_manager=None, 
                 run_bridge=True):
        self.run_bridge = run_bridge
        if LOCAL_DEBUG:
            osc_logger.info(f"🅾️📡💻 [OSC] Initializing Bridge "
                             f"(Bridge={run_bridge})...")
        
        self.state_cache_manager = state_cache_manager
        self.mqtt_connection_manager = mqtt_connection_manager
        self._running = False

        # Routing Table
        self.osc_to_topic = {}
        self.topic_to_osc = {}

        # Workers
        self.rx_server = None
        self.tx_client = None
        
        # Socket Info for reporting
        self._rx_addr = "None"
        self._tx_addr = "None"
        
        # Monitor callbacks for GUI
        self._monitor_callbacks = []

        # Protocol Router Sync Logic: Listen for remote/local activity
        from oaComBroker.protocol_router import ProtocolRouter
        ProtocolRouter.get_instance().register_cache_observer(self._on_protocol_event)

    def _broadcast_status_loop(self):
        """Periodically publishes OSC bridge status to MQTT for UI sync."""
        while self._running:
            if self.run_bridge and self.state_cache_manager:
                status = self.get_status()
                self.state_cache_manager.handle_external_update(
                    "OPEN-AIR/System/Status/OSC/Bridge", 
                    status, 
                    source="OSC-STATUS"
                )
            time.sleep(5.0)

    def get_status(self):
        """Returns a logic-only status report for the UI."""
        return {
            "running": self._running,
            "rx_socket": self._rx_addr,
            "tx_socket": self._tx_addr,
            "routes_count": len(self.osc_to_topic),
            "bridge_mode": self.run_bridge
        }

    def add_monitor_callback(self, callback):
        self._monitor_callbacks.append(callback)

    def remove_monitor_callback(self, callback):
        if callback in self._monitor_callbacks:
            self._monitor_callbacks.remove(callback)

    def _notify_monitor(self, direction, address, value, topic=None):
        for cb in self._monitor_callbacks:
            try: cb(direction, address, value, topic)
            except: pass

    def start(self):
        if self._running: return
        self._running = True
        
        rx_port = getattr(app_constants, "OSC_RX_PORT", 8888)
        tx_host = getattr(app_constants, "OSC_REMOTE_IP", "127.0.0.1")
        tx_port = getattr(app_constants, "OSC_TX_PORT", 9000)

        if self.run_bridge:
            try:
                # RX Server
                self.rx_server = OscRxServer("0.0.0.0", rx_port, 
                                             self.handle_incoming_osc)
                self.rx_server.start()
                self._rx_addr = f"{get_local_ip()}:{rx_port}"
                if LOCAL_DEBUG:
                    osc_logger.success(f"🅾️📡✅ [OSC] RX SERVER ACTIVE: "
                                       f"{self._rx_addr}")

                # TX Client
                self.tx_client = OscTxClient(tx_host, tx_port)
                self.tx_client.start()
                self._tx_addr = f"{tx_host}:{tx_port}"
                if LOCAL_DEBUG:
                    osc_logger.success(f"🅾️📡✅ [OSC] TX CLIENT ACTIVE: "
                                       f"{self._tx_addr}")

                # ⚡ STATUS MONITOR: Start periodic broadcast
                threading.Thread(target=self._broadcast_status_loop, 
                                 daemon=True).start()

            except Exception as e:
                osc_logger.error(f"❌🚫🛑 [OSC] Bridge Start Failed: {e}")
        else:
            if LOCAL_DEBUG:
                osc_logger.info("🅾️📡💻 [OSC] Bridge: Observer mode active.")

    def stop(self):
        self._running = False
        if self.rx_server: self.rx_server.stop()
        if self.tx_client: self.tx_client.stop()
        osc_logger.warning("🅾️📡🛑 [OSC] Bridge Offline.")

    def handle_incoming_osc(self, address, value):
        # 1. Route Map
        topic = self.osc_to_topic.get(address, f"OPEN-AIR/OSC{address}")
        
        # ⚡ LOGGING: High-signal Firehose style
        if LOCAL_DEBUG:
            osc_logger.debug(f"📥📡📥 [OSC] RX: {address} -> {value} "
                             f"(Topic: {topic})")
        
        # ⚡ ANTI-FEEDBACK SPEC: Define identity at transport ingress
        meta = {
            "osc_address": address,
            "msg_type": "SPLICE_ACTION",
            "origin_source": "OSC"
        }

        # 2. Update HUB and State (Internal Sync)
        if self.state_cache_manager:
            self.state_cache_manager.handle_external_update(
                topic, 
                value, 
                source="OSC", 
                metadata=meta
            )
            
            # 3. Update Monitor Feed (UI Decoration)
            monitor_payload = {
                "val": value,
                "source": "OSC",
                "address": address,
                "direction": "RX"
            }
            # Propagate spec fields to monitor payload
            monitor_payload.update(meta)

            self.state_cache_manager.handle_external_update(
                "OPEN-AIR/System/Monitor/OSC/Activity", 
                monitor_payload, 
                source="OSC"
            )
        else:
            # Fallback if no state manager
            from oaComBroker.protocol_router import ProtocolRouter
            ProtocolRouter.get_instance().ingest("OSC", topic, value, meta)
        
        self._notify_monitor("RX", address, value, topic)

    def send(self, address, value, meta=None):
        """
        Explicit publication method called by ProtocolRouter.
        Handles Internal -> External OSC Sync (OSC Out).
        """
        if not self._running or not self.run_bridge or not self.tx_client:
            return

        meta = meta or {}
        # ⚡ ANTI-FEEDBACK SPEC: Unified Fields
        msg_type = meta.get("msg_type", "SPLICE_ACTION")
        origin_source = meta.get("origin_source", "UNKNOWN")

        # ⚡ ANTI-FEEDBACK SPEC: The Golden Rule for Transports
        if msg_type == "LINK_FEEDBACK" and not meta.get("is_settled"):
            return
        if origin_source == "OSC":
            return

        # ⚡ LOGGING
        if LOCAL_DEBUG:
            osc_logger.debug(f"📤📡📤 [OSC] TX: {address} <- {value}")
        
        self.tx_client.send_message(address, value)
        
        # ⚡ BROADCAST activity back to UI monitor (as a TX event)
        if self.run_bridge and self.state_cache_manager: 
            monitor_payload = {
                "val": value,
                "source": "OSC",
                "address": address,
                "direction": "TX",
                "ts": time.time(),
                "GUID": app_constants.INSTANCE_GUID,
                "partition": app_constants.PARTITION_ID
            }
            # ⚡ ANTI-FEEDBACK SPEC: Preserve identity in monitor log
            monitor_payload["msg_guid"] = meta.get("msg_guid")
            monitor_payload["msg_type"] = meta.get("msg_type")
            monitor_payload["origin_source"] = origin_source

            self.state_cache_manager.handle_external_update(
                "OPEN-AIR/System/Monitor/OSC/Activity",
                monitor_payload,
                source="OSC"
            )

        from oaComBroker.protocol_router import ProtocolRouter
        # Ingest the TX event back into the router for forensics
        ProtocolRouter.get_instance().ingest("OSC-TX", f"OPEN-AIR/OSC{address}", value, {
            "osc_address": address, 
            "partition": app_constants.PARTITION_ID,
            "msg_guid": meta.get("msg_guid"),
            "msg_type": msg_type,
            "origin_source": origin_source
        })

        self._notify_monitor("TX", address, value)

    def _on_protocol_event(self, msg):
        """Callback for all router traffic. Handles OSC status and monitor updates."""
        if not self._running: return
        
        source = msg.get("source", "UNKNOWN").upper()
        logical_source = msg.get("logical_source", source).upper()
        topic = str(msg.get("topic", ""))
        val = msg.get("val")
        meta = msg.get("meta", {})
        
        # --- CASE 1: Monitor UI Update (UI Only) ---
        # Dashboard needs to see OSC events (RX or TX)
        if not self.run_bridge:
            if logical_source == "OSC":
                # RX or Remote Sync Event
                direction = meta.get("direction", "RX")
                address = meta.get("address", meta.get("osc_address", topic))
                # For sync traffic via MQTT, the value might be the raw value or the monitor dict
                real_val = val.get("val") if isinstance(val, dict) and "val" in val and "address" in val else val
                self._notify_monitor(direction, address, real_val, topic)
            elif source == "OSC-TX":
                # Local TX Event from Core
                self._notify_monitor("TX", meta.get("osc_address", topic), val, topic)
            return

        # --- CASE 2: Internal -> External Sync ---
        # ⚡ DEPRECATED: Now handled by explicit send() method.
        pass

    def register_route(self, osc_address: str, topic: str):
        self.osc_to_topic[osc_address] = topic
        self.topic_to_osc[topic] = osc_address
        if LOCAL_DEBUG:
            osc_logger.info(f"🗺️📡💻 [OSC] Route Registered: "
                             f"{osc_address} <-> {topic}")
