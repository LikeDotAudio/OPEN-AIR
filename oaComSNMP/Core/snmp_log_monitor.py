# oaComSNMP/Core/snmp_log_monitor.py
#
# Monitors the SNMP SET log file for incoming commands and dispatches them.
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
# Version 20260329.1015.1

import os
import time
import threading
from loguru import logger

# Import necessary constants and logging
from oaOchestration.Constants.project_paths import SNMP_SET_LOG
from oaLogging.Core.logger import SNMP_LOGGER as snmp_logger
from oaComSNMP.Constants.snmp_constants import THREAD_JOIN_TIMEOUT, LOG_POLLING_INTERVAL, MIN_LOG_PARTS

# Import ProtocolRouter and other dependencies
from oaComBroker.Core.protocol_router.manager import ProtocolRouter 

# LOCAL_DEBUG can be set or passed if needed
LOCAL_DEBUG = False

class SnmpLogMonitor:
    """
    Monitors the SNMP SET log file for incoming commands and translates them
    into system events via the Protocol Router and State Cache.
    This class is designed to be managed by a parent class (e.g., SNMPManager).
    """

    def __init__(self, state_cache_manager, thread_lock: threading.RLock, notify_monitor_callback, running_flag_getter):
        """
        Initializes the log monitor.
        
        Args:
            state_cache_manager: Manager providing access to the state cache.
            thread_lock: The RLock used by the calling manager for thread-safe access.
            notify_monitor_callback: Callback function to notify about SNMP activity.
            running_flag_getter: A function that returns the current running state of the manager.
        """
        self.state_cache_manager = state_cache_manager
        self._state_lock = thread_lock # Use the provided lock for external state access
        self._notify_monitor = notify_monitor_callback
        self._running_flag_getter = running_flag_getter # Function to check if manager is running

        self._thread = None
        self.log_file = str(SNMP_SET_LOG)

    def start(self):
        """Starts the background thread for log monitoring."""
        if self._thread and self._thread.is_alive():
            snmp_logger.warning("SnmpLogMonitor: Thread already running.")
            return

        self._thread = threading.Thread(target=self._log_monitoring_loop, daemon=True, name="SNMP-LogMonitorLoop")
        self._thread.start()
        snmp_logger.info("SnmpLogMonitor: Started background log monitoring thread.")

    def stop(self):
        """Signals the background thread to stop and waits for it to terminate."""
        if self._thread and self._thread.is_alive():
            snmp_logger.info("SnmpLogMonitor: Stopping background log monitoring thread...")
            self._thread.join(timeout=THREAD_JOIN_TIMEOUT) # Wait for thread to finish
            if self._thread.is_alive():
                snmp_logger.warning("SnmpLogMonitor: Thread did not terminate gracefully.")
        snmp_logger.info("SnmpLogMonitor: Stopped.")

    def _log_monitoring_loop(self):
        """The main loop for monitoring the SNMP SET log file."""
        while self._running_flag_getter(): # Check if the manager is still running
            try:
                if os.path.isfile(self.log_file) and os.path.getsize(self.log_file) > 0:
                    with open(self.log_file, "r+", encoding="utf-8") as f:
                        lines = f.readlines()
                        for line in lines:
                            parts = line.split()
                            # Expected format: "-s <oid> <value>"
                            if len(parts) >= MIN_LOG_PARTS and parts[0] == "-s":
                                oid, val = parts[1], parts[2] # Assuming value is the third part
                                
                                if LOCAL_DEBUG:
                                    snmp_logger.debug(f"SnmpLogMonitor: RX SET: {oid} -> {val}")
                                
                                # ⚡ ANTI-FEEDBACK SPEC: Define identity at transport ingress
                                # We use SNMP_SET instead of SNMP to distinguish from 
                                # mirrored state and allow it to pass through the persister 
                                # filter if necessary, or just to avoid self-reflection loops.
                                meta = {
                                    "msg_type": "SPLICE_ACTION",
                                    "origin_source": "SNMP_SET"
                                }

                                # Ingest the command via Protocol Router
                                ProtocolRouter.get_instance().ingest("SNMP", oid, val, meta)

                                # Notify monitors and update state cache
                                topic = f"OPEN-AIR/SNMP/{oid}" # Construct topic
                                self._notify_monitor("RX_SET", oid, val, topic, meta)
                                if self.state_cache_manager:
                                    self.state_cache_manager.handle_external_update(topic, val, source="SNMP", metadata=meta)
                        f.seek(0) # Rewind to beginning of file
                        f.truncate() # Clear the file content after processing
            except FileNotFoundError:
                # Log this if the file might not exist initially
                if LOCAL_DEBUG:
                    snmp_logger.debug("SnmpLogMonitor: Log file not found yet. Waiting...")
            except Exception as e:
                snmp_logger.error(f"SnmpLogMonitor: Log monitoring loop error: {e}")
            
            time.sleep(LOG_POLLING_INTERVAL) # Poll frequently for new log entries
