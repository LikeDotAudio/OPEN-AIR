# Core/protocol_router/router.py
#
# The Hub and Orchestrator for the modular Protocol Router engine.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20260331.2230.1

import concurrent.futures
import queue
import threading

from oaLogging.Core.logger import logger
from oaLogging.Methods.matrix_gate import matrix_log

from .constants import app_constants

try:
    from oaRustCore.oa_core_router_rs import CoreRouter as RustCoreRouter
    HAS_RUST_ROUTER = True
except ImportError:
    logger.warning("🚀⚠️ [ROUTER] Rust Core Router missing. Falling back to slow Python routing.")
    HAS_RUST_ROUTER = False

# Modular Subsystem Imports
from .dispatch import dispatch_message
from .dpi import investigate_packet
from .ingest import create_silent_message, normalize_and_ingest
from .monitor import Monitor
from .settle import SettleManager
from .strategy import calculate_strategy, calculate_ui_tags


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
        self.rust_router = RustCoreRouter() if HAS_RUST_ROUTER else None

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
        self.protocols = ["MQTT", "OSC", "MIDI", "SNMP", "REST", "SMPTE2138", "AES70", "EMBER", "NMOS", "VISA", "GUI", "CUSTOM"]

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
            "OSC": "OPEN-AIR/OSC",
            "SNMP": "OPEN-AIR/System/Monitor/SNMP",
            "NMOS": "OPEN-AIR/NMOS",
            "AES70": "OPEN-AIR/AES70",
            "SMPTE2138": "OPEN-AIR/SMPTE2138",
            "EMBER": "OPEN-AIR/EMBER"
        }

        # ⚡ HUB-AND-SPOKE: Boolean enablement maps
        # Enable all routing by default as per user request.
        self.ingest_enabled = {p: True for p in self.protocols}
        self.egress_enabled = {p: True for p in self.protocols}

        # ⚡ V3.1.25 LEGACY COMPATIBILITY: Restore N x N Routing Matrix
        # Many UI components still expect this structure for granular visualization.
        self.routing_matrix = {source: {destination: True for destination in self.protocols} for source in self.protocols}
        # Standard loopback prevention
        for p in self.protocols:
            self.routing_matrix[p][p] = False

        # ⚡ PROTOCOL ROUTING (DEPRECATED)
        self.state_cache = None
        self.is_active = True

    def _save_routing_config(self, proto, type, enabled):
        """Persists enablement state to config.ini."""
        config_path = "/home/anthony/Documents/OPEN-AIR/config.ini"
        import configparser
        configuration = configparser.ConfigParser()
        configuration.read(config_path)
        if not configuration.has_section("Routing"): configuration.add_section("Routing")
        configuration.set("Routing", f"{type}_{proto.lower()}", str(enabled))
        with open(config_path, "w") as f:
            configuration.write(f)

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

    def set_routing_state(self, source, destination, enabled):
        """Updates the Hub-and-Spoke enablement maps and the routing matrix."""
        s_up = str(source).upper()
        d_up = str(destination).upper()

        # Enable/Disable Egress to the destination
        if d_up in self.egress_enabled:
            self.egress_enabled[d_up] = enabled

        # Enable/Disable Ingress from the source
        if s_up in self.ingest_enabled:
            self.ingest_enabled[s_up] = enabled

        # ⚡ LEGACY COMPATIBILITY: Update the N x N routing matrix
        if s_up in self.routing_matrix and d_up in self.routing_matrix[s_up]:
            self.routing_matrix[s_up][d_up] = enabled

        matrix_log("comms", "broker", "set_routing_state", f"🔄 [ROUTING] {s_up} -> {d_up} set to {enabled}.", "INFO")

    def set_topic_routing(self, source, destination, send_topic=None, sub_topic=None):
        """Deprecated."""
        pass

    def get_topic_routing(self, source, destination):
        """Deprecated."""
        return {"send": None, "subscribe": None}

    def get_strategy_for_source(self, source):
        """Returns the emoji strategy string for a given logical source."""
        s_up = str(source).upper()
        enabled_dests = [d for d in self.protocols if self.egress_enabled.get(d, True)]
        emojis = [self.protocol_emojis.get(d, d) for d in enabled_dests]
        return " ".join(emojis)

    def calculate_strategy_for_message(self, source, topic):
        """
        Calculates the emoji strategy for a specific message.
        Checks egress enablement and the 'Subscribe' topic filters.
        """
        s_up = str(source).upper()

        emojis = []
        for destination in self.protocols:
            if not self.egress_enabled.get(destination, False):
                continue

            # (No topic filtering in hub-and-spoke model)
            emojis.append(self.protocol_emojis.get(destination, destination))

        if not emojis:
            return "IGNORE (ROUTING DISABLED)"

        return " ".join(emojis)

    def register_cache_observer(self, cb): self.monitor.register_cache_observer(cb)
    def unregister_cache_observer(self, cb): self.monitor.remove_observer(cb)
    def remove_observer(self, cb): self.monitor.remove_observer(cb)

    def ingest(self, transport_source, topic, value, metadata=None):
        # ⚡ USER REQUEST: Disconnect Command Router.
        # If all ingest is disabled, we drop the packet before it even enters the pipeline.
        if not any(self.ingest_enabled.values()):
            return

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
        message = create_silent_message(transport_source, topic, value, meta, self.GUID, self.rust_router)
        self._process_message_pipeline(message)

    def _fetch_next_inbound(self):
        # ⚡ DRAIN: If messages are in the Rust router, we must drain them to prevent leaks.
        # For now, we still use the Python inbound_queue as the primary source of truth.

        # TODO: BUG: The rust_router drain loop causes the ingest pipeline to hang for
        # some message types (e.g. MIDI). Disabling until the Rust component can be fixed.
        # if self.rust_router and self.rust_router.inbound_len() > 0:
        #     while self.rust_router.inbound_len() > 0:
        #         self.rust_router.pop_inbound()

        try:
            # ⚡ OPTIMIZATION: Increased timeout from 0.001 to 0.1 to reduce busy-wait overhead.
            return self.inbound_queue.get(timeout=0.1)
        except queue.Empty:
            return None

    def _process_message_pipeline(self, message):
        investigate_packet(message, self.mib_cache)

        strategy = calculate_strategy(message)
        message["strategy"] = strategy

        # if self.splinker_manager:
        #     try: self.splinker_manager.process_router_event(message)
        #     except Exception as e:
        #         matrix_log("comms", "broker", "_process_pipeline", f"🔗🚫🛑 [ROUTER] Splinker Error: {e}", "ERROR")

        message["ui_tags"] = calculate_ui_tags(message, self.GUID)

        self.monitor.append_to_firehose(message)
        self.monitor.broadcast_to_observers(message)

        if getattr(app_constants, "ROUTER_DISPATCH_LOGS", True):
            val_str = str(message['value'])[:100] + ("..." if len(str(message['value'])) > 100 else "")
            matrix_log("comms", "broker", "_process_pipeline", f"📥📡📤 [ROUTER] {strategy} >> {message['topic']}: {val_str}", "DEBUG")

        self._dispatch_by_strategy(strategy, message)

    def _dispatch_by_strategy(self, strategy, message):
        if "IGNORE" not in strategy:
            self.outbound_queue.put(message)

    def _ingest_loop(self):
        while self._running:
            try:
                message = self._fetch_next_inbound()
                if message is None: continue
                self._process_message_pipeline(message)
            except Exception as e:
                matrix_log("comms", "broker", "_ingest_loop", f"📥🚫🛑 [ROUTER] Ingest Error: {e}", "ERROR")

    def _dispatch_loop(self):
        while self._running:
            try:
                try:
                    # ⚡ OPTIMIZATION: Increased timeout from 0.001 to 0.1 to reduce busy-wait overhead.
                    message = self.outbound_queue.get(timeout=0.1)
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
                        message, managers,
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
            return next((m for m in self.monitor.firehose if f"{m['timestamp']:.6f}" == utp), None)

    def publish_splinker_direct(self, s_topic, d_topic, s_val=None, d_val=None):
        payload = {"source": s_topic, "dest": d_topic, "source_val": s_val, "dest_val": d_val}
        self.ingest("comms", "broker", payload)
        return True
