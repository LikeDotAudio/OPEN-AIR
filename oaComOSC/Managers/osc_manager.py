# Managers/osc_manager.py
# Author: Anthony P. Kuzub (Refactored)
# Version: 20260323.1700.1
#
# Description: Dedicated orchestrator for OSC (Open Sound Control) traffic.

import threading
import time
import orjson
import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from loguru import logger
from oaLogging.Core.logger import OSC_LOGGER as logger
from oaConfiguration.FileReaders.config_reader import Config
from ..Workers.osc_rx_server import OscRxServer
from ..Workers.osc_tx_client import OscTxClient
from oaOchestration.Methods.network_utils import get_local_ip

app_constants = Config.get_instance()

class OSCManager:
    """
    Manages bidirectional OSC communication.
    Centralizes all OSC logic away from the UI.
    """

    def __init__(self, state_cache_manager=None, mqtt_connection_manager=None, 
                 run_bridge=True):
        self.run_bridge = run_bridge
        if LOCAL_DEBUG:
            logger.info(f"Initializing Bridge (Bridge={run_bridge})...")
        
        # ⚡ STANDALONE: Fallback to global singletons if not injected
        from oaComBroker.Managers.protocol_router import ProtocolRouter
        self.protocol_router = ProtocolRouter.get_instance()
        
        self.state_cache_manager = state_cache_manager
        self.mqtt_connection_manager = mqtt_connection_manager
        
        # ⚡ STANDALONE: Attempt to deduce managers if missing
        if not self.state_cache_manager:
            try:
                from oaStateCache.Core.state_cache import StateRegistry
                # ProtocolRouter might already have it
                self.state_cache_manager = getattr(self.protocol_router, "state_cache_manager", None)
            except Exception:
                pass

        if not self.mqtt_connection_manager:
            try:
                self.mqtt_connection_manager = getattr(self.protocol_router, "mqtt_manager", None)
            except Exception:
                pass

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
        
        # ⚡ THREAD SAFETY: Protect shared mutable state
        self._state_lock = threading.RLock()

        # Protocol Router Sync Logic: Listen for remote/local activity
        from oaComBroker.Managers.protocol_router import ProtocolRouter
        ProtocolRouter.get_instance().register_cache_observer(self._on_protocol_event)

    def _broadcast_status_loop(self):
        """Periodically publishes OSC bridge status to MQTT for UI sync."""
        while True:
            with self._state_lock:
                if not self._running: break
                
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
        with self._state_lock:
            return {
                "running": self._running,
                "rx_socket": self._rx_addr,
                "tx_socket": self._tx_addr,
                "routes_count": len(self.osc_to_topic),
                "bridge_mode": self.run_bridge
            }

    def add_monitor_callback(self, callback):
        with self._state_lock:
            if callback not in self._monitor_callbacks:
                self._monitor_callbacks.append(callback)

    def remove_monitor_callback(self, callback):
        with self._state_lock:
            if callback in self._monitor_callbacks:
                self._monitor_callbacks.remove(callback)

    def _notify_monitor(self, direction, address, value, topic=None):
        # Take snapshot to avoid holding lock during callback execution
        with self._state_lock:
            callbacks = list(self._monitor_callbacks)
            
        for cb in callbacks:
            try:
                cb(direction, address, value, topic)
            except Exception:
                pass

    def set_bridge_mode(self, enabled):
        """Toggles bridge mode. If transitioning to enabled while running, starts workers."""
        with self._state_lock:
            if self.run_bridge == enabled:
                return
            self.run_bridge = enabled
            running = self._running
            
        if running:
            if enabled:
                # If we were running in observer mode, now we need to start workers
                self._start_workers()
            else:
                # If we were bridging, now we stop workers but keep the manager 'running'
                self._stop_workers()
        
        logger.info(f"OSC Bridge Mode: {'ENABLED' if enabled else 'DISABLED'}")
        self._notify_monitor("STATUS_UPDATE", "BRIDGE_MODE", enabled)

    def _start_workers(self):
        """Internal helper to start RX/TX workers."""
        rx_port = getattr(app_constants, "OSC_RX_PORT", 8888)
        tx_host = getattr(app_constants, "OSC_REMOTE_IP", "127.0.0.1")
        tx_port = getattr(app_constants, "OSC_TX_PORT", 9000)

        try:
            # RX Server
            if not self.rx_server:
                self.rx_server = OscRxServer("0.0.0.0", rx_port, 
                                             self.handle_incoming_osc)
                self.rx_server.start()
                
            with self._state_lock:
                self._rx_addr = f"{get_local_ip()}:{rx_port}"
                
            if LOCAL_DEBUG:
                logger.success(f"RX SERVER ACTIVE: {self._rx_addr}")

            # TX Client
            if not self.tx_client:
                self.tx_client = OscTxClient(tx_host, tx_port)
                self.tx_client.start()
            
            with self._state_lock:
                self._tx_addr = f"{tx_host}:{tx_port}"
                
            if LOCAL_DEBUG:
                logger.success(f"TX CLIENT ACTIVE: {self._tx_addr}")

            # ⚡ STATUS MONITOR: Start periodic broadcast
            threading.Thread(target=self._broadcast_status_loop, 
                             daemon=True, name="OSC-StatusBroadcast").start()

        except Exception as e:
            logger.error(f"Bridge Workers Start Failed: {e}")

    def _stop_workers(self):
        """Internal helper to stop RX/TX workers."""
        if self.rx_server: 
            self.rx_server.stop()
            self.rx_server = None
        if self.tx_client: 
            self.tx_client.stop()
            self.tx_client = None
        
        with self._state_lock:
            self._rx_addr = "None"
            self._tx_addr = "None"
        
        logger.warning("OSC Workers Offline.")

    def start(self):
        with self._state_lock:
            if self._running: return
            self._running = True
        
        if self.run_bridge:
            self._start_workers()
        else:
            if LOCAL_DEBUG:
                logger.info("Bridge: Observer mode active.")

    def stop(self):
        with self._state_lock:
            self._running = False
            
        self._stop_workers()
        logger.warning("Bridge Offline.")

    def handle_incoming_osc(self, address, value):
        # 1. Route Map
        with self._state_lock:
            topic = self.osc_to_topic.get(address, f"OPEN-AIR/OSC{address}")
        
        # ⚡ LOGGING: High-signal Firehose style
        if LOCAL_DEBUG:
            logger.debug(f"RX: {address} -> {value} (Topic: {topic})")
        
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
            # Skip monitor topics from self-reporting to prevent recursion
            if "/Monitor/" not in address:
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
            from oaComBroker.Managers.protocol_router import ProtocolRouter
            ProtocolRouter.get_instance().ingest("OSC", topic, value, meta)
        
        self._notify_monitor("RX", address, value, topic)

    def send(self, address, value, meta=None):
        """
        Explicit publication method called by ProtocolRouter.
        Handles Internal -> External OSC Sync (OSC Out).
        """
        with self._state_lock:
            running = self._running
            
        if not running or not self.run_bridge or not self.tx_client:
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
            logger.debug(f"TX: {address} <- {value}")
        
        self.tx_client.send_message(address, value)
        
        # ⚡ BROADCAST activity back to UI monitor (as a TX event)
        # Skip monitor topics from self-reporting to prevent recursion
        if self.run_bridge and self.state_cache_manager and "/Monitor/" not in address: 
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

        from oaComBroker.Managers.protocol_router import ProtocolRouter
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
        with self._state_lock:
            if not self._running: return
        
        source = msg.get("source", "UNKNOWN").upper()
        logical_source = msg.get("logical_source", source).upper()
        topic = str(msg.get("topic", ""))
        val = msg.get("val")
        meta = msg.get("meta", {})
        
        # ⚡ LOOP PREVENTION: Never mirror our own reflection from MQTT
        if source == "MQTT" and msg.get("full_id") == app_constants.FULL_INSTANCE_ID:
            return

        # --- CASE 1: Monitor UI Update (UI Only) ---
        # Dashboard needs to see OSC events (RX or TX) and MQTT events
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
            elif logical_source == "MQTT" or source == "MQTT":
                # All MQTT elements published here as well
                self._notify_monitor("MQTT", topic, val, topic)
            return

        # --- CASE 2: Core Bridge Mirroring (Bridge Mode) ---
        # "All mqtt elements should be published here as well"
        if self.run_bridge:
            # We mirror MQTT traffic out to OSC
            if logical_source == "MQTT" or source == "MQTT":
                # EXCLUDE MONITOR TOPICS FROM MIRRORING
                if "/Monitor/" in topic:
                    return
                # Loop prevention is handled inside self.send() via metadata
                # Translate topic to OSC address
                osc_address = "/" + topic.replace("OPEN-AIR/", "")
                
                # Extract value if it's a manifest-style dict
                real_val = val
                if isinstance(val, dict) and "val" in val:
                    real_val = val["val"]
                
                self.send(osc_address, real_val, meta)
            return

    def register_route(self, osc_address: str, topic: str):
        with self._state_lock:
            self.osc_to_topic[osc_address] = topic
            self.topic_to_osc[topic] = osc_address
            
        if LOCAL_DEBUG:
            logger.info(f"Route Registered: {osc_address} <-> {topic}")
