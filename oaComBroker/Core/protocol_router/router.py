# protocol_router/router.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: The Orchestrator for the modular Protocol Router.

import queue
import threading
import concurrent.futures
from .constants import LOCAL_DEBUG, app_constants
from oaLogging.Core.logger import router_logger

# Modular Imports
from .ingest import normalize_and_ingest, create_silent_msg
from .dispatch import dispatch_message
from .settle import SettleManager
from .strategy import calculate_strategy, calculate_ui_tags
from .dpi import investigate_packet
from .monitor import Monitor

class ProtocolRouter:
    """
    Singleton Hub for all command traffic.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        
        # Internal buffering.
        self.inbound_queue = queue.Queue()
        self.outbound_queue = queue.Queue()
        
        self._running = False
        self._dispatch_threads = 4
        self._executor = None
        
        # Subsystem-specific caches.
        self.mib_cache = {}
        self.osc_cache = {}
        
        # Components.
        self.monitor = Monitor(self.GUID)
        self.settle_manager = SettleManager(self.ingest)
        
        # Transport Managers.
        self.mqtt_manager = None
        self.splinker_manager = None
        self.osc_manager = None
        self.midi_manager = None
        self.snmp_manager = None

    @property
    def firehose(self):
        return self.monitor.firehose

    @property
    def GUID(self):
        return app_constants.INSTANCE_GUID

    @classmethod
    def get_instance(cls, force_reload=False):
        """
        Thread-safe singleton getter.
        """
        # Fast path for existing instance
        if cls._instance is not None and not force_reload:
            return cls._instance

        with cls._lock:
            # Re-check inside lock
            if cls._instance is None or force_reload:
                if force_reload and cls._instance:
                    router_logger.warning("📜📑💻 [CONFIG] Force Reloading ProtocolRouter.")
                    # Capture state from old instance
                    old_observers = cls._instance.monitor._observers
                    old_mqtt = cls._instance.mqtt_manager
                    old_splinker = cls._instance.splinker_manager
                    
                    # Create new instance
                    new_instance = cls()
                    
                    # Restore state
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
                router_logger.warning("⚠️ [ROUTER] ThreadPoolExecutor failed (atexit after shutdown). Falling back to single-threaded dispatch.")
                # Fallback: manually start one dispatch thread without using a pool
                t = threading.Thread(target=self._dispatch_loop, name="ProtocolDispatchFallback", daemon=True)
                t.start()
            else:
                raise
        
        router_logger.success(f"▶️▶️▶️ [START] Protocol Router Active (GUID: {self.GUID}).")

    def stop(self):
        self._running = False
        if self._executor: self._executor.shutdown(wait=False)

    # --- Linking APIs ---
    def set_mqtt_manager(self, m): self.mqtt_manager = m
    def set_splinker_manager(self, m): self.splinker_manager = m
    def set_osc_manager(self, m): self.osc_manager = m
    def set_midi_manager(self, m): self.midi_manager = m
    def set_snmp_manager(self, m): self.snmp_manager = m

    # --- Observation APIs ---
    def register_cache_observer(self, cb): self.monitor.register_cache_observer(cb)
    def remove_observer(self, cb): self.monitor.remove_observer(cb)

    def ingest(self, transport_source, topic, value, metadata=None):
        normalize_and_ingest(
            transport_source, topic, value, metadata, 
            self.GUID, self.settle_manager, self.inbound_queue,
            self._ingest_silent
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
                    except Exception as e: router_logger.error(f"🔗🚫🛑 [ROUTER] Splinker Error: {e}")

                msg["ui_tags"] = calculate_ui_tags(msg, self.GUID)
                self.monitor.append_to_firehose(msg)

                if LOCAL_DEBUG:
                    val_str = str(msg['val'])[:100] + ("..." if len(str(msg['val'])) > 100 else "")
                    router_logger.debug(f"📥📡📤 [ROUTER] {strategy} >> {msg['topic']}: {val_str}")

                self.monitor.broadcast_to_observers(msg)
                if "IGNORE" not in strategy:
                    self.outbound_queue.put(msg)
                self.inbound_queue.task_done()
            except queue.Empty: continue
            except Exception as e: router_logger.error(f"📥🚫🛑 [ROUTER] Ingest Error: {e}")

    def _dispatch_loop(self):
        managers = {
            "mqtt": self.mqtt_manager, "osc": self.osc_manager,
            "midi": self.midi_manager, "snmp": self.snmp_manager
        }
        while self._running:
            try:
                msg = self.outbound_queue.get(timeout=1.0)
                if msg is None: break
                dispatch_message(msg, managers)
                self.outbound_queue.task_done()
            except queue.Empty: continue
            except Exception as e: router_logger.error(f"📤🚫🛑 [ERROR] Dispatch Loop Error: {e}")

    # --- Monitoring / Forensic APIs ---
    def get_splink_relationship(self, ts): return self.monitor.get_splink_relationship(ts)
    def get_dpi_report(self, ts): return self.monitor.get_dpi_report(ts)
    
    def publish_splink(self, s_topic, d_topic, s_val=None, d_val=None):
        payload = {"source": s_topic, "dest": d_topic, "source_val": s_val, "dest_val": d_val}
        self.ingest("GUI", "OPEN-AIR/System/Control/Splinker/DirectCreate", payload)
        return True
