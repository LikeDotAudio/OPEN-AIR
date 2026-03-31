# Core/protocol_router/router.py
#
# The Hub and Orchestrator for the modular Protocol Router engine.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260330.1600.1

import queue
import threading
import concurrent.futures
from .constants import LOCAL_DEBUG, app_constants
from oaLogging.Core.logger import router_logger
from oaLogging.Methods.matrix_gate import matrix_log

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
        
        self.inbound_queue = queue.Queue()
        self.outbound_queue = queue.Queue()
        
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
        return app_constants.INSTANCE_GUID

    @classmethod
    def get_instance(cls, force_reload=False):
        if cls._instance is not None and not force_reload:
            return cls._instance

        with cls._lock:
            if cls._instance is None or force_reload:
                if force_reload and cls._instance:
                    matrix_log("core", "router", "get_instance", "📜📑💻 [CONFIG] Force Reloading ProtocolRouter.", "WARNING")
                    old_observers = cls._instance.monitor._observers
                    old_mqtt = cls._instance.mqtt_manager
                    old_splinker = cls._instance.splinker_manager
                    
                    new_instance = cls()
                    new_instance.monitor._observers = old_observers
                    new_instance.mqtt_manager = old_mqtt
                    new_instance.splinker_manager = old_splinker
                    cls._instance = new_instance
                else:
                    cls._instance = cls()
        return cls._instance

    def start(self):
        if self._running: return
        self._running = True
        threading.Thread(target=self._ingest_loop, daemon=True).start()
        
        try:
            self._executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=self._dispatch_threads, 
                thread_name_prefix="ProtocolDispatch"
            )
            for _ in range(self._dispatch_threads):
                self._executor.submit(self._dispatch_loop)
        except RuntimeError as e:
            if "atexit" in str(e):
                matrix_log("core", "router", "start", "⚠️ [ROUTER] ThreadPoolExecutor failed. Falling back to single-threaded dispatch.", "WARNING")
                t = threading.Thread(target=self._dispatch_loop, name="ProtocolDispatchFallback", daemon=True)
                t.start()
            else:
                raise
        
        matrix_log("core", "router", "start", f"▶️▶️▶️ [START] Protocol Router Active (GUID: {self.GUID}).", "SUCCESS")

    def stop(self):
        self._running = False
        if self._executor: 
            self._executor.shutdown(wait=False)

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
        normalize_and_ingest(
            transport_source, topic, value, metadata, 
            self.GUID, self.settle_manager, self.inbound_queue,
            self._ingest_silent, self.state_cache
        )

    def _ingest_silent(self, transport_source, topic, value, meta):
        msg = create_silent_msg(transport_source, topic, value, meta, self.GUID)
        self.inbound_queue.put(msg)

    def _ingest_loop(self):
        while self._running:
            try:
                msg = self.inbound_queue.get(timeout=1.0)
                if msg is None: break
                
                investigate_packet(msg, self.mib_cache)
                strategy = calculate_strategy(msg)
                msg["strategy"] = strategy

                if self.splinker_manager:
                    try: self.splinker_manager.process_router_event(msg)
                    except Exception as e: 
                        matrix_log("core", "router", "_ingest_loop", f"🔗🚫🛑 [ROUTER] Splinker Error: {e}", "ERROR")

                msg["ui_tags"] = calculate_ui_tags(msg, self.GUID)
                self.monitor.append_to_firehose(msg)

                val_str = str(msg['val'])[:100] + ("..." if len(str(msg['val'])) > 100 else "")
                matrix_log("core", "router", "_ingest_loop", f"📥📡📤 [ROUTER] {strategy} >> {msg['topic']}: {val_str}", "DEBUG")

                self.monitor.broadcast_to_observers(msg)
                
                if "IGNORE" not in strategy:
                    self.outbound_queue.put(msg)
                self.inbound_queue.task_done()
            except queue.Empty: continue
            except Exception as e: 
                matrix_log("core", "router", "_ingest_loop", f"📥🚫🛑 [ROUTER] Ingest Error: {e}", "ERROR")

    def _dispatch_loop(self):
        while self._running:
            try:
                msg = self.outbound_queue.get(timeout=1.0)
                if msg is None: break
                
                active_managers = {"mqtt": self.mqtt_manager}
                if getattr(self, "is_active", True):
                    active_managers.update({
                        "osc": self.osc_manager,
                        "midi": self.midi_manager, 
                        "snmp": self.snmp_manager,
                        "smpte2138": self.smpte2138_manager
                    })
                
                dispatch_message(msg, active_managers)
                self.outbound_queue.task_done()
            except queue.Empty: continue
            except Exception as e: 
                matrix_log("core", "router", "_dispatch_loop", f"📤🚫🛑 [ERROR] Dispatch Loop Error: {e}", "ERROR")

    def get_splink_relationship(self, ts): return self.monitor.get_splink_relationship(ts)
    def get_dpi_report(self, ts): return self.monitor.get_dpi_report(ts)
    
    def publish_splink(self, s_topic, d_topic, s_val=None, d_val=None):
        payload = {"source": s_topic, "dest": d_topic, "source_val": s_val, "dest_val": d_val}
        self.ingest("GUI", "OPEN-AIR/System/Control/Splinker/DirectCreate", payload)
        return True
