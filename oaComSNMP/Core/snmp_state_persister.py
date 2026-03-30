# oaComSNMP/Core/snmp_state_persister.py
#
# Manages the periodic persistence of SNMP state to a file.
#
# Author: Anthony Peter Kuzub (Contributor to this project)
# Blog: www.Like.audio
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260329.1020.1

import os
import time
import threading
from loguru import logger

# Import necessary constants and logging
from oaOchestration.Constants.project_paths import SNMP_STATE_FILE
from oaLogging.Core.logger import SNMP_LOGGER as snmp_logger 
from oaComSNMP.Constants.snmp_constants import THREAD_JOIN_TIMEOUT, LOG_POLLING_INTERVAL, STATE_SYNC_INTERVAL

# LOCAL_DEBUG can be set or passed if needed
LOCAL_DEBUG = False

class SnmpStatePersister:
    """
    Handles the background persistence of SNMP state (OID map) to a file.
    This class is designed to be managed by a parent class (e.g., SNMPManager).
    """

    def __init__(self, state_cache_manager, thread_lock: threading.RLock, notify_monitor_callback, run_bridge: bool, base_oid: str, oid_map_converter):
        """
        Initializes the state persister.
        
        Args:
            state_cache_manager: Manager providing access to the state cache.
            thread_lock: The RLock used by the calling manager for thread-safe access.
            notify_monitor_callback: Callback function to notify about SNMP activity.
            run_bridge: Flag indicating if the SNMP bridge is active.
            base_oid: The base OID for SNMP data.
            oid_map_converter: The converter instance providing the OID map.
        """
        self.state_cache_manager = state_cache_manager
        self._state_lock = thread_lock # Use the provided lock for external state access
        self._notify_monitor = notify_monitor_callback
        self.run_bridge = run_bridge
        self.base_oid = base_oid
        self.oid_map_converter = oid_map_converter # Reference to the converter

        self._running = True # Internal flag to control the loop
        self._thread = None

        self.state_file = str(SNMP_STATE_FILE)
        self._last_topic_count = 0

    def start(self):
        """Starts the background thread for state persistence."""
        if self._thread and self._thread.is_alive():
            snmp_logger.warning("SnmpStatePersister: Thread already running.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._persistence_loop, daemon=True, name="SNMP-StatePersistenceLoop")
        self._thread.start()
        snmp_logger.info("SnmpStatePersister: Started background persistence thread.")

    def stop(self):
        """Signals the background thread to stop and waits for it to terminate."""
        self._running = False
        if self._thread and self._thread.is_alive():
            snmp_logger.info("SnmpStatePersister: Stopping background persistence thread...")
            self._thread.join(timeout=THREAD_JOIN_TIMEOUT) # Wait for thread to finish
            if self._thread.is_alive():
                snmp_logger.warning("SnmpStatePersister: Thread did not terminate gracefully.")
        snmp_logger.info("SnmpStatePersister: Stopped.")

    def _persistence_loop(self):
        """The main loop for periodically saving SNMP state to a file."""
        while self._running:
            try:
                if not self.state_cache_manager:
                    snmp_logger.warning("SnmpStatePersister: State cache manager is not available. Skipping persistence.")
                    time.sleep(STATE_SYNC_INTERVAL)
                    continue

                # Safely get OID map data for processing from the converter
                oid_map_data = []
                cache_snapshot = {}

                # Accessing state and converter requires the lock
                with self._state_lock: # Use the lock provided by the manager
                    if not self.state_cache_manager.cache: # Skip if cache is empty
                        time.sleep(STATE_SYNC_INTERVAL)
                        continue

                    # 1. Create a snapshot of the current state cache
                    try:
                        cache_snapshot = self.state_cache_manager.cache.copy()
                    except AttributeError:
                        cache_snapshot = dict(self.state_cache_manager.cache)

                    # 2. ⚡ REFRESH: Rebuild the OID map from this specific snapshot
                    self.oid_map_converter.build_oid_map(cache_snapshot=cache_snapshot)

                    # 3. Extract the items for iteration outside the lock
                    oid_map_data = list(self.oid_map_converter.oid_map.items())

                sorted_items = sorted(oid_map_data, key=lambda x: x[1]['topic'])
                lines = []

                for oid, data in sorted_items:
                    topic = data['topic']
                    # Use the snapshot we took inside the lock for consistency
                    payload = cache_snapshot.get(topic, {}) 
 # Get payload for filtering if needed

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
                    # Notify monitor about outgoing data
                    self._notify_monitor("TX_DUMP", oid, val_str, topic, data)
                
                # Only perform file operations if the bridge is active and there's data
                if self.run_bridge and lines:
                    current_count = 0
                    with self._state_lock: # Access converter's map for count
                        current_count = len(self.oid_map_converter.oid_map) 
                    
                    # Check if OID map has grown and sync MIB if necessary
                    # This logic might need re-evaluation if MIB sync should be separate.
                    # Keeping it here for structural extraction.
                    if current_count > 0 and current_count != self._last_topic_count:
                        if LOCAL_DEBUG:
                            snmp_logger.info(f"SnmpStatePersister: Tree Expansion ({self._last_topic_count} -> {current_count}). MIB sync might be needed.")
                        # Note: MIB saving logic (`save_current_mib`) requires SNMPManager context,
                        # so it cannot be called directly here. It's called in SNMPManager.start and
                        # potentially elsewhere. This extraction might need further refinement.
                        with self._state_lock:
                            self._last_topic_count = current_count

                    # Sort lines for consistent file writing
                    def oid_key(oid_line):
                        oid_str = oid_line.split(':')[0]
                        return [int(x) for x in oid_str.strip('.').split('.')]
                    lines.sort(key=oid_key)
                    
                    # Write to a temporary file and then replace
                    os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
                    temp_path = self.state_file + ".tmp"
                    with open(temp_path, "w", encoding="utf-8") as f:
                        f.write("\n".join(lines) + "\n")
                    
                    if os.path.exists(temp_path):
                        os.replace(temp_path, self.state_file)
                        os.chmod(self.state_file, 0o644) # Set appropriate permissions
                        if LOCAL_DEBUG:
                            snmp_logger.debug(f"SnmpStatePersister: State persisted to {self.state_file}")

            except Exception as e:
                snmp_logger.error(f"SnmpStatePersister: Persistence loop error: {e}")
            
            time.sleep(STATE_SYNC_INTERVAL) # Periodically check for updates
