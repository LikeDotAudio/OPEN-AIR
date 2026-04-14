# Managers/snmp_manager.py
# Dedicated orchestrator for SNMP traffic and bridge management.

import os
import time
import threading
from dataclasses import dataclass
from typing import Any, Optional
from oaLogging.Core.logger import SNMP_LOGGER as logger
from oaConfigurationManager.FileReaders.config_reader import Config
from oaComProtocols.oaComSNMP.Core.snmp_tree import SNMPTreeBuilder
from oaOchestration.Methods.network_utils import get_local_ip
from oaOchestration.Constants.project_paths import (
    SNMP_STATE_FILE, 
    SNMP_SET_LOG, 
    SNMP_CURRENT_MIB,
    SNMP_OPENAIR_MIB
)

from oaComProtocols.oaComSNMP.Core.oid_map_converter import OidMapConverter
from oaComProtocols.oaComSNMP.Core.snmp_state_persister import SnmpStatePersister
from oaComProtocols.oaComSNMP.Core.snmp_log_monitor import SnmpLogMonitor
from oaComProtocols.oaComSNMP.Methods.snmp_mib_generator import MibGenerator
from oaComProtocols.oaComSNMP.Methods.snmp_installer_generator import InstallerGenerator
from oaComProtocols.oaComSNMP.Workers.snmp_tester import SnmpTester
from oaComProtocols.oaComSNMP.Methods.snmp_utils import get_snmp_node_id, get_snmp_descriptor, initialize_oid_map
from oaComProtocols.oaComSNMP.Constants.snmp_constants import BASE_OID, STATE_SYNC_INTERVAL

from oaLogging.Core.logger import SNMP_LOGGER as snmp_logger, is_debug_allowed
from oaLogging.Methods.matrix_gate import matrix_log


@dataclass
class BridgeContext:
    state_cache_manager: Optional[Any] = None
    mqtt_connection_manager: Optional[Any] = None
    subscriber_router: Optional[Any] = None

class SNMPManager:
    """Factory and base interface for SNMP Managers."""
    
    @staticmethod
    def create(context: BridgeContext, run_bridge: bool):
        if run_bridge:
            return SNMPBridge(context)
        return SNMPObserver(context)

    def __init__(self, context: BridgeContext):
        self.context = context
        self._running = False
        self.run_bridge = False
        
        from oaOchestration.Constants.project_paths import (
            SNMP_STATE_FILE, 
            SNMP_CURRENT_MIB,
            SNMP_BRIDGE_SCRIPT
        )
        self.state_file = SNMP_STATE_FILE
        self.mib_path = SNMP_CURRENT_MIB
        self.master_script_path = SNMP_BRIDGE_SCRIPT
        self.base_oid = BASE_OID
        self._socket_info = "None"
        
        self.tree_builder = SNMPTreeBuilder(base_oid=self.base_oid)
        self.tree_builder.master_script_path = self.master_script_path
        
        self.oid_map = {}
        self._mqtt_state = {} # ⚡ REFLECTION: Local mirror of MQTT state
        self._monitor_callbacks = []
        self._state_lock = threading.RLock()
        
        self._initialize_workers()

    def get_mqtt_state(self):
        """Returns a snapshot of the reflected MQTT state."""
        with self._state_lock:
            return dict(self._mqtt_state)

    def _initialize_workers(self):
        self.oid_map_converter = OidMapConverter(self.base_oid, self._state_lock)
        self.state_persister = SnmpStatePersister(
            state_provider=self, # Pass self as the state provider
            thread_lock=self._state_lock,
            notify_monitor_callback=self._notify_monitor,
            run_bridge=self.run_bridge,
            base_oid=self.base_oid,
            oid_map_converter=self.oid_map_converter
        )
        self.log_monitor = SnmpLogMonitor(
            state_cache_manager=self.context.state_cache_manager,
            thread_lock=self._state_lock,
            notify_monitor_callback=self._notify_monitor,
            running_flag_getter=lambda: self._running
        )

    def get_status(self):
        with self._state_lock:
            status = {
                "running": self._running,
                "socket": self._socket_info,
                "base_oid": self.base_oid,
                "object_count": len(self.oid_map_converter.oid_map),
                "bridge_mode": self.run_bridge,
                "mib_path": self.mib_path,
                "installer_script": self.get_installer_script()
            }
            return status

    def add_monitor_callback(self, callback):
        with self._state_lock:
            if callback not in self._monitor_callbacks:
                self._monitor_callbacks.append(callback)

    def remove_monitor_callback(self, callback):
        with self._state_lock:
            if callback in self._monitor_callbacks:
                self._monitor_callbacks.remove(callback)

    def _notify_monitor(self, direction, oid, value, topic=None, metadata=None):
        with self._state_lock:
            callbacks = list(self._monitor_callbacks)

        for cb in callbacks:
            try: cb(direction, oid, value, topic, metadata)
            except Exception: pass

        if self.run_bridge and self.context.state_cache_manager:
            if topic and "Monitor/SNMP" in topic: return
            
            # ⚡ ANTI-LOOP: Tag our outgoing activity logs so we don't ingest them back
            monitor_payload = {
                "value": value, "source": "SNMP", "oid": oid,
                "topic": topic, "direction": direction, "timestamp": time.time(), "metadata": metadata,
                "origin_source": "oaComSNMP"
            }
            self.context.state_cache_manager.handle_external_update(
                "OPEN-AIR/System/Monitor/SNMP/Activity", monitor_payload, source="SNMP"
            )

    def handle_protocol_event(self, message):
        """
        Processes unified messages from the ProtocolRouter.
        Ensures SNMP state is a direct reflection of MQTT traffic.
        """
        with self._state_lock:
            if not self._running: return
            
            # ⚡ REFLECTION: Only update our internal state if the message originated from MQTT
            # OR if we are the bridge and this is a direct dispatch (logical_source is NOT SNMP)
            source = message.get("source", "UNKNOWN").upper()
            is_reflection = message.get("is_reflection", False)
            
            # If it's a reflection of our own authorship, ignore it
            meta = message.get("meta", {})
            if is_reflection or meta.get("origin_source") in ["oaComSNMP", "SNMP"]:
                return

            if source == "MQTT" or (self.run_bridge and source != "SNMP"):
                topic = message.get("topic")
                if topic:
                    # Update local state mirror with the normalized router packet
                    self._mqtt_state[topic] = message

    def publish(self, topic, value, meta=None):
        """
        Direct dispatch entry point for the ProtocolRouter.
        Standardizes the incoming data into a synthetic router packet for the state mirror.
        """
        synthetic_message = {
            "source": "INTERNAL",
            "logical_source": "ROUTER",
            "topic": topic,
            "value": value,
            "meta": meta or {}
        }
        self.handle_protocol_event(synthetic_message)

    def start(self, display_root=None):
        with self._state_lock:
            if self._running: return
            self._running = True
        
        configuration = Config.get_instance()
        self._socket_info = f"{get_local_ip()}:{configuration.SNMP_PORT} (System Daemon Bridge)"
        
        # ⚡ STANDALONE: The OID map source is now decoupled from the protocol logic.
        # We check for an explicit display_root, then a config override, then fallback.
        oid_source = display_root or getattr(configuration, "OID_MAP_SOURCE", None)
        
        if oid_source and os.path.exists(oid_source):
            start_oid = time.time()
            matrix_log("comms", "snmp", "start", f"📡 [SNMP] Initializing OID Map from: {oid_source}...", "DEBUG")
            initialize_oid_map(oid_source)
            end_oid = time.time()
            matrix_log("comms", "snmp", "start", f"📡 [SNMP] OID Map initialized from: {oid_source} in {end_oid - start_oid:.4f}s.", "SUCCESS")
        else:
            matrix_log("comms", "snmp", "start", "📡 [SNMP] No OID Map source found. Using default/flat topic mapping.", "WARNING")

        matrix_log("comms", "snmp", "start", "📡 [SNMP] Starting persistence and monitoring workers...", "DEBUG")
        self.state_persister.start()
        self.log_monitor.start()

        # ⚡ PRIME STATE: Initialize our internal mirror from the global state cache
        if self.context.state_cache_manager:
            with self._state_lock:
                start_time = time.time()
                matrix_log("comms", "snmp", "start", "📡 [SNMP] Priming state mirror from cache...", "DEBUG")
                
                # ⚡ PERFORMANCE: Directly iterate over Rust cache items to avoid deepcopy/dict conversion
                items = self.context.state_cache_manager.rust_cache.items()
                mid_time = time.time()
                matrix_log("comms", "snmp", "start", f"📡 [SNMP] Cache items retrieved in {mid_time - start_time:.4f}s. Normalizing {len(items)} entries...", "DEBUG")
                
                for topic, payload in items:
                    if topic not in self._mqtt_state:
                        # Normalize cached entries into router-like packets
                        self._mqtt_state[topic] = {
                            "source": "CACHE",
                            "topic": topic,
                            "value": payload.get("value") if isinstance(payload, dict) else payload,
                            "meta": payload if isinstance(payload, dict) else {}
                        }
                end_time = time.time()
                matrix_log("comms", "snmp", "start", f"📡 [SNMP] Primed state mirror in {end_time - mid_time:.4f}s. Total: {end_time - start_time:.4f}s.", "INFO")

        from oaComBroker.Core.protocol_router.manager import ProtocolRouter
        router = ProtocolRouter.get_instance()
        router.register_cache_observer(self.handle_protocol_event)
        
        # ⚡ V3.1.24 STATUS VISIBILITY: Ensure all modes (Bridge/Observer) publish status.
        if self.context.mqtt_connection_manager:
            self._status_update_thread = threading.Thread(target=self._mqtt_status_loop, daemon=True, name="SNMP-MqttStatus")
            self._status_update_thread.start()

        self._start_specifics(router)

    def _mqtt_status_loop(self):
        while self._running:
            self._publish_status()
            time.sleep(5)

    def _publish_status(self, force_script=False):
        if not self.context.mqtt_connection_manager: return
        status = self.get_status()
        self.context.mqtt_connection_manager.publish("OPEN-AIR/System/Status/SNMP/Bridge", status)

    def _start_specifics(self, router):
        pass

    def _handle_network_activity(self, message):
        try:
            if not message.payload:
                return

            import orjson
            payload = message.payload.decode() if isinstance(message.payload, bytes) else message.payload
            data = orjson.loads(payload)
            synthetic_message = {
                "source": "MQTT", "logical_source": "SNMP", "topic": message.topic,
                "value": data, "meta": data.get("metadata", {})
            }
            self.handle_protocol_event(synthetic_message)
        except Exception as e:
            if is_debug_allowed("comms", "snmp"): snmp_logger.error(f"❌ [SNMP-UI] Failed to parse network activity: {e}")

    def stop(self):
        # ⚡ V3.1.29 RESILIENCE: Use a timed lock to avoid hanging during rapid shutdown/interruption
        if not self._state_lock.acquire(timeout=1.0):
            snmp_logger.warning("SNMP stop() timed out waiting for lock. Forcing shutdown.")
        
        try:
            if not self._running: return
            self._running = False
        finally:
            try: self._state_lock.release()
            except RuntimeError: pass # Already released or not held
        
        snmp_logger.warning("SNMP Bridge Offline.")
        try:
            from oaComBroker.Core.protocol_router.manager import ProtocolRouter
            router = ProtocolRouter.get_instance()
            if hasattr(router, "unregister_cache_observer"):
                router.unregister_cache_observer(self.handle_protocol_event)
            if self.run_bridge and hasattr(router, "set_snmp_manager"):
                router.set_snmp_manager(None)
        except Exception as e:
            snmp_logger.error(f"Failed to unregister SNMP Manager from router: {e}")

        self.state_persister.stop()
        self.log_monitor.stop()

    def get_mib_content(self):
        state_snapshot = self.get_mqtt_state()
        oid_map_data = self.oid_map_converter.build_oid_map(state_snapshot=state_snapshot)
        with self._state_lock:
            return MibGenerator.generate(self.base_oid, self.oid_map_converter.oid_map)

    def save_current_mib(self):
        try:
            os.makedirs(os.path.dirname(SNMP_CURRENT_MIB), exist_ok=True)
            content = self.get_mib_content()
            
            # Write to 'current.mib' for internal tracking
            with open(SNMP_CURRENT_MIB, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Write to 'OPEN-AIR.mib' for external delivery as requested
            with open(SNMP_OPENAIR_MIB, "w", encoding="utf-8") as f:
                f.write(content)
                
            if is_debug_allowed("comms", "snmp"): 
                snmp_logger.success(f"MIB Synchronized to {SNMP_CURRENT_MIB} and {SNMP_OPENAIR_MIB}")
            return True
        except Exception as e:
            snmp_logger.error(f"Failed to save MIB: {e}")
            return False

    def get_installer_script(self):
        return InstallerGenerator.generate(self.base_oid, self.master_script_path)

    def run_verification(self, mib_path=None, force_raw=True):
        if mib_path: return SnmpTester.verify_oid_tree(self.base_oid, mib_path=mib_path)
        if force_raw: return SnmpTester.verify_oid_tree(self.base_oid)
        mib_content = self.get_mib_content()
        return SnmpTester.verify_oid_tree(self.base_oid, mib_content=mib_content)


class SNMPObserver(SNMPManager):
    def __init__(self, context: BridgeContext):
        super().__init__(context)
        self.run_bridge = False
        
    def handle_protocol_event(self, message):
        # 1. Update internal state (reflection)
        super().handle_protocol_event(message)
        
        with self._state_lock:
            if not self._running: return

        source = message.get("source", "UNKNOWN").upper()
        logical_source = message.get("logical_source", source).upper()
        topic = str(message.get("topic", ""))
        value = message.get("value")
        meta = message.get("meta", {})

        if logical_source == "SNMP":
            if topic == "OPEN-AIR/System/Monitor/SNMP/Activity" and isinstance(value, dict):
                direction = value.get("direction", "RX")
                oid = value.get("oid", "unknown")
                real_val = value.get("value")
                real_topic = value.get("topic")
                metadata = value.get("metadata")
                self._notify_monitor(direction, oid, real_val, real_topic, metadata)
            elif topic != "OPEN-AIR/System/Monitor/SNMP/Activity":
                oid = meta.get("oid", topic.split("/")[-1])
                self._notify_monitor("RX", oid, value, topic, meta)

    def _start_specifics(self, router):
        if self.context.subscriber_router:
            self.context.subscriber_router.subscribe_to_topic(
                "OPEN-AIR/System/Monitor/SNMP/Activity", self._handle_network_activity
            )
        if is_debug_allowed("comms", "snmp"): snmp_logger.info("SNMP Bridge: Running in Observer mode.")


class SNMPBridge(SNMPManager):
    def __init__(self, context: BridgeContext):
        super().__init__(context)
        self.run_bridge = True
        self.state_persister.run_bridge = True

    def handle_protocol_event(self, message):
        # Update internal state (reflection)
        super().handle_protocol_event(message)

    def _start_specifics(self, router):
        try:
            self.tree_builder.generate_master_script()
            if hasattr(router, "set_snmp_manager"):
                router.set_snmp_manager(self)
            
            if self.context.subscriber_router:
                self.context.subscriber_router.subscribe_to_topic("OPEN-AIR/System/Control/SNMP/GenerateScript", self._handle_mqtt_command)

                # ⚡ RACE CONDITION FIX: Give the router time to populate the state mirror
                # before generating the initial MIB. We run this in a thread to avoid 
                # blocking the main startup sequence in launcher.py.
                def delayed_mib_sync():
                    snmp_logger.info("SNMP Bridge: Delaying initial MIB generation for 5 seconds to allow state sync...")
                    time.sleep(5)
                    self.save_current_mib()
                    if is_debug_allowed("comms", "snmp"): 
                        snmp_logger.success(f"SNMP Bridge Active on {self._socket_info}")
                
                threading.Thread(target=delayed_mib_sync, daemon=True, name="SNMP-InitialSync").start()

        except Exception as e:
            snmp_logger.error(f"SNMP Bridge Start Failed: {e}")

    def _handle_mqtt_command(self, message):
        if "GenerateScript" in message.topic:
            self.tree_builder.generate_master_script()
            self._publish_status(force_script=True)
