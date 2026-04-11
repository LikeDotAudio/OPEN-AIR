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
from oaConfigurationManager.Entry import Config

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
        
        # ⚡ NATIVE ACCELERATION: Rust core router for high-speed paths.
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
        self.nmos_manager = None
        self.smpte2138_manager = None
        
        # ⚡ PROTOCOL ROUTING MATRIX (N x N): 
        # Controls which source protocols (Rows) are allowed to dispatch to destination protocols (Cols).
        # "anything can route to anything but itself" - Standard loopback prevention.
        self.protocols = ["MQTT", "OSC", "MIDI", "SNMP", "REST", "SMPTE2138", "AES70", "EMBER", "NMOS", "VISA", "GUI"]
        
        # Emoji mapping for strategy generation
        self.protocol_emojis = {
            "MQTT": "🚀", "OSC": "🅾️", "MIDI": "🎹", "SNMP": "Ⓢ", "REST": "🌐",
            "SMPTE2138": "🔗", "AES70": "70", "EMBER": "🔥", "NMOS": "N", "VISA": "V",
            "GUI": "Ⓖ"
        }

        # ⚡ PROTOCOL TOPIC PREFIXES: Used to auto-detect logical source from MQTT topics.
        self.protocol_prefixes = {
            "GUI": ["OPEN-AIR/GUI", "OPEN-AIR/oaGui"],
            "MIDI": "OPEN-AIR/MIDI",
            "NMOS": "OPEN-AIR/NMOS",
            "AES70": "OPEN-AIR/AES70",
            "SMPTE2138": "OPEN-AIR/SMPTE2138",
            "EMBER": "OPEN-AIR/EMBER"
        }

        # ⚡ HUB-AND-SPOKE: Boolean enablement maps
        # Initialize from config.ini. Default True if config key is missing.
        self.ingest_enabled = {p: app_constants.get(f"ingest_{p.lower()}", True) or True for p in self.protocols}
        self.egress_enabled = {p: app_constants.get(f"egress_{p.lower()}", True) or True for p in self.protocols}
        
        # ⚡ V3.1.25 LEGACY COMPATIBILITY: Restore N x N Routing Matrix
        # Many UI components still expect this structure for granular visualization.
        # We synchronize it with the hub-and-spoke maps.
        self.routing_matrix = {src: {dest: True for dest in self.protocols} for src in self.protocols}
        for p in self.protocols:
            self.routing_matrix[p][p] = False # Default loopback prevention
        
        # ⚡ PROTOCOL ROUTING (DEPRECATED)
        self.state_cache = None
        self.is_active = True 

    def _save_routing_config(self, proto, type, enabled):
        """Persists enablement state to config.ini."""
        config_path = "/home/anthony/Documents/OPEN-AIR/config.ini"
        import configparser
        cfg = configparser.ConfigParser()
        cfg.read(config_path)
        if not cfg.has_section("Routing"): cfg.add_section("Routing")
        cfg.set("Routing", f"{type}_{proto.lower()}", str(enabled))
        with open(config_path, "w") as f:
            cfg.write(f)

    @property
    def firehose(self):
        return self.monitor.firehose

    @property
    def GUID(self):
        return app_constants.FULL_INSTANCE_ID

    @classmethod
    def get_instance(cls, force_reload=False):
        # ⚡ OPTIMIZATION: Double-checked locking to avoid lock overhead in the fast path.
        if not force_reload and cls._instance is not None:
            return cls._instance
            
        with cls._lock:
            if force_reload:
                cls._instance = None
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def start(self):
        if self._running: return
        self._running = True
        
        # ⚡ LEADERSHIP: Force initial active state to ensure all managers start as PRIMARY
        self.set_active_state(True)
        
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=self._dispatch_threads, thread_name_prefix="Router-Dispatch")
        
        threading.Thread(target=self._ingest_loop, daemon=True, name="Router-Ingest").start()
        threading.Thread(target=self._dispatch_loop, daemon=True, name="Router-Dispatch-Master").start()
        
        matrix_log("comms", "broker", "start", f"▶️▶️▶️ [START] Protocol Router Active (GUID: {self.GUID}).", "SUCCESS")

    def stop(self):
        self._running = False
        # ⚡ STABILITY: Wait for pending dispatch tasks to finish before closing native resources
        if self._executor: self._executor.shutdown(wait=True)
        matrix_log("comms", "broker", "stop", "⏹️ [STOP] Protocol Router Offline.", "INFO")

    def shutdown(self):
        """
        ⚡ V3.1.29 GRACEFUL SHUTDOWN: Orchestrates the teardown of internal 
        monitoring and dispatch subsystems.
        """
        self.stop()
        if hasattr(self, 'monitor'):
            self.monitor.shutdown()
        matrix_log("comms", "broker", "shutdown", "Protocol Router shutdown sequence complete.", "DEBUG")

    def set_active_state(self, active):
        if self.is_active == active: return
        self.is_active = active
        
        state_label = "PRIMARY" if active else "SHADOW"
        matrix_log("comms", "broker", "set_active_state", f"🔄 [FAILOVER] Protocol Router transitioning to {state_label} mode.", "INFO")
        
        managers = [self.osc_manager, self.midi_manager, self.snmp_manager, self.smpte2138_manager]
        for mgr in managers:
            if not mgr: continue
            try:
                if active:
                    if hasattr(mgr, "start"): mgr.start()
                else:
                    if hasattr(mgr, "stop"): mgr.stop()
            except Exception as e:
                matrix_log("comms", "broker", "set_active_state", f"❌ [FAILOVER] Error transitioning manager: {e}", "ERROR")

    def set_mqtt_manager(self, m): self.mqtt_manager = m
    def set_splinker_manager(self, m): self.splinker_manager = m
    def set_osc_manager(self, m): self.osc_manager = m
    def set_midi_manager(self, m): self.midi_manager = m
    def set_snmp_manager(self, m): self.snmp_manager = m
    def set_nmos_manager(self, m): self.nmos_manager = m
    def set_smpte2138_manager(self, m): self.smpte2138_manager = m
    def set_state_cache(self, c): self.state_cache = c

    def set_routing_state(self, source, dest, enabled):
        """Updates the Hub-and-Spoke enablement maps."""
        # Note: In the new architecture, we treat 'dest' as the spoke being enabled/disabled.
        s_up = str(source).upper() # Left for compatibility, but deprecated
        d_up = str(dest).upper()
        
        # Enable/Disable Egress to the destination
        if d_up in self.egress_enabled:
            self.egress_enabled[d_up] = enabled
        
        # Enable/Disable Ingress from the source
        if s_up in self.ingest_enabled:
            self.ingest_enabled[s_up] = enabled
            
        matrix_log("comms", "broker", "set_routing_state", f"🔄 [ROUTING] {source} -> {dest} set to {enabled}.", "INFO")

    def set_topic_routing(self, source, dest, send_topic=None, sub_topic=None):
        """Deprecated."""
        pass

    def get_topic_routing(self, source, dest):
        """Deprecated."""
        return {"send": None, "subscribe": None}

    def get_strategy_for_source(self, source):
        """Returns the emoji strategy string for a given logical source."""
        s_up = str(source).upper()
        enabled_dests = [d for d in self.protocols if self.egress_enabled.get(d, True)]
        emojis = [self.protocol_emojis.get(d, d) for d in enabled_dests]
        return " ".join(emojis)

    def calculate_strategy_for_msg(self, source, topic):
        """
        Calculates the emoji strategy for a specific message.
        Checks egress enablement and the 'Subscribe' topic filters.
        """
        s_up = str(source).upper()
        
        import fnmatch
        emojis = []
        for dest in self.protocols:
            if not self.egress_enabled.get(dest, True):
                continue
            
            # (No topic filtering in hub-and-spoke model)
            emojis.append(self.protocol_emojis.get(dest, dest))
            
        return " ".join(emojis)

    def register_cache_observer(self, cb): self.monitor.register_cache_observer(cb)
    def unregister_cache_observer(self, cb): self.monitor.remove_observer(cb)
    def remove_observer(self, cb): self.monitor.remove_observer(cb)

    def ingest(self, transport_source, topic, value, metadata=None):
        # ⚡ ARCHITECTURAL CHOICE: Allow all ingest so messages appear in the firehose.
        # Routing gating is now handled at the Dispatch phase via the N x N matrix.
        normalize_and_ingest(
            transport_source, topic, value, metadata, 
            self.GUID, self.settle_manager, self.inbound_queue,
            self._ingest_silent, self.state_cache, self.rust_router,
            self.is_active
        )

    def _ingest_silent(self, transport_source, topic, value, meta):
        # ⚡ V3.1.5 PIPELINE SYNC:
        # Silent messages (Boot sequence) must still pass through the pipeline 
        # to ensure they are normalized with GUIDs and UI tags for the Command Router.
        msg = create_silent_msg(transport_source, topic, value, meta, self.GUID, self.rust_router)
        self._process_message_pipeline(msg)

    def _fetch_next_inbound(self):
        # ⚡ DRAIN: If messages are in the Rust router, we must drain them to prevent leaks.
        # For now, we still use the Python inbound_queue as the primary source of truth.
        if self.rust_router and self.rust_router.inbound_len() > 0:
            while self.rust_router.inbound_len() > 0:
                self.rust_router.pop_inbound()

        try:
            # ⚡ OPTIMIZATION: Increased timeout from 0.001 to 0.1 to reduce busy-wait overhead.
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
                matrix_log("comms", "broker", "_process_pipeline", f"🔗🚫🛑 [ROUTER] Splinker Error: {e}", "ERROR")

        msg["ui_tags"] = calculate_ui_tags(msg, self.GUID)
        
        self.monitor.append_to_firehose(msg)
        self.monitor.broadcast_to_observers(msg)
        
        val_str = str(msg['val'])[:100] + ("..." if len(str(msg['val'])) > 100 else "")
        matrix_log("comms", "broker", "_process_pipeline", f"📥📡📤 [ROUTER] {strategy} >> {msg['topic']}: {val_str}", "DEBUG")
        
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
                matrix_log("comms", "broker", "_ingest_loop", f"📥🚫🛑 [ROUTER] Ingest Error: {e}", "ERROR")

    def _dispatch_loop(self):
        while self._running:
            try:
                try:
                    # ⚡ OPTIMIZATION: Increased timeout from 0.001 to 0.1 to reduce busy-wait overhead.
                    msg = self.outbound_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Prepare manager registry for the dispatcher
                managers = {
                    "mqtt": self.mqtt_manager,
                    "osc": self.osc_manager,
                    "midi": self.midi_manager,
                    "snmp": self.snmp_manager,
                    "nmos": self.nmos_manager,
                    "smpte2138": self.smpte2138_manager
                }
                
                if self._running:
                    self._executor.submit(
                        dispatch_message, 
                        msg, managers,
                        self.is_active
                    )
            except RuntimeError as e:
                # ⚡ TEARDOWN SAFETY: Ignore executor shutdown errors during exit
                if "after shutdown" in str(e).lower():
                    pass
                else:
                    matrix_log("comms", "broker", "_dispatch_loop", f"📤🚫🛑 [ERROR] Dispatch Loop Error: {e}", "ERROR")
            except Exception as e:
                matrix_log("comms", "broker", "_dispatch_loop", f"📤🚫🛑 [ERROR] Dispatch Loop Error: {e}", "ERROR")

    def get_message_by_utp(self, utp):
        """Retrieves a complete message from the firehose by its UTP."""
        if not utp: return None
        with self.monitor._firehose_lock:
            return next((m for m in self.monitor.firehose if f"{m['ts']:.6f}" == utp), None)

    def publish_splinker_direct(self, s_topic, d_topic, s_val=None, d_val=None):
        payload = {"source": s_topic, "dest": d_topic, "source_val": s_val, "dest_val": d_val}
        self.ingest("comms", "broker", payload)
        return True