# Managers/snmp_manager.py
# Author: Anthony P. Kuzub (Refactored)
# Version: 20260323.1700.1
#
# Description: Dedicated orchestrator for SNMP traffic.

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
# --- Specialized Logic Workers ---
from oaComSNMP.Methods.snmp_mib_generator import MibGenerator
from oaComSNMP.Methods.snmp_installer_generator import InstallerGenerator
from oaComSNMP.Workers.snmp_tester import SnmpTester
from oaComSNMP.Methods.snmp_utils import get_snmp_node_id, get_snmp_descriptor, initialize_oid_map
from oaComSNMP.Constants.snmp_constants import BASE_OID, STATE_SYNC_INTERVAL

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from oaLogging.Core.logger import SNMP_LOGGER as snmp_logger

class SNMPManager:
    """
    Manages the SNMP protocol bridge.
    Centralizes all SNMP logic away from the UI.
    """

    def __init__(self, state_cache_manager=None, mqtt_connection_manager=None, run_bridge=True):
        self.run_bridge = run_bridge
        if LOCAL_DEBUG:
            snmp_logger.info("Initializing SNMP Bridge...")
        
        self.state_cache_manager = state_cache_manager
        self.mqtt_connection_manager = mqtt_connection_manager
        self._running = False
        
        self.state_file = str(SNMP_STATE_FILE)
        self.base_oid = BASE_OID
        self._socket_info = "None"
        
        self.tree_builder = SNMPTreeBuilder(base_oid=self.base_oid)
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
                "object_count": len(self.oid_map),
                "bridge_mode": self.run_bridge,
                "mib_path": str(SNMP_CURRENT_MIB)
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
        
        Vocal Policy: Logs callback failures without stopping the notification loop.
        """
        from oaLogging.Entry import vocal_capture
        
        # Take a snapshot of callbacks to avoid holding lock during execution
        with self._state_lock:
            callbacks = list(self._monitor_callbacks)
            
        for cb in callbacks:
            try: 
                # Try full signature first
                cb(direction, oid, value, topic, metadata)
            except TypeError:
                try: 
                    # Fallback for legacy callbacks
                    cb(direction, oid, value, topic)
                except Exception:
                    vocal_capture("SNMP", f"Callback {cb.__name__} failed (Legacy Signature)")
            except Exception:
                vocal_capture("SNMP", f"Callback {cb.__name__} failed (Full Signature)")

    def start(self):
        with self._state_lock:
            if self._running: return
            self._running = True
        
        from oaConfiguration.FileReaders.config_reader import Config
        cfg = Config.get_instance()
        self._socket_info = f"{get_local_ip()}:{cfg.SNMP_PORT} (System Daemon Bridge)"
        
        # ⚡ CRAWLER: Build the metadata map from folders
        initialize_oid_map("oaGuiDefinitions")

        # 🟢 Start Background Monitor
        self._flat_file_thread = threading.Thread(target=self._state_to_file_loop, daemon=True, name="SNMP-FlatFileLoop")
        self._flat_file_thread.start()

        # Start the SnmpStatePersister thread
        self.state_persister.start()

        # Start the SnmpLogMonitor thread
        self.log_monitor.start()

        if self.run_bridge:
            try:
                self.tree_builder.generate_master_script()
                
                # Protocol Router Sync Logic: Listen for remote/local activity
                from oaComBroker.Managers.protocol_router import ProtocolRouter
                ProtocolRouter.get_instance().register_cache_observer(self.handle_protocol_event)
                    
                # Initial MIB Sync
                self.save_current_mib()
                if LOCAL_DEBUG:
                    snmp_logger.success(f"SNMP Bridge Active on {self._socket_info}")
            except Exception as e:
                snmp_logger.error(f"SNMP Bridge Start Failed: {e}")
        else:
            if LOCAL_DEBUG:
                snmp_logger.info("SNMP Bridge: Running in Observer mode.")

    def stop(self):
        with self._state_lock:
            self._running = False
        snmp_logger.warning("SNMP Bridge Offline.")
        
        # Stop the SnmpStatePersister thread
        self.state_persister.stop()

    def publish(self, topic, val, meta=None):
        """
        Explicit publication method called by ProtocolRouter.
        """
        pass

    def handle_protocol_event(self, msg):
        """Callback for all router traffic. No direct action needed as SNMP syncs via file loop."""
        pass

    # --- Worker Delegations ---
    def get_mib_content(self):
        if LOCAL_DEBUG:
            snmp_logger.debug("Generating dynamic MIB content.")
        # Updated to use the new OidMapConverter
        oid_map_data = self.oid_map_converter.build_oid_map()
        with self._state_lock:
            # The build_oid_map method now updates self.oid_map_converter.oid_map directly
            # We retrieve it here to pass to MibGenerator
            return MibGenerator.generate(self.base_oid, self.oid_map_converter.oid_map)

    def save_current_mib(self):
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
        return InstallerGenerator.generate(self.base_oid, self.tree_builder.master_script_path)

    def run_verification(self, mib_path=None, force_raw=True):
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



    def _state_to_file_loop(self):
        while True:
            with self._state_lock:
                if not self._running: break
            
            try:
                if self.state_cache_manager:
                    # 1. Update the OID map (Safe call)
                    # Updated to use the new OidMapConverter
                    self.oid_map_converter.build_oid_map()
                    
                    with self._state_lock:
                        # 2. Get OID map data for processing
                        # The build_oid_map method updates self.oid_map_converter.oid_map directly
                        oid_data_items = list(self.oid_map_converter.oid_map.items())
                        # Take a cache snapshot for consistent processing in this loop
                        try:
                            cache_snapshot = self.state_cache_manager.cache.copy()
                        except AttributeError:
                            cache_snapshot = dict(self.state_cache_manager.cache)

                    sorted_items = sorted(oid_data_items, key=lambda x: x[1]['topic'])
                    lines = []
                    for oid, data in sorted_items:
                        topic = data['topic']
                        payload = cache_snapshot.get(topic, {})
                        
                        # ⚡ ANTI-FEEDBACK SPEC: The Golden Rule for Transports
                        msg_type = payload.get("msg_type")
                        origin_source = payload.get("origin_source")
                        is_settled = payload.get("is_settled", False)
                        
                        # 1. If it's LINK_FEEDBACK, we only push to SNMP if it's SETTLED (confirmed state)
                        if msg_type == "LINK_FEEDBACK" and not is_settled:
                            continue
                            
                        # 2. If the origin_source is SNMP, don't send it back to SNMP
                        if origin_source == "SNMP":
                            continue

                        val_str = data['val']
                        lines.append(f"{oid}:{val_str}")
                        self._notify_monitor("TX_DUMP", oid, val_str, topic, data)
                    
                    if self.run_bridge:
                        with self._state_lock:
                            current_count = len(self.oid_map_converter.oid_map)
                        
                        if current_count > 0 and current_count != self._last_topic_count:
                            if LOCAL_DEBUG:
                                snmp_logger.info(f"Tree Expansion ({self._last_topic_count} -> {current_count}). Syncing MIB...")
                            self.save_current_mib()
                            with self._state_lock:
                                self._last_topic_count = current_count

                        if lines:
                            def oid_key(oid_line):
                                oid_str = oid_line.split(':')[0]
                                return [int(x) for x in oid_str.strip('.').split('.')]
                            lines.sort(key=oid_key)
                            
                            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
                            temp_path = self.state_file + ".tmp"
                            with open(temp_path, "w", encoding="utf-8") as f:
                                f.write("\n".join(lines) + "\n")
                            
                            if os.path.exists(temp_path):
                                os.replace(temp_path, self.state_file)
                                os.chmod(self.state_file, 0o644)
            except Exception as e:
                snmp_logger.error(f"State-to-File error: {e}")
            
            time.sleep(STATE_SYNC_INTERVAL)


