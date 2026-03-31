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
# Version 20260330.1600.1

import os
import time
import threading
from loguru import logger

# Import necessary constants and logging
from oaOchestration.Constants.project_paths import SNMP_SET_LOG
from oaLogging.Core.logger import SNMP_LOGGER as snmp_logger
from oaComSNMP.Constants.snmp_constants import THREAD_JOIN_TIMEOUT, LOG_POLLING_INTERVAL, MIN_LOG_PARTS
from oaLogging.Methods.matrix_gate import matrix_log

# Import ProtocolRouter and other dependencies
from oaComBroker.Core.protocol_router.manager import ProtocolRouter 

# LOCAL_DEBUG can be set or passed if needed

class SnmpLogMonitor:
    """
    Monitors the SNMP SET log file for incoming commands and translates them
    into system events via the Protocol Router and State Cache.
    """

    def __init__(self, state_cache_manager, thread_lock: threading.RLock, notify_monitor_callback, running_flag_getter):
        """
        Initializes the log monitor.
        """
        self.state_cache_manager = state_cache_manager
        self._state_lock = thread_lock 
        self._notify_monitor = notify_monitor_callback
        self._running_flag_getter = running_flag_getter 

        self._thread = None
        self.log_file = str(SNMP_SET_LOG)

    def start(self):
        """Starts the background thread for log monitoring."""
        if self._thread and self._thread.is_alive():
            snmp_logger.warning("SnmpLogMonitor: Thread already running.")
            return

        self._thread = threading.Thread(target=self._log_monitoring_loop, daemon=True, name="SNMP-LogMonitorLoop")
        self._thread.start()
        matrix_log("comms", "snmp", "start", 
                   "SnmpLogMonitor: Started background log monitoring thread.", "INFO")

    def stop(self):
        """Signals the background thread to stop and waits for it to terminate."""
        if self._thread and self._thread.is_alive():
            matrix_log("comms", "snmp", "stop", 
                       "SnmpLogMonitor: Stopping background log monitoring thread...", "INFO")
            self._thread.join(timeout=THREAD_JOIN_TIMEOUT)
            if self._thread.is_alive():
                snmp_logger.warning("SnmpLogMonitor: Thread did not terminate gracefully.")
        matrix_log("comms", "snmp", "stop", "SnmpLogMonitor: Stopped.", "INFO")

    def _log_monitoring_loop(self):
        """The main loop for monitoring the SNMP SET log file."""
        while self._running_flag_getter():
            try:
                if os.path.isfile(self.log_file) and os.path.getsize(self.log_file) > 0:
                    with open(self.log_file, "r+", encoding="utf-8") as f:
                        lines = f.readlines()
                        for line in lines:
                            parts = line.split()
                            if len(parts) >= MIN_LOG_PARTS and parts[0] == "-s":
                                oid, val = parts[1], parts[2]
                                
                                matrix_log("comms", "snmp", "_log_monitoring_loop", 
                                           f"SnmpLogMonitor: RX SET: {oid} -> {val}", "DEBUG")
                                
                                meta = {
                                    "msg_type": "SPLICE_ACTION",
                                    "origin_source": "SNMP_SET"
                                }

                                ProtocolRouter.get_instance().ingest("SNMP", oid, val, meta)

                                topic = f"OPEN-AIR/SNMP/{oid}"
                                self._notify_monitor("RX_SET", oid, val, topic, meta)
                                if self.state_cache_manager:
                                    self.state_cache_manager.handle_external_update(topic, val, source="SNMP", metadata=meta)
                        f.seek(0)
                        f.truncate()
            except FileNotFoundError:
                pass
            except Exception as e:
                snmp_logger.error(f"SnmpLogMonitor: Log monitoring loop error: {e}")
            
            time.sleep(LOG_POLLING_INTERVAL)
