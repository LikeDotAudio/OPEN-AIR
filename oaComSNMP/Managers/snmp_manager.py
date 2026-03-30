# Managers/snmp_manager.py
#
# Dedicated orchestrator for SNMP traffic and bridge management.
#
# Author: Anthony P. Kuzub (Refactored)
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260329.1005.1
#
# Description:
# The SNMPManager serves as the central hub for the SNMP communication layer. 
# It orchestrates the synchronization between the internal MQTT-based state 
# cache and the external SNMP daemon (snmpd). It manages OID mapping, state 
# persistence, and log monitoring for incoming SET commands.
#
# Architectural Role:
# - Bridge Orchestrator: Connects Core partition logic with SNMP protocols.
# - Lifecycle Manager: Controls background persistence and monitoring threads.
# - Protocol Translator: Maps hierarchical MQTT topics to numerical OID trees.

import os
import time
import threading
from loguru import logger
from oaConfiguration.FileReaders.config_reader import Config
from oaComSNMP.Core.snmp_tree import SNMPTreeBuilder
from oaOchestration.Methods.network_utils import get_local_ip
from oaOchestration.Constants.project_paths import (
    SNMP_STATE_FILE, 
    SNMP_SET_LOG, 
    SNMP_CURRENT_MIB
)

from oaComSNMP.Core.oid_map_converter import OidMapConverter
from oaComSNMP.Core.snmp_state_persister import SnmpStatePersister
from oaComSNMP.Core.snmp_log_monitor import SnmpLogMonitor
from oaDataSNMP.Entry import SnmpDataEntry
# --- Specialized Logic Workers ---
from oaComSNMP.Methods.snmp_mib_generator import MibGenerator
from oaComSNMP.Methods.snmp_installer_generator import InstallerGenerator
from oaComSNMP.Workers.snmp_tester import SnmpTester
from oaComSNMP.Methods.snmp_utils import get_snmp_node_id, get_snmp_descriptor, initialize_oid_map
from oaComSNMP.Constants.snmp_constants import BASE_OID, STATE_SYNC_INTERVAL

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import SNMP_LOGGER as snmp_logger, is_debug_allowed
LOCAL_DEBUG = is_debug_allowed(system="Comms", element="SNMP")

class SNMPManager:
    """
    Manages the SNMP protocol bridge.
    Centralizes all SNMP logic away from the UI.
    """

    def __init__(self, state_cache_manager=None, mqtt_connection_manager=None, subscriber_router=None, run_bridge=True):
        self.run_bridge = run_bridge
        if LOCAL_DEBUG:
            snmp_logger.info("Initializing SNMP Bridge...")
        
        self.state_cache_manager = state_cache_manager
        self.mqtt_connection_manager = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self._running = False
        
        # ⚡ DATA ARCHITECTURE: Use oaDataSNMP for all state/config paths
        self.data_manager = SnmpDataEntry()
        self.state_file = self.data_manager.get_state_path()
        self.mib_path = self.data_manager.get_mib_path()
        self.base_oid = BASE_OID
        self._socket_info = "None"
        
        # Initialize tree builder with the correct script path from data_manager
        self.tree_builder = SNMPTreeBuilder(base_oid=self.base_oid)
        self.tree_builder.master_script_path = self.data_manager.get_master_script_path()
        
        self.oid_map = {}
        self._last_topic_count = 0
        self._monitor_callbacks = []
        
        # ⚡ THREAD SAFETY: Protect shared mutable state
        self._state_lock = threading.RLock()
        
        # Instantiate the OID Map Converter
        self.oid_map_converter = OidMapConverter(self.base_oid, self.state_cache_manager, self._state_lock)
        
        # Instantiate the State Persister
        self.state_persister = SnmpStatePersister(
            state_cache_manager=self.state_cache_manager,
            thread_lock=self._state_lock,
            notify_monitor_callback=self._notify_monitor,
            run_bridge=self.run_bridge,
            base_oid=self.base_oid,
            oid_map_converter=self.oid_map_converter
        )
        
        # Instantiate the Log Monitor
        self.log_monitor = SnmpLogMonitor(
            state_cache_manager=self.state_cache_manager,
            thread_lock=self._state_lock,
            notify_monitor_callback=self._notify_monitor,
            running_flag_getter=lambda: self._running # Function to get running state
        )

    def get_status(self):
        """Returns a logic-only status report for the UI."""
        with self._state_lock:
            return {
                "running": self._running,
                "socket": self._socket_info,
                "base_oid": self.base_oid,
                "object_count": len(self.oid_map_converter.oid_map),
                "bridge_mode": self.run_bridge,
                "mib_path": self.mib_path
            }

    def add_monitor_callback(self, callback):
        with self._state_lock:
            if callback not in self._monitor_callbacks:
                self._monitor_callbacks.append(callback)

    def remove_monitor_callback(self, callback):
        with self._state_lock:
            if callback in self._monitor_callbacks:
                self._monitor_callbacks.remove(callback)

    def _notify_monitor(self, direction, oid, value, topic=None, metadata=None):
        """
        Notify all registered callbacks of SNMP activity.
        And broadcast to the system-wide monitor topic if in Bridge mode.
        """
        # 1. Local Notifications
        with self._state_lock:
            callbacks = list(self._monitor_callbacks)

        for cb in callbacks:
            try: 
                cb(direction, oid, value, topic, metadata)
            except Exception: pass

        # 2. System-wide Broadcast (Bridge Mode -> Network)
        # We only broadcast individual changes or periodic dumps to the network monitor
        if self.run_bridge and self.state_cache_manager:
            # Skip recursion: Don't report on the monitor topic itself
            if topic and "Monitor/SNMP" in topic:
                return

            monitor_payload = {
                "val": value,
                "source": "SNMP",
                "oid": oid,
                "topic": topic,
                "direction": direction,
                "ts": time.time(),
                "metadata": metadata
            }

            # Use a throttled or specific topic for the monitor feed
            self.state_cache_manager.handle_external_update(
                "OPEN-AIR/System/Monitor/SNMP/Activity",
                monitor_payload,
                source="SNMP"
            )

    def handle_protocol_event(self, msg):
        """
        Callback for all router traffic. 
        In UI mode, this is our primary way of seeing what CORE is doing.
        """
        with self._state_lock:
            if not self._running: return

        source = msg.get("source", "UNKNOWN").upper()
        logical_source = msg.get("logical_source", source).upper()
        topic = str(msg.get("topic", ""))
        val = msg.get("val")
        meta = msg.get("meta", {})

        # --- CASE 1: Monitor UI Update (UI Only) ---
        if not self.run_bridge:
            if logical_source == "SNMP":
                # This could be a direct OID update or a monitor packet
                if topic == "OPEN-AIR/System/Monitor/SNMP/Activity":
                    # Unpack the monitor payload
                    direction = val.get("direction", "RX")
                    oid = val.get("oid", "unknown")
                    real_val = val.get("val")
                    real_topic = val.get("topic")
                    metadata = val.get("metadata")
                    self._notify_monitor(direction, oid, real_val, real_topic, metadata)
                else:
                    # Direct OID update (logical source is SNMP)
                    oid = meta.get("oid", topic.split("/")[-1])
                    self._notify_monitor("RX", oid, val, topic, meta)
            return

        # --- CASE 2: Core Bridge Mirroring (Bridge Mode) ---
        # Currently SNMP is primarily a 'Pull' protocol via file sync, 
        # but we handle protocol events for future 'Push' trap support.
        pass

    def start(self):
        with self._state_lock:
            if self._running: return
            self._running = True
        
        from oaConfiguration.FileReaders.config_reader import Config
        cfg = Config.get_instance()
        self._socket_info = f"{get_local_ip()}:{cfg.SNMP_PORT} (System Daemon Bridge)"
        
        # ⚡ CRAWLER: Build the metadata map from folders
        from oaOchestration.Core.path_initializer import GLOBAL_PROJECT_ROOT
        initialize_oid_map(os.path.join(str(GLOBAL_PROJECT_ROOT), "oaGuiDefinitions"))

        # 🟢 Start Background Monitor
        # Start the SnmpStatePersister thread
        self.state_persister.start()

        # Start the SnmpLogMonitor thread
        self.log_monitor.start()

        # Protocol Router Sync Logic: Listen for remote/local activity
        from oaComBroker.Core.protocol_router.manager import ProtocolRouter
        router = ProtocolRouter.get_instance()
        router.register_cache_observer(self.handle_protocol_event)

        # ⚡ NETWORK SYNC: In UI mode, we need to listen for traffic from CORE
        if not self.run_bridge and self.subscriber_router:
            if LOCAL_DEBUG:
                snmp_logger.info("📡 [SNMP] Linking to system SNMP activity (Monitor/SNMP/Activity)")
            self.subscriber_router.subscribe_to_topic(
                "OPEN-AIR/System/Monitor/SNMP/Activity",
                self._handle_network_activity
            )

        if self.run_bridge:
            try:
                self.tree_builder.generate_master_script()
                
                # ⚡ MODULARITY: Register self as the active SNMP manager
                if hasattr(router, "set_snmp_manager"):
                    router.set_snmp_manager(self)
                
                # 📡 MQTT BRIDGE: Support UI-to-Core communication
                if self.mqtt_connection_manager and self.subscriber_router:
                    # Subscribe to UI commands
                    self.subscriber_router.subscribe_to_topic("OPEN-AIR/System/Control/SNMP/GenerateScript", self._handle_mqtt_command)
                    # Start periodic status updates
                    self._status_update_thread = threading.Thread(target=self._mqtt_status_loop, daemon=True, name="SNMP-MqttStatus")
                    self._status_update_thread.start()
                    
                # Initial MIB Sync
                self.save_current_mib()
                if LOCAL_DEBUG:
                    snmp_logger.success(f"SNMP Bridge Active on {self._socket_info}")
            except Exception as e:
                snmp_logger.error(f"SNMP Bridge Start Failed: {e}")
        else:
            if LOCAL_DEBUG:
                snmp_logger.info("SNMP Bridge: Running in Observer mode.")

    def _handle_mqtt_command(self, msg):
        """Processes commands sent from the UI via MQTT."""
        topic = msg.topic
        if "GenerateScript" in topic:
            if LOCAL_DEBUG: snmp_logger.info("📡📥 [INBOUND] SNMP command: GenerateScript")
            self.tree_builder.generate_master_script()
            self._publish_status(force_script=True)

    def _handle_network_activity(self, msg):
        """Shim to ingest network SNMP activity into the local event handler."""
        try:
            import orjson
            # msg.payload can be bytes or str depending on the client
            payload = msg.payload.decode() if isinstance(msg.payload, bytes) else msg.payload
            data = orjson.loads(payload)
            # Create a synthetic router message for the internal event handler
            synthetic_msg = {
                "source": "MQTT",
                "logical_source": "SNMP",
                "topic": msg.topic,
                "val": data,
                "meta": data.get("metadata", {})
            }
            self.handle_protocol_event(synthetic_msg)
        except Exception as e:
            if LOCAL_DEBUG: snmp_logger.error(f"❌ [SNMP-UI] Failed to parse network activity: {e}")

    def _mqtt_status_loop(self):
        """Periodically publishes bridge status to MQTT for UI consumption."""
        while self._running:
            self._publish_status()
            time.sleep(5)

    def _publish_status(self, force_script=False):
        """Publishes the current bridge status to MQTT."""
        if not self.mqtt_connection_manager: return
        
        status = self.get_status()
        # Add the installer script if requested
        if force_script:
            status["installer_script"] = self.get_installer_script()
            
        self.mqtt_connection_manager.publish("OPEN-AIR/System/Status/SNMP/Bridge", status)

    def stop(self):
        """
        Signals the SNMP bridge and all associated workers to stop.
        
        Side Effects:
            - Transitions the 'running' state to False.
            - Stops the background persistence and log monitoring threads.
            - Unregisters from the Protocol Router to prevent duplicate observers.
            - Logs a warning that the bridge is offline.
        """
        with self._state_lock:
            if not self._running:
                return
            self._running = False
        
        snmp_logger.warning("SNMP Bridge Offline.")
        
        # 1. Unregister from Protocol Router to stop receiving events
        try:
            from oaComBroker.Core.protocol_router.manager import ProtocolRouter
            router = ProtocolRouter.get_instance()
            if hasattr(router, "unregister_cache_observer"):
                router.unregister_cache_observer(self.handle_protocol_event)
            
            # Clear self as the active SNMP manager in the router
            if self.run_bridge and hasattr(router, "set_snmp_manager"):
                router.set_snmp_manager(None)
        except Exception as e:
            snmp_logger.error(f"Failed to unregister SNMP Manager from router: {e}")

        # 2. Stop background worker threads.
        self.state_persister.stop()
        self.log_monitor.stop()

    def publish(self, topic, val, meta=None):
        """
        Placeholder for explicit data publication (Traps).
        
        Note:
            The current SNMP implementation uses a 'Pull' model via file 
            synchronization with the snmpd daemon.
        """
        pass

    # --- Worker Delegations ---
    def get_mib_content(self):
        """
        Generates dynamic MIB file content based on the current OID map.
        
        Returns:
            str: Complete SMIv2 MIB definition.
        """
        if LOCAL_DEBUG:
            snmp_logger.debug("Generating dynamic MIB content.")
        oid_map_data = self.oid_map_converter.build_oid_map()
        with self._state_lock:
            return MibGenerator.generate(self.base_oid, self.oid_map_converter.oid_map)

    def save_current_mib(self):
        """
        Serializes the dynamic MIB to the configured system path.
        
        Returns:
            bool: True on success, False on failure.
        """
        try:
            os.makedirs(os.path.dirname(SNMP_CURRENT_MIB), exist_ok=True)
            content = self.get_mib_content()
            with open(SNMP_CURRENT_MIB, "w", encoding="utf-8") as f:
                f.write(content)
            if LOCAL_DEBUG:
                snmp_logger.success(f"MIB Synchronized to {SNMP_CURRENT_MIB}")
            return True
        except Exception as e:
            snmp_logger.error(f"Failed to save MIB: {e}")
            return False

    def get_installer_script(self):
        """
        Retrieves the full bash installation script for system deployment.
        
        Returns:
            str: Bash installer content.
        """
        return InstallerGenerator.generate(self.base_oid, self.data_manager.get_master_script_path())

    def run_verification(self, mib_path=None, force_raw=True):
        """
        Executes a diagnostic snmpwalk to verify tree availability.
        
        Args:
            mib_path (str, optional): Path to a specific MIB file.
            force_raw (bool): If True, returns numerical OIDs only.
            
        Returns:
            str: Diagnostic report from the snmpwalk command.
        """
        if mib_path:
            if LOCAL_DEBUG:
                snmp_logger.debug(f"Verifying with MIB: {mib_path}")
            return SnmpTester.verify_oid_tree(self.base_oid, mib_path=mib_path)
        
        if force_raw:
            if LOCAL_DEBUG:
                snmp_logger.debug("Running RAW numerical OID verification.")
            return SnmpTester.verify_oid_tree(self.base_oid)
        
        mib_content = self.get_mib_content()
        return SnmpTester.verify_oid_tree(self.base_oid, mib_content=mib_content)



