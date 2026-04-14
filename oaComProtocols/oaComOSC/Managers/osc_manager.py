# Managers/osc_manager.py
# Author: Anthony P. Kuzub (Refactored)
# Version: 20260330.1600.1
#
# Description: Dedicated orchestrator for OSC (Open Sound Control) traffic.

import threading
import time
import orjson
import os

# --- Standard Debug Logging Setup ---
from loguru import logger
from oaLogging.Core.logger import OSC_LOGGER as osc_logger
from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config
from oaComProtocols.oaComOSC.Workers.osc_rx_server import OscRxServer
from oaComProtocols.oaComOSC.Workers.osc_tx_client import OscTxClient
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
        # We ignore the run_bridge parameter and force it to True where safe.
        partition_id = os.environ.get("OPEN_AIR_PARTITION_ID", "CORE")
        
        self.context = context
        self.run_bridge = True
        if partition_id == "UI":
             matrix_log("comms", "osc", "__init__",
                        "ℹ️ OSC Bridge active in UI partition. Ensure port 8888 is available.", "INFO")

        matrix_log("comms", "osc", "__init__",
                   "Initializing Mandatory OSC Bridge...", "INFO")
        # ⚡ STANDALONE: Fallback to global singletons if not injected
        from oaComBroker.Core.protocol_router.manager import ProtocolRouter
        self.protocol_router = ProtocolRouter.get_instance()
        
        self.state_cache_manager = state_cache_manager or (context.state_cache_manager if context else None)
        self.mqtt_connection_manager = mqtt_connection_manager or (context.mqtt_connection_manager if context else None)
        
        # ⚡ STANDALONE: Attempt to deduce managers if missing
        if not self.state_cache_manager:
            try:
                from oaStateCache.Core.state_cache import StateRegistry
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
        
        # ⚡ STANDALONE MQTT TRANSPORT:
        # We use an internal MQTT client for standalone mode to relay commands.
        self._internal_mqtt = None
        self._internal_mqtt_connected = False

        # ⚡ THREAD SAFETY: Protect shared mutable state
        self._state_lock = threading.RLock()

        # Protocol Router Sync Logic: Listen for remote/local activity
        try:
            from oaComBroker.Core.protocol_router.manager import ProtocolRouter
            ProtocolRouter.get_instance().register_cache_observer(self._on_protocol_event)
        except Exception:
            pass

        # ⚡ AUTO-START: OSC is a mandatory system service and must be online immediately.
        self.start()

    def _setup_internal_mqtt(self):
        """
        Initializes a private MQTT client for the OSC module.
        Used primarily in standalone mode to relay commands from the MQTT fabric.
        """
        try:
            import paho.mqtt.client as mqtt
            from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage
            
            client_id = f"OSC-STANDALONE-{int(time.time())}"
            
            # ⚡ VERSION GUARD: Support both Paho v1.x and v2.x
            if hasattr(mqtt, 'CallbackVersion'):
                self._internal_mqtt = mqtt.Client(callback_api_version=mqtt.CallbackVersion.VERSION2, client_id=client_id)
            else:
                self._internal_mqtt = mqtt.Client(client_id=client_id)
            
            def on_connect(client, userdata, flags, rc, properties=None):
                # Handle both v1 and v2 callback signatures
                # In v1, rc is passed directly. In v2, it's properties.
                # rc == 0 means success
                if rc == 0:
                    self._internal_mqtt_connected = True
                    matrix_log("comms", "osc", "mqtt_connect", "✅ [OSC] Internal MQTT Connected.", "SUCCESS")
                    client.subscribe("OPEN-AIR/#")
                else:
                    matrix_log("comms", "osc", "mqtt_connect", f"❌ [OSC] Internal MQTT Connection Failed: {rc}", "ERROR")

            def on_message(client, userdata, msg):
                # Relay to internal handler
                try:
                    message = MqttMessage(topic=msg.topic, payload=msg.payload, qos=msg.qos, retain=msg.retain)
                    self._handle_mqtt_activity(message)
                except Exception as e:
                    logger.error(f"[OSC] MQTT Internal handling failure: {e}")

            self._internal_mqtt.on_connect = on_connect
            self._internal_mqtt.on_message = on_message
            
            # Use background thread for MQTT loop
            host = getattr(app_constants, "MQTT_BROKER_HOST", "localhost")
            port = getattr(app_constants, "MQTT_BROKER_PORT", 1883)
            
            self._internal_mqtt.connect_async(host, port, 60)
            self._internal_mqtt.loop_start()
            
        except Exception as e:
            matrix_log("comms", "osc", "mqtt_init", f"⚠️ [OSC] Internal MQTT initialization failed: {e}", "WARNING")

    def _handle_mqtt_activity(self, message):
        """Standardizes MQTT activity for the protocol event handler."""
        if not self._running: return
        
        topic = message.topic
        payload = message.get_json_payload()
        
        # Determine logical source from payload if present
        source = "MQTT"
        value = payload
        meta = {}
        
        if isinstance(payload, dict):
            source = payload.get("source", "MQTT").upper()
            value = payload.get("value") if "value" in payload else payload
            meta = payload.get("metadata", payload)

        synthetic_message = {
            "source": "MQTT",
            "logical_source": source,
            "topic": topic,
            "value": value,
            "meta": meta
        }
        self._on_protocol_event(synthetic_message)

    def _broadcast_status_loop(self):
        """Periodically publishes OSC bridge status to MQTT for UI sync."""
        while True:
            with self._state_lock:
                if not self._running: break
                
            if self.state_cache_manager and hasattr(self.state_cache_manager, 'handle_external_update'):
                status = self.get_status()
                self.state_cache_manager.handle_external_update(
                    "OPEN-AIR/System/Status/OSC/Bridge", 
                    status, 
                    source="OSC-STATUS"
                )
            elif self.mqtt_connection_manager and hasattr(self.mqtt_connection_manager, 'publish'):
                status = self.get_status()
                self.mqtt_connection_manager.publish("OPEN-AIR/System/Status/OSC/Bridge", status)
                
            time.sleep(5.0)

    def get_status(self):
        """Returns a logic-only status report for the UI."""
        with self._state_lock:
            return {
                "running": self._running,
                "rx_socket": self._rx_addr,
                "tx_socket": self._tx_addr,
                "routes_count": len(self.osc_to_topic),
                "bridge_mode": True # Always True now
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

    def _stop_workers(self):
        """DEPRECATED: OSC Bridge is now always online."""
        osc_logger.warning("OSC Workers Stop Request Ignored: Always Online.")

    def start(self):
        with self._state_lock:
            if self._running: return
            self._running = True
        
        self._start_workers()
        
        # ⚡ STANDALONE: If we don't have a context or managers, we act as a standalone bridge
        if not self.mqtt_connection_manager:
            self._setup_internal_mqtt()

    def stop(self):
        """Stops the OSC bridge services and internal MQTT."""
        with self._state_lock:
            if not self._running: return
            self._running = False
            
        # Stop internal MQTT if active
        if self._internal_mqtt:
            try:
                self._internal_mqtt.loop_stop()
                self._internal_mqtt.disconnect()
                matrix_log("comms", "osc", "stop", "🛑 [OSC] Internal MQTT Disconnected.", "INFO")
            except Exception: pass
            self._internal_mqtt = None

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
        # 1. Route Map
        with self._state_lock:
            topic = self.osc_to_topic.get(address, f"OPEN-AIR/OSC{address}")
        
        matrix_log("comms", "osc", "handle_incoming_osc", 
                   f"RX: {address} -> {value} (Topic: {topic})", "DEBUG")
        
        # ⚡ ANTI-FEEDBACK SPEC: Define identity at transport ingress
        meta = {
            "osc_address": address,
            "message_type": "SPLICE_ACTION",
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
        else:
            try:
                from oaComBroker.Core.protocol_router.manager import ProtocolRouter
                ProtocolRouter.get_instance().ingest("OSC", topic, value, meta)
            except Exception:
                pass
        
        # 3. ⚡ STANDALONE RELAY: If we have an internal MQTT client, publish there too
        if self._internal_mqtt and self._internal_mqtt_connected:
            try:
                payload = {"value": value, "source": "OSC", "timestamp": time.time()}
                self._internal_mqtt.publish(topic, orjson.dumps(payload).decode())
            except Exception as e:
                logger.error(f"[OSC] Failed to relay to internal MQTT: {e}")
        
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
        message_type = meta.get("message_type", "SPLICE_ACTION")
        origin_source = meta.get("origin_source", "UNKNOWN")

        if message_type == "LINK_FEEDBACK" and not meta.get("is_settled"):
            return
        if origin_source == "OSC":
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
        
        # --- LOOP PREVENTION & FILTERING (V3.1.8 MONITOR REFLECTION) ---
        # We no longer drop MQTT reflections here because we want local monitors 
        # to see the traffic. Hardware-level loops are handled by origin_source checks.
        is_self_reflection = (source == "MQTT" and message.get("full_id") == app_constants.FULL_INSTANCE_ID)

        # Determine if the message is OSC-related
        is_osc_related_by_tag = (logical_source == "OSC" or source == "OSC" or source == "OSC-TX")
        is_osc_related_by_topic = topic.startswith("OPEN-AIR/OSC/")
        is_osc_dest = any(dest == "OSC" for dest in message.get("strategy", "").split())

        if (is_osc_related_by_tag or is_osc_related_by_topic or is_osc_dest):
            # For re-transmission to hardware, we still need strict rules.
            # If it's a reflection, we only re-transmit if it's a settled state update.
            if is_self_reflection and not meta.get("is_settled"):
                pass # Allow to continue to monitor but skip re-send logic if needed

        # Skip SYSTEM, GUI, and internal topics.
        if source == "SYSTEM" or any(topic.startswith(x) for x in ["OPEN-AIR/System/", "OPEN-AIR/GUI/", "OPEN-AIR/oaGui/"]):
            return
            
        # Skip monitor topics.
        if "/Monitor/" in topic:
            return

        # --- MESSAGE PROCESSING ---
        # Map the topic to an OSC address (if not found, construct fallback).
        with self._state_lock:
            osc_address = self.topic_to_osc.get(topic)
            
        if not osc_address:
            # Fallback logic for topic to OSC address mapping.
            # Ensure that /OSC is only prepended if it's not already present in a way that
            # would create redundancy, and that the base topic is correctly formed.
            base_topic = topic.replace("OPEN-AIR/", "").lstrip("/")
            if base_topic.startswith("OSC/"):
                osc_address = "/" + base_topic
            else:
                osc_address = "/OSC/" + base_topic
            
            # Clean up potential double slashes or leading/trailing slashes after mapping
            osc_address = osc_address.replace("//", "/").strip("/")
            if not osc_address.startswith("/"):
                osc_address = "/" + osc_address
            
            # If the resulting address is just "/OSC" or "/", it's likely an invalid mapping.
            if osc_address == "/OSC" or osc_address == "/":
                osc_address = None # Invalidate the address to prevent sending.

        if osc_address: # Only proceed if a valid OSC address was determined
            real_val = value
            if isinstance(value, dict) and "value" in value:
                real_val = value["value"]
            
            origin_source = meta.get("origin_source", "UNKNOWN")
            
            # The Asynchronous "Listen-and-Filter" Loop
            # ⚡ V3.2.0 FILTERING: Prevent reflection of non-OSC sources back into the Hub
            should_send = (origin_source != "OSC" and not is_self_reflection) or meta.get("is_settled")
            
            # ⚡ V3.2.1 UPDATE: Allow MQTT and GUI sources to be bridged to OSC devices.
            is_valid_source = (logical_source in ["OSC", "GUI", "MQTT", "UNKNOWN"] or 
                               source in ["OSC", "OSC-TX", "MQTT"])
            
            if should_send and self.run_bridge and is_valid_source:
                if isinstance(real_val, (int, float, str, bool, list)):
                    self.send(osc_address, real_val, meta)
        else:
            osc_logger.warning(f"Skipping OSC re-transmission: No valid OSC address mapped for topic '{topic}'")
        
        # Monitor/Observer mode (executed for both bridge and non-bridge)
        if logical_source == "OSC":
            direction = meta.get("direction", "RX")
            address = meta.get("address", meta.get("osc_address", topic))
            # Extract real value safely
            r_val = value.get("value") if (isinstance(value, dict) and "value" in value and "address" in value) else value
            self._notify_monitor(direction, address, r_val, topic)
        elif source == "OSC-TX":
            self._notify_monitor("TX", meta.get("osc_address", topic), value, topic)
        elif logical_source == "MQTT" or source == "MQTT":
            # Show MQTT reflections in the monitor
            addr = meta.get("osc_address", topic)
            self._notify_monitor("MQTT", addr, value, topic)
        
        return

    def register_route(self, osc_address: str, topic: str):
        with self._state_lock:
            self.osc_to_topic[osc_address] = topic
            self.topic_to_osc[topic] = osc_address
            
        matrix_log("comms", "osc", "register_route", 
                   f"Route Registered: {osc_address} <-> {topic}", "INFO")
