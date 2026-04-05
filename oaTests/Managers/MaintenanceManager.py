# oaTests/Managers/MaintenanceManager.py
# Author: Gemini CLI
# Version: 20260404.1400.1
#
# Description: Orchestrates cleanup and maintenance tasks for the OPEN-AIR test suite.

import os
import threading
from datetime import datetime
from oaTests.Workers.CleanupApps.Clear_logs import cleanup_logs
from oaTests.Workers.CleanupApps.ClearMQTT import MQTTSweeper
from oaTests.Workers.CleanupApps.Clear_flamegraph import cleanup_flamegraph
from oaTests.Workers.CleanupApps.Clear_audits import cleanup_audits
from oaTests.Workers.CleanupApps.Clear_reports import cleanup_reports
from oaTests.Workers.CleanupApps.Clear_cache import purge_cache
from oaTests.Workers.CleanupApps.Clear_JsonLines import cleanup_jsonlines

class MaintenanceManager:
    """Manages system-wide maintenance and cleanup operations."""

    def __init__(self, project_root, log_callback):
        self.project_root = project_root
        self.log_callback = log_callback

    def _run_task(self, task_func, start_msg, end_msg, *args):
        self.log_callback(start_msg)
        def thread_wrapper():
            try:
                task_func(*args)
                self.log_callback(end_msg)
            except Exception as e:
                self.log_callback(f"💥 [ERROR] Maintenance task failed: {e}")
        
        thread = threading.Thread(target=thread_wrapper, daemon=True)
        thread.start()

    def clear_logs(self):
        self._run_task(cleanup_logs, "🧹 [CLEANUP] Purging all application logs...", "✨ [SUCCESS] Logs cleared.", None)

    def clear_audits(self):
        self._run_task(cleanup_audits, "🧹 [CLEANUP] Purging all system audit results...", "✨ [SUCCESS] Audits cleared.")

    def clear_reports(self):
        self._run_task(cleanup_reports, "🧹 [CLEANUP] Purging old reports (preserving latest)...", "✨ [SUCCESS] Report cleanup complete.")

    def clear_jsonlines(self):
        self._run_task(cleanup_jsonlines, "🧹 [CLEANUP] Purging all JSON Lines logs...", "✨ [SUCCESS] JsonLines cleared.")

    def clear_mqtt(self):
        self.log_callback("🧹 [CLEANUP] Wiping the MQTT topic tree...")
        def task():
            try:
                sweeper = MQTTSweeper("localhost", 1883, "OPEN-AIR")
                sweeper.sweep()
                self.log_callback("✨ [SUCCESS] MQTT topic tree sanitized.")
            except Exception as e:
                self.log_callback(f"💥 [ERROR] MQTT sweep failed: {e}")
        
        thread = threading.Thread(target=task, daemon=True)
        thread.start()

    def clear_flamegraph(self):
        self._run_task(cleanup_flamegraph, "🧹 [CLEANUP] Deleting flame graph artifacts...", "✨ [SUCCESS] Flame graph data purged.")

    def clear_cache(self):
        self._run_task(purge_cache, "🌪️ [PURGE] Nuking local cache and running state...", "✨ [SUCCESS] Cache purged and structure re-initialized.")
