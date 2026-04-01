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

try:
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

    class QueueBridge:
        def __init__(self, rust_router):
            self.rust_router = rust_router
        def put(self, msg):
            self.rust_router.push_inbound(msg)

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        
        try:
            self.rust_router = RustCoreRouter()
            matrix_log("core", "router", "__init__", "🚀 Using HIGH-PERFORMANCE RUST core router.", "DEBUG")
        except Exception as e:
            matrix_log("core", "router", "__init__", f"🚀❌ [FATAL] Rust Router init failed: {e}", "ERROR")
            raise e

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
    def get_instance(cls):
        with cls._lock:
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

    def register_cache_observer(self, cb): self.monitor.register_cache_observer(cb)
    def unregister_cache_observer(self, cb): self.monitor.remove_observer(cb)
    def remove_observer(self, cb): self.monitor.remove_observer(cb)

    def ingest(self, transport_source, topic, value, metadata=None):
        bridge = self.QueueBridge(self.rust_router)

        normalize_and_ingest(
            transport_source, topic, value, metadata, 
            self.GUID, self.settle_manager, bridge,
            self._ingest_silent, self.state_cache
        )

    def _ingest_silent(self, transport_source, topic, value, meta):
        msg = create_silent_msg(transport_source, topic, value, meta, self.GUID)
        self.rust_router.push_inbound(msg)

    def _fetch_next_inbound(self):
        msg = self.rust_router.pop_inbound()
        if msg is None: time.sleep(0.001)
        return msg

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
            self.rust_router.push_outbound(msg)

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
                msg = self.rust_router.pop_outbound()
                if msg is None:
                    time.sleep(0.001)
                    continue
                
                self._executor.submit(
                    dispatch_message, 
                    msg, self.mqtt_manager, self.osc_manager, self.midi_manager
                )
            except Exception as e:
                matrix_log("core", "router", "_dispatch_loop", f"📤🚫🛑 [ERROR] Dispatch Loop Error: {e}", "ERROR")

    def publish_splinker_direct(self, s_topic, d_topic, s_val=None, d_val=None):
        payload = {"source": s_topic, "dest": d_topic, "source_val": s_val, "dest_val": d_val}
        self.ingest("GUI", "OPEN-AIR/System/Control/Splinker/DirectCreate", payload)
        return True
