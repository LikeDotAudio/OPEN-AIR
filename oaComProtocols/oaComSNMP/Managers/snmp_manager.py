# oaComProtocols.oaComSNMP/Managers/snmp_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260414.215.1
#
# Description: Dedicated orchestrator for SNMP traffic and bridge management.
# ⚡ STANDALONE: 100% independent of ProtocolRouter and StateCache.

import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from oaComProtocols.oaComSNMP.Constants.snmp_constants import BASE_OID
from oaComProtocols.oaComSNMP.Core.oid_map_converter import OidMapConverter
from oaComProtocols.oaComSNMP.Core.snmp_log_monitor import SnmpLogMonitor
from oaComProtocols.oaComSNMP.Core.snmp_mqtt_client import SnmpMqttClient
from oaComProtocols.oaComSNMP.Core.snmp_state_persister import SnmpStatePersister
from oaComProtocols.oaComSNMP.Core.snmp_tree import SNMPTreeBuilder
from oaComProtocols.oaComSNMP.Methods.snmp_mib_generator import MibGenerator
from oaComProtocols.oaComSNMP.Methods.snmp_utils import initialize_oid_map
from oaConfigurationManager.Entry import Config
from oaLogging.Core.logger import SNMP_LOGGER as snmp_logger
from oaLogging.Methods.matrix_gate import matrix_log


@dataclass
class BridgeContext:
    mqtt_client: SnmpMqttClient | None = None

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

        from oaOchestration.Constants.project_paths import SNMP_BRIDGE_SCRIPT, SNMP_CURRENT_MIB, SNMP_STATE_FILE
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
        self._mqtt_listeners = []
        self._state_lock = threading.RLock()

        self._initialize_workers()

    def register_mqtt_listener(self, callback: Callable[[str, Any], None]):
        """Registers a listener for incoming MQTT messages."""
        with self._state_lock:
            if callback not in self._mqtt_listeners:
                self._mqtt_listeners.append(callback)

    def remove_mqtt_listener(self, callback: Callable[[str, Any], None]):
        """Unregisters an MQTT listener."""
        with self._state_lock:
            if callback in self._mqtt_listeners:
                self._mqtt_listeners.remove(callback)

    def get_mqtt_state(self):
        """Returns a snapshot of the reflected MQTT state."""
        with self._state_lock:
            return dict(self._mqtt_state)

    def _initialize_workers(self):
        self.oid_map_converter = OidMapConverter(self.base_oid, self._state_lock)
        self.state_persister = SnmpStatePersister(
            state_provider=self,
            thread_lock=self._state_lock,
            notify_monitor_callback=self._notify_monitor,
            run_bridge=self.run_bridge,
            base_oid=self.base_oid,
            oid_map_converter=self.oid_map_converter
        )
        self.log_monitor = SnmpLogMonitor(
            thread_lock=self._state_lock,
            notify_monitor_callback=self._notify_monitor,
            running_flag_getter=lambda: self._running,
            mqtt_client=self.context.mqtt_client
        )

    def start(self, display_root=None):
        if self._running: return
        self._running = True

        configuration = Config.get_instance()

        # ⚡ STANDALONE OID Mapping
        oid_source = display_root or getattr(configuration, "OID_MAP_SOURCE", None)
        if oid_source and os.path.exists(oid_source):
            initialize_oid_map(oid_source)
        else:
            matrix_log("comms", "snmp", "start", "📡 [SNMP] No OID Map source found. Using default mapping.", "DEBUG")

        # ⚡ OPTIMIZATION: Only start local workers if we are the master bridge
        if self.run_bridge:
            matrix_log("comms", "snmp", "start", "📡 [SNMP] Starting persistence and monitoring workers (Bridge Mode)...", "DEBUG")
            self.state_persister.start()
            self.log_monitor.start()
        else:
            matrix_log("comms", "snmp", "start", "📡 [SNMP] Observer active. Local workers suppressed.", "DEBUG")

        # ⚡ NATIVE STANDALONE MQTT
        if self.context.mqtt_client:
            if hasattr(self.context.mqtt_client, 'set_on_message_callback'):
                self.context.mqtt_client.set_on_message_callback(self.handle_mqtt_message)
            else:
                self.context.mqtt_client.on_message_callback = self.handle_mqtt_message

            self.context.mqtt_client.subscribe("OPEN-AIR/#")

            self._status_update_thread = threading.Thread(target=self._mqtt_status_loop, daemon=True, name="SNMP-MqttStatus")
            self._status_update_thread.start()

        # ⚡ OPTIMIZATION: Non-blocking specific initialization
        threading.Thread(target=self._start_specifics, daemon=True, name="SNMP-StartSpecifics").start()
    def handle_mqtt_message(self, topic: str, payload: Any):
        """Processes raw MQTT messages to maintain the SNMP state mirror."""
        if not self._running: return

        # ⚡ PROPAGATE: Notify external listeners (e.g. UI tabs)
        with self._state_lock:
            listeners = list(self._mqtt_listeners)
        for listener in listeners:
            try: listener(topic, payload)
            except: pass

        # ⚡ ANTI-FEEDBACK
        if "Monitor/SNMP" in topic: return

        # If the origin_source is SNMP, ignore it to prevent loops
        if isinstance(payload, dict) and payload.get("origin_source") in ["oaComSNMP", "SNMP"]:
            return

        with self._state_lock:
            self._mqtt_state[topic] = {
                "source": "MQTT",
                "topic": topic,
                "value": payload.get("value") if isinstance(payload, dict) else payload,
                "meta": payload if isinstance(payload, dict) else {}
            }

    def _mqtt_status_loop(self):
        while self._running:
            self._publish_status()
            time.sleep(5)

    def _publish_status(self):
        if not self.context.mqtt_client: return
        status = self.get_status()
        self.context.mqtt_client.publish("OPEN-AIR/System/Status/SNMP/Bridge", status)

    def _start_specifics(self):
        pass

    def stop(self):
        # ⚡ SIGNAL SHUTDOWN FIRST: Ensure background threads see _running=False and release the lock.
        self._running = False

        if not self._state_lock.acquire(timeout=2.0):
            snmp_logger.warning("SNMP stop() timed out waiting for lock. Forcing thread termination.")
        else:
            try:
                # Any final state-protected cleanup here
                pass
            finally:
                self._state_lock.release()

        self.state_persister.stop()
        self.log_monitor.stop()

    def get_status(self):
        with self._state_lock:
            status = {
                "running": self._running,
                "socket": self._socket_info,
                "base_oid": self.base_oid,
                "object_count": len(self.oid_map_converter.oid_map),
                "bridge_mode": self.run_bridge,
                "mib_path": str(self.mib_path),
                "installer_script": self.get_installer_script()
            }
            return status

    def _notify_monitor(self, direction, oid, value, topic=None, metadata=None):
        with self._state_lock:
            callbacks = list(self._monitor_callbacks)

        for cb in callbacks:
            try: cb(direction, oid, value, topic, metadata)
            except: pass

        if self.run_bridge and self.context.mqtt_client:
            if topic and "Monitor/SNMP" in topic: return

            monitor_payload = {
                "value": value, "source": "SNMP", "oid": oid,
                "topic": topic, "direction": direction, "timestamp": time.time(), "metadata": metadata,
                "origin_source": "oaComSNMP"
            }
            self.context.mqtt_client.publish("OPEN-AIR/System/Monitor/SNMP/Activity", monitor_payload)

    def add_monitor_callback(self, callback):
        with self._state_lock:
            if callback not in self._monitor_callbacks:
                self._monitor_callbacks.append(callback)

    def remove_monitor_callback(self, callback):
        with self._state_lock:
            if callback in self._monitor_callbacks:
                self._monitor_callbacks.remove(callback)

    def reset_monitor_state(self):
        if hasattr(self, 'state_persister'):
            self.state_persister.reset_delta_tracking()

    def run_verification(self, mib_path=None):
        """Runs an snmpwalk to verify the current OID tree or a specific MIB."""
        from oaComProtocols.oaComSNMP.Workers.snmp_tester import SnmpTester
        return SnmpTester.verify_oid_tree(base_oid=self.base_oid, mib_path=mib_path)

    def get_mib_content(self):
        state_snapshot = self.get_mqtt_state()
        self.oid_map_converter.build_oid_map(state_snapshot)
        return MibGenerator.generate(self.base_oid, self.oid_map_converter.oid_map)

    def save_current_mib(self):
        try:
            content = self.get_mib_content()
            from oaOchestration.Constants.project_paths import SNMP_CURRENT_MIB, SNMP_OPENAIR_MIB
            os.makedirs(os.path.dirname(SNMP_CURRENT_MIB), exist_ok=True)
            with open(SNMP_CURRENT_MIB, "w") as f: f.write(content)
            with open(SNMP_OPENAIR_MIB, "w") as f: f.write(content)
            return True
        except Exception as e:
            snmp_logger.error(f"Failed to save MIB: {e}")
            return False

    def get_installer_script(self):
        from oaComProtocols.oaComSNMP.Methods.snmp_installer_generator import InstallerGenerator
        return InstallerGenerator.generate(self.base_oid, self.master_script_path)

class SNMPObserver(SNMPManager):
    def __init__(self, context: BridgeContext):
        super().__init__(context)
        self.run_bridge = False

    def handle_mqtt_message(self, topic: str, payload: Any):
        super().handle_mqtt_message(topic, payload)

        if not self._running: return

        value = payload.get("value") if isinstance(payload, dict) else payload
        meta = payload if isinstance(payload, dict) else {}

        if topic == "OPEN-AIR/System/Monitor/SNMP/Activity" and isinstance(payload, dict):
            self._notify_monitor(
                payload.get("direction", "RX"), payload.get("oid", "unknown"),
                payload.get("value"), payload.get("topic"), payload.get("metadata")
            )
        elif "Monitor/SNMP" not in topic:
            oid = meta.get("oid", topic.split("/")[-1])
            self._notify_monitor("RX", oid, value, topic, meta)

class SNMPBridge(SNMPManager):
    def __init__(self, context: BridgeContext):
        super().__init__(context)
        self.run_bridge = True
        self.state_persister.run_bridge = True

    def _start_specifics(self):
        self.tree_builder.generate_master_script()
        # ⚡ OPTIMIZATION: Trigger immediate MIB sync, then follow up if needed
        self.delayed_mib_sync(immediate=True)

    def delayed_mib_sync(self, immediate=False):
        try:
            if not immediate:
                time.sleep(5)

            if self._running:
                self.tree_builder.generate_master_script()
                self.save_current_mib()
                snmp_logger.success("SNMP Bridge Active")
        except Exception as e:
            snmp_logger.error(f"SNMP Bridge sync failed: {e}")
