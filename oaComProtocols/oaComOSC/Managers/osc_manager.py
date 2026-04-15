# Managers/osc_manager.py
# Author: Gemini (Collaborator)
# Version: 20260414.1900.1
#
# Description: Dedicated orchestrator for OSC (Open Sound Control) traffic.
# ⚡ REFACTORED: Now utilizes native Core OscMqttTransport.

import threading
import time
import os

# --- Standard Debug Logging Setup ---
from loguru import logger
from oaLogging.Core.logger import OSC_LOGGER as osc_logger
from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config
from oaComProtocols.oaComOSC.Workers.osc_rx_server import OscRxServer
from oaComProtocols.oaComOSC.Workers.osc_tx_client import OscTxClient
from oaComProtocols.oaComOSC.Core.osc_mqtt_transport import OscMqttTransport
from oaOchestration.Methods.network_utils import get_local_ip

app_constants = Config.get_instance()

LOCAL_DEBUG = False

class OSCManager:
    """
    Manages bidirectional OSC communication.
    Centralizes all OSC logic away from the UI.
    """

    def __init__(self, context=None, state_cache_manager=None, mqtt_connection_manager=None, 
                 run_bridge=True):
        # ⚡ ALWAYS ONLINE: OSC Bridge is now a mandatory system service.
        partition_id = os.environ.get("OPEN_AIR_PARTITION_ID", "CORE")
        
        self.context = context
        self.run_bridge = True
        if partition_id == "UI":
             matrix_log("comms", "osc", "__init__",
                        "ℹ️ OSC Bridge active in UI partition. Ensure port 8888 is available.", "INFO")

        matrix_log("comms", "osc", "__init__",
                   "Initializing Mandatory OSC Bridge...", "INFO")
        
        # ⚡ STANDALONE: Fallback to global singletons if not injected
        # from oaComBroker.Core.protocol_router.manager import ProtocolRouter
        self.protocol_router = None # ProtocolRouter.get_instance()
        
        self.state_cache_manager = state_cache_manager or (getattr(context, "state_cache_manager", None) if context else None)
        self.mqtt_connection_manager = mqtt_connection_manager or (getattr(context, "mqtt_connection_manager", None) if context else None)
        
        # ⚡ STANDALONE: Attempt to deduce managers if missing
        if not self.state_cache_manager:
            try:
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
        
        # ⚡ NATIVE CORE TRANSPORT:
        # We use a core MQTT transport for standalone mode to relay commands.
        self.mqtt_transport = OscMqttTransport()

        # ⚡ THREAD SAFETY: Protect shared mutable state
        self._state_lock = threading.RLock()

        # Protocol Router Sync Logic: Listen for remote/local activity
        try:
            self.protocol_router.register_cache_observer(self._on_protocol_event)
        except Exception:
            pass

        # ⚡ AUTO-START: OSC is a mandatory system service and must be online immediately.
        self.start()

    def _on_transport_message(self, topic, payload):
        """Unified callback from Core MQTT Transport."""
        if not self._running: return
        
        # Relay to protocol event handler
        synthetic_message = {
            "source": "MQTT",
            "logical_source": payload.get("source", "MQTT").upper() if isinstance(payload, dict) else "MQTT",
            "topic": topic,
            "value": payload.get("value") if isinstance(payload, dict) and "value" in payload else payload,
            "meta": payload.get("metadata", payload) if isinstance(payload, dict) else {}
        }
        self._on_protocol_event(synthetic_message)

    def _broadcast_status_loop(self):
        """Periodically publishes OSC bridge status to MQTT for UI sync."""
        while True:
            with self._state_lock:
                if not self._running: break
                
            status = self.get_status()
            topic = "OPEN-AIR/System/Status/OSC/Bridge"

            if self.state_cache_manager and hasattr(self.state_cache_manager, 'handle_external_update'):
                self.state_cache_manager.handle_external_update(topic, status, source="OSC-STATUS")
            elif self.mqtt_connection_manager and hasattr(self.mqtt_connection_manager, 'publish'):
                self.mqtt_connection_manager.publish(topic, status)
            elif self.mqtt_transport and self.mqtt_transport.is_connected():
                self.mqtt_transport.publish(topic, {"value": status, "source": "OSC-STATUS"})
                
            time.sleep(5.0)

    def get_status(self):
        """Returns a logic-only status report for the UI."""
        with self._state_lock:
            return {
                "running": self._running,
                "rx_socket": self._rx_addr,
                "tx_socket": self._tx_addr,
                "routes_count": len(self.osc_to_topic),
                "bridge_mode": True 
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
        with self._state_lock:
            callbacks = list(self._monitor_callbacks)
            
        for cb in callbacks:
            try:
                cb(direction, address, value, topic)
            except Exception:
                pass

    def set_bridge_mode(self, enabled):
        """DEPRECATED: OSC Bridge is now always enabled."""
        osc_logger.info("OSC Bridge Mode: ALWAYS ENABLED (Request ignored)")
        self._notify_monitor("STATUS_UPDATE", "BRIDGE_MODE", True)

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
                
            matrix_log("comms", "osc", "_start_workers", 
                       f"RX SERVER ACTIVE: {self._rx_addr}", "SUCCESS")

            # TX Client
            if not self.tx_client:
                self.tx_client = OscTxClient(tx_host, tx_port)
                self.tx_client.start()
            
            with self._state_lock:
                self._tx_addr = f"{tx_host}:{tx_port}"
                
            matrix_log("comms", "osc", "_start_workers", 
                       f"TX CLIENT ACTIVE: {self._tx_addr}", "SUCCESS")

            # ⚡ STATUS MONITOR: Start periodic broadcast
            threading.Thread(target=self._broadcast_status_loop, 
                             daemon=True, name="OSC-StatusBroadcast").start()

        except Exception as e:
            osc_logger.error(f"Bridge Workers Start Failed: {e}")

    def start(self):
        with self._state_lock:
            if self._running: return
            self._running = True
        
        self._start_workers()
        
        # ⚡ STANDALONE: Setup core MQTT transport if system manager is missing
        if not self.mqtt_connection_manager:
            self.mqtt_transport.set_message_handler(self._on_transport_message)
            connection_params = {
                "destination_host": getattr(app_constants, "MQTT_BROKER_ADDRESS", "localhost"),
                "destination_port": getattr(app_constants, "MQTT_BROKER_PORT", 1883),
                "client_id": f"OSC-CORE-{app_constants.FULL_INSTANCE_ID[:8]}"
            }
            if self.mqtt_transport.connect(connection_params):
                self.mqtt_transport.subscribe("OPEN-AIR/#")

    def stop(self):
        """Stops the OSC bridge services and core transport."""
        with self._state_lock:
            if not self._running: return
            self._running = False
            
        # Stop core transport
        if self.mqtt_transport:
            self.mqtt_transport.disconnect()

        # Terminate workers
        if self.rx_server:
            try: self.rx_server.stop()
            except: pass
            self.rx_server = None
            
        if self.tx_client:
            try: self.tx_client.stop()
            except: pass
            self.tx_client = None
            
        matrix_log("comms", "osc", "stop", "🛑 [OSC] Bridge Services Offline.", "INFO")


    def handle_incoming_osc(self, address, value):
        with self._state_lock:
            topic = self.osc_to_topic.get(address, f"OPEN-AIR/OSC{address}")
        
        matrix_log("comms", "osc", "handle_incoming_osc", 
                   f"RX: {address} -> {value} (Topic: {topic})", "DEBUG")
        
        meta = {
            "osc_address": address,
            "message_type": "SPLICE_ACTION",
            "origin_source": "OSC"
        }

        # 2. Update HUB and State
        if self.state_cache_manager:
            self.state_cache_manager.handle_external_update(topic, value, source="OSC", metadata=meta)
        else:
            try:
                self.protocol_router.ingest("OSC", topic, value, meta)
            except Exception:
                pass
        
        # 3. ⚡ CORE RELAY: Relay to core MQTT if standalone
        if self.mqtt_transport and self.mqtt_transport.is_connected():
            payload = {"value": value, "source": "OSC", "timestamp": time.time(), "meta": meta}
            self.mqtt_transport.publish(topic, payload)
        
        self._notify_monitor("RX", address, value, topic)

    def send(self, address, value, meta=None):
        """Handles Internal -> External OSC Sync (OSC Out)."""
        with self._state_lock:
            running = self._running
            
        if not running or not self.run_bridge or not self.tx_client:
            return

        meta = meta or {}
        if meta.get("message_type") == "LINK_FEEDBACK" and not meta.get("is_settled"):
            return
        if meta.get("origin_source") == "OSC":
            return

        matrix_log("comms", "osc", "send", f"TX: {address} <- {value}", "DEBUG")
        self.tx_client.send_message(address, value)
        self._notify_monitor("TX", address, value)

    def _on_protocol_event(self, message):
        with self._state_lock:
            if not self._running: return
        
        source = message.get("source", "UNKNOWN").upper()
        logical_source = message.get("logical_source", source).upper()
        topic = str(message.get("topic", ""))
        value = message.get("value")
        meta = message.get("meta", {})
        
        is_self_reflection = (source == "MQTT" and message.get("full_id") == app_constants.FULL_INSTANCE_ID)

        # Skip non-OSC system/gui traffic
        if source == "SYSTEM" or any(topic.startswith(x) for x in ["OPEN-AIR/System/", "OPEN-AIR/GUI/", "OPEN-AIR/oaGui/"]):
            if "OSC" not in topic: return # Keep status updates
            
        if "/Monitor/" in topic: return

        # Map topic to OSC address
        with self._state_lock:
            osc_address = self.topic_to_osc.get(topic)
            
        if not osc_address:
            base_topic = topic.replace("OPEN-AIR/", "").lstrip("/")
            osc_address = "/" + base_topic if base_topic.startswith("OSC/") else "/OSC/" + base_topic
            osc_address = osc_address.replace("//", "/").strip("/")
            if not osc_address.startswith("/"): osc_address = "/" + osc_address
            if osc_address in ["/OSC", "/"]: osc_address = None

        if osc_address:
            real_val = value.get("value") if isinstance(value, dict) and "value" in value else value
            origin_source = meta.get("origin_source", "UNKNOWN")
            
            should_send = (origin_source != "OSC" and not is_self_reflection) or meta.get("is_settled")
            is_valid_source = (logical_source in ["OSC", "GUI", "MQTT", "UNKNOWN"] or source in ["OSC", "OSC-TX", "MQTT"])
            
            if should_send and self.run_bridge and is_valid_source:
                if isinstance(real_val, (int, float, str, bool, list)):
                    self.send(osc_address, real_val, meta)
        
        # Monitor Updates
        if logical_source == "OSC":
            self._notify_monitor(meta.get("direction", "RX"), meta.get("osc_address", topic), 
                                 value.get("value") if isinstance(value, dict) and "value" in value else value, topic)
        elif source in ["OSC-TX", "MQTT"]:
            self._notify_monitor(source.replace("-TX", ""), meta.get("osc_address", topic), value, topic)
        
        return

    def register_route(self, osc_address: str, topic: str):
        with self._state_lock:
            self.osc_to_topic[osc_address] = topic
            self.topic_to_osc[topic] = osc_address
            
        matrix_log("comms", "osc", "register_route", 
                   f"Route Registered: {osc_address} <-> {topic}", "INFO")
