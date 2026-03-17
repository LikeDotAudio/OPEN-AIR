# workers/Command_Router/AES70/aes70.py
#
# Dedicated orchestrator for AES70 / OCA (Open Control Architecture) traffic.
# This manager acts as a bridge between the internal state system and the AES70 network.
#
# Author: Anthony P. Kuzub(Refactored)
# Version 20260308.Harden.1

import threading
import time
# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from loguru import logger
from managers.configini.config_reader import Config

app_constants = Config.get_instance()
# ⚡ SUBSYSTEM: AES70_BRIDGE
aes_logger = logger.bind(subsystem="AES70_BRIDGE", category="COMM")

class AES70Manager:
    """
    Manages AES70 / OCA connectivity.
    Centralizes all OCA logic away from the UI.
    """

    def __init__(self, state_cache_manager=None, run_bridge=True):
        self.run_bridge = run_bridge
        self.state_cache_manager = state_cache_manager
        self._running = False
        self._discovered_devices = []
        
        # Monitor callbacks for GUI
        self._monitor_callbacks = []
        
        if LOCAL_DEBUG:
            aes_logger.info("📻🛠️🔗 [AES70] Initializing AES70 Bridge...")
        
        # Link to state cache if provided
        if state_cache_manager:
            self.state_cache_manager.register_cache_observer(self._on_state_update)
            if LOCAL_DEBUG:
                aes_logger.debug("📻🛠️🔗 [AES70] Bridge linked to State Cache.")

    def add_monitor_callback(self, callback):
        self._monitor_callbacks.append(callback)

    def remove_monitor_callback(self, callback):
        if callback in self._monitor_callbacks:
            self._monitor_callbacks.remove(callback)

    def _notify_monitor(self, event_type, data):
        for cb in self._monitor_callbacks:
            try: cb(event_type, data)
            except: pass

    def start(self):
        if self._running: return
        self._running = True
        
        if self.run_bridge:
            try:
                # Observer is already added in __init__
                if LOCAL_DEBUG:
                    aes_logger.success("✅✅✅ [SUCCESS] AES70 Bridge Active.")
            except Exception as e:
                # Gravity of Errors: Non-gated failure reporting.
                aes_logger.error(f"📻🚫🛑 [AES70] ERROR: AES70 Bridge Start "
                                 f"Failed: {e}")
        else:
            if LOCAL_DEBUG:
                aes_logger.info("📻🛠️👁️ [AES70] Bridge: Running in Observer "
                                "mode.")

    def _on_state_update(self, topic, payload):
        """Observer for all state changes from the StateRegistry."""
        if not self._running: return

        # ⚡ LOGGING: High-signal Firehose style
        if LOCAL_DEBUG:
            aes_logger.debug(f"📻📡📥 [AES70] Intercepted State Change "
                             f"-> {topic}: {payload}")
        self._notify_monitor("STATE_SYNC", f"{topic} = {payload}")

    def stop(self):
        self._running = False
        if LOCAL_DEBUG:
            aes_logger.warning("📻🔌🛑 [AES70] AES70 Bridge Offline.")

    def trigger_scan(self):
        """Logic-only network scan for OCA devices."""
        if LOCAL_DEBUG:
            aes_logger.info("📻🔍📡 [AES70] Initiating AES70 Network Scan...")
        # Mock scan for now
        time.sleep(0.5)
        self._discovered_devices = ["Mock_OCA_Device_1", "Mock_OCA_Device_2"]
        if LOCAL_DEBUG:
            aes_logger.success(f"✅✅✅ [SUCCESS] Scan Complete. Found "
                               f"{len(self._discovered_devices)} devices.")
        self._notify_monitor("SCAN_COMPLETE", self._discovered_devices)
        return self._discovered_devices
