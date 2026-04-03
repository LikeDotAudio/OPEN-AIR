# Core/protocol_router/router.py
#
# The Hub and Orchestrator for the modular Protocol Router engine.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20260331.2230.1

import queue
import threading
import time
import concurrent.futures
from .constants import LOCAL_DEBUG, app_constants
from oaLogging.Core.logger import router_logger, logger
from oaLogging.Methods.matrix_gate import matrix_log
from oaConfiguration.Entry import Config

from oaComBroker.Methods.oaCoreRouter_rs.compiler_hook import ensure_compiled
try:
    ensure_compiled()
    from oacorerouter_rs import CoreRouter as RustCoreRouter
except ImportError as e:
    logger.critical("🚀❌ [FATAL] Rust Core Router module missing. Pure Rust mode is mandatory.")
    raise e

# Modular Subsystem Imports
from .ingest import normalize_and_ingest, create_silent_msg
from .dispatch import dispatch_message
from .settle import SettleManager
from .strategy import calculate_strategy, calculate_ui_tags
from .dpi import investigate_packet
from .monitor import Monitor

class ProtocolRouter:
    """
    Singleton Hub for all command and telemetry traffic.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        
        # ⚡ STABILITY OVERRIDE: Use Python native queues for complex object passing
        # Rust core router is reserved for high-speed numeric/primitive paths.
        self.inbound_queue = queue.Queue()
        self.outbound_queue = queue.Queue()
        
        # ⚡ RUST NATIVE ACCELERATION: Initialize the Rust core router if available
        self.rust_router = RustCoreRouter()

        self._running = False
        self._dispatch_threads = 4
        self._executor = None
        
        self.mib_cache = {}
        self.osc_cache = {}
        
        self.monitor = Monitor(self.GUID)
        self.settle_manager = SettleManager(self.ingest)
        
        self.mqtt_manager = None
        self.splinker_manager = None
        self.osc_manager = None
        self.midi_manager = None
        self.snmp_manager = None
        self.smpte2138_manager = None
        
        self.state_cache = None
        self.is_active = True 

    @property
    def firehose(self):
        return self.monitor.firehose

    @property
    def GUID(self):
        return app_constants.FULL_INSTANCE_ID

    @classmethod
    def get_instance(cls, force_reload=False):
        with cls._lock:
            if force_reload:
                cls._instance = None
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def start(self):
        if self._running: return
        self._running = True
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=self._dispatch_threads, thread_name_prefix="Router-Dispatch")
        
        threading.Thread(target=self._ingest_loop, daemon=True, name="Router-Ingest").start()
        threading.Thread(target=self._dispatch_loop, daemon=True, name="Router-Dispatch-Master").start()
        
        matrix_log("core", "router", "start", f"▶️▶️▶️ [START] Protocol Router Active (GUID: {self.GUID}).", "SUCCESS")

    def stop(self):
        self._running = False
        if self._executor: self._executor.shutdown(wait=False)
        matrix_log("core", "router", "stop", "⏹️ [STOP] Protocol Router Offline.", "WARNING")

    def set_active_state(self, active):
        if self.is_active == active: return
        self.is_active = active
        
        state_label = "PRIMARY" if active else "SHADOW"
        matrix_log("core", "router", "set_active_state", f"🔄 [FAILOVER] Protocol Router transitioning to {state_label} mode.", "INFO")
        
        managers = [self.osc_manager, self.midi_manager, self.snmp_manager, self.smpte2138_manager]
        for mgr in managers:
            if not mgr: continue
            try:
                if active:
                    if hasattr(mgr, "start"): mgr.start()
                else:
                    if hasattr(mgr, "stop"): mgr.stop()
            except Exception as e:
                matrix_log("core", "router", "set_active_state", f"❌ [FAILOVER] Error transitioning manager: {e}", "ERROR")

    def set_mqtt_manager(self, m): self.mqtt_manager = m
    def set_splinker_manager(self, m): self.splinker_manager = m
    def set_osc_manager(self, m): self.osc_manager = m
    def set_midi_manager(self, m): self.midi_manager = m
    def set_snmp_manager(self, m): self.snmp_manager = m
    def set_smpte2138_manager(self, m): self.smpte2138_manager = m
    def set_state_cache(self, c): self.state_cache = c

    def get_dpi_report(self, utp):
        """
        Placeholder method to get DPI report.
        Implement actual logic for retrieving DPI report for a given UTP.
        """
        # In a real fix, this would fetch and return relevant data.
        # For now, it prevents the AttributeError.
        print(f"DEBUG: ProtocolRouter.get_dpi_report called for UTP: {utp}") # For debugging
        return {"report": "placeholder_dpi_report_data", "utp": utp} # Example placeholder return

    def publish_splink(self, src, dest, s_val=None, d_val=None):
        """
        Placeholder method to publish a splink.
        Implement actual logic for publishing splink with provided parameters.
        """
        # In a real fix, this would establish or manage the splink connection.
        # For now, it prevents the AttributeError.
        print(f"DEBUG: ProtocolRouter.publish_splink called: src={src}, dest={dest}, s_val={s_val}, d_val={d_val}") # For debugging
        return True # Example placeholder return

    def register_cache_observer(self, cb): self.monitor.register_cache_observer(cb)
    def unregister_cache_observer(self, cb): self.monitor.remove_observer(cb)
    def remove_observer(self, cb): self.monitor.remove_observer(cb)

    def ingest(self, transport_source, topic, value, metadata=None):
        normalize_and_ingest(
            transport_source, topic, value, metadata, 
            self.GUID, self.settle_manager, self.inbound_queue,
            self._ingest_silent, self.state_cache, self.rust_router
        )

    def _ingest_silent(self, transport_source, topic, value, meta):
        msg = create_silent_msg(transport_source, topic, value, meta, self.GUID, self.rust_router)
        self.inbound_queue.put(msg)

    def _fetch_next_inbound(self):
        try:
            return self.inbound_queue.get(timeout=0.1)
        except queue.Empty:
            return None

    def _process_message_pipeline(self, msg):
        investigate_packet(msg, self.mib_cache)
        
        strategy = calculate_strategy(msg)
        msg["strategy"] = strategy

        if self.splinker_manager:
            try: self.splinker_manager.process_router_event(msg)
            except Exception as e: 
                matrix_log("core", "router", "_process_pipeline", f"🔗🚫🛑 [ROUTER] Splinker Error: {e}", "ERROR")

        msg["ui_tags"] = calculate_ui_tags(msg, self.GUID)
        
        self.monitor.append_to_firehose(msg)
        self.monitor.broadcast_to_observers(msg)
        
        val_str = str(msg['val'])[:100] + ("..." if len(str(msg['val'])) > 100 else "")
        matrix_log("core", "router", "_process_pipeline", f"📥📡📤 [ROUTER] {strategy} >> {msg['topic']}: {val_str}", "DEBUG")
        
        self._dispatch_by_strategy(strategy, msg)

    def _dispatch_by_strategy(self, strategy, msg):
        if "IGNORE" not in strategy:
            self.outbound_queue.put(msg)

    def _ingest_loop(self):
        while self._running:
            try:
                msg = self._fetch_next_inbound()
                if msg is None: continue
                self._process_message_pipeline(msg)
            except Exception as e: 
                matrix_log("core", "router", "_ingest_loop", f"📥🚫🛑 [ROUTER] Ingest Error: {e}", "ERROR")

    def _dispatch_loop(self):
        while self._running:
            try:
                try:
                    msg = self.outbound_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Prepare manager registry for the dispatcher
                managers = {
                    "mqtt": self.mqtt_manager,
                    "osc": self.osc_manager,
                    "midi": self.midi_manager,
                    "snmp": self.snmp_manager,
                    "smpte2138": self.smpte2138_manager
                }
                
                self._executor.submit(
                    dispatch_message, 
                    msg, managers
                )
            except Exception as e:
                matrix_log("core", "router", "_dispatch_loop", f"📤🚫🛑 [ERROR] Dispatch Loop Error: {e}", "ERROR")

    def publish_splinker_direct(self, s_topic, d_topic, s_val=None, d_val=None):
        payload = {"source": s_topic, "dest": d_topic, "source_val": s_val, "dest_val": d_val}
        self.ingest("GUI", "OPEN-AIR/System/Control/Splinker/DirectCreate", payload)
        return True