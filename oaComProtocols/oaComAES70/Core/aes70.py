# Core/aes70.py
# Author: Anthony P. Kuzub(Refactored)
# Version: 20260308.Harden.1
#
# Description: Dedicated orchestrator for AES70 / OCA (Open Control Architecture) traffic.

import threading
import time
# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from oaLogging.Core.logger import get_logger
from oaConfigurationManager.FileReaders.config_reader import Config
from oaComProtocols.oaComAES70.Methods.aes70_parser import OcaParser

app_constants = Config.get_instance()
# ⚡ SUBSYSTEM: AES70_BRIDGE
aes_logger = get_logger("AES70")

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
        self._parser = OcaParser()
        
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

    def ingest_pdu(self, raw_data):
        """Processes raw bytes from the network socket using the high-performance parser."""
        if not raw_data: return None
        
        pdu = self._parser.decode(raw_data)
        if not pdu:
            if LOCAL_DEBUG:
                aes_logger.error("📻🚫🛑 [AES70] Malformed OCP.1 PDU.")
            return None
        
        if LOCAL_DEBUG:
            aes_logger.debug(f"📻📡📥 [AES70] Inbound PDU: Version {pdu['version']}, {pdu['message_count']} messages.")
        
        # Process individual messages (Dispatching to state cache, etc.)
        for message in pdu['messages']:
            self._handle_message(message)
            
        return pdu

    def _handle_message(self, message):
        """Dispatches an OcaMessage to the appropriate handler."""
        # This is where the MethodID and ONo mapping happens
        if LOCAL_DEBUG:
            aes_logger.debug(f"📻📡📥 [AES70] MSG: Handle {message['handle']} -> ONo {message['target_ono']} Method {message['method_id']}")
        
        # ⚡ Example: Handle specific method/ONo combinations
        # If ONo is 1 (DeviceManager) and Method is some Set property...
        pass

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
