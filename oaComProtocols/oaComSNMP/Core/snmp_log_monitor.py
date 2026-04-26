# oaComProtocols.oaComSNMP/Core/snmp_log_monitor.py
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
import threading
import time

from oaComProtocols.oaComSNMP.Constants.snmp_constants import LOG_POLLING_INTERVAL, MIN_LOG_PARTS, THREAD_JOIN_TIMEOUT
from oaLogging.Core.logger import SNMP_LOGGER as snmp_logger
from oaLogging.Methods.matrix_gate import matrix_log

# Import necessary constants and logging
from oaOchestration.Constants.project_paths import SNMP_SET_LOG


class SnmpLogMonitor:
    """
    Monitors the SNMP SET log file for incoming commands and translates them
    into system events via the direct MQTT client.
    """

    def __init__(self, thread_lock: threading.RLock, notify_monitor_callback, running_flag_getter, mqtt_client=None):
        """
        Initializes the log monitor.
        """
        self._state_lock = thread_lock
        self._notify_monitor = notify_monitor_callback
        self._running_flag_getter = running_flag_getter
        self._mqtt_client = mqtt_client

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
                                oid, value = parts[1], parts[2]

                                matrix_log("comms", "snmp", "_log_monitoring_loop",
                                           f"SnmpLogMonitor: RX SET: {oid} -> {value}", "DEBUG")

                                meta = {
                                    "message_type": "SPLICE_ACTION",
                                    "origin_source": "oaComSNMP"
                                }

                                if self._mqtt_client:
                                    topic = f"OPEN-AIR/SNMP/gui_out/{oid}"
                                    self._mqtt_client.publish(topic, {"value": value, "origin_source": "oaComSNMP"})

                                self._notify_monitor("RX_SET", oid, value, None, meta)
                        f.seek(0)
                        f.truncate()
            except FileNotFoundError:
                pass
            except Exception as e:
                snmp_logger.error(f"SnmpLogMonitor: Log monitoring loop error: {e}")

            time.sleep(LOG_POLLING_INTERVAL)
