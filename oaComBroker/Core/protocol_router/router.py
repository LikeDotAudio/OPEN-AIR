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
# Version 20260328.1405.1
#
# Description:
# The ProtocolRouter is the central nervous system of the OPEN-AIR 
# communication layer. It acts as a high-performance multiplexer that 
# normalizes ingress traffic from MQTT, MIDI, OSC, and SNMP into a 
# unified internal format, applies strategy-based filtering, and 
# dispatches commands to the appropriate endpoints.
#
# Architectural Role:
# - Serves as the primary bridge between Core hardware logic and UI layers.
# - Implements the Failover State Machine (Active/Shadow modes).
# - Enforces the Partitioned Architecture by decoupling transport protocols 
#   from business logic.

import queue
import threading
import concurrent.futures
from .constants import LOCAL_DEBUG, app_constants
from oaLogging.Core.logger import router_logger

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
    
    This class manages the lifecycle of the internal message queues and
    the thread pools responsible for concurrent packet processing and
    dispatch. It handles failover state transitions to ensure that only
    the primary instance controls physical hardware.
    """
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        """
        Initializes the router's internal state and buffers.
        
        This constructor should not be called directly. Use get_instance() 
        to ensure singleton integrity.
        
        Side Effects:
            - Allocates thread-safe queues for inbound and outbound traffic.
            - Spawns internal monitoring and settlement managers.
        """
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        
        # Internal buffering.
        self.inbound_queue = queue.Queue()
        self.outbound_queue = queue.Queue()
        
        self._running = False
        self._dispatch_threads = 4
        self._executor = None
        
        # Subsystem-specific caches for protocol optimization.
        self.mib_cache = {}
        self.osc_cache = {}
        
        # Components for observability and settling.
        self.monitor = Monitor(self.GUID)
        self.settle_manager = SettleManager(self.ingest)
        
        # Transport Managers: Registered dynamically during boot.
        self.mqtt_manager = None
        self.splinker_manager = None
        self.osc_manager = None
        self.midi_manager = None
        self.snmp_manager = None
        
        # Reference to the global State Cache for cross-instance mirroring.
        self.state_cache = None
        
        # Failover State: True (Primary), False (Shadow).
        self.is_active = True 

    @property
    def firehose(self):
        """Provides access to the high-velocity monitoring stream."""
        return self.monitor.firehose

    @property
    def GUID(self):
        """Returns the Instance's unique identifier."""
        return app_constants.INSTANCE_GUID

    @classmethod
    def get_instance(cls, force_reload=False):
        """
        Thread-safe singleton accessor for the ProtocolRouter.
        
        Args:
            force_reload (bool): If True, nukes the current instance and
                re-initializes. Use only during configuration shifts.
        
        Returns:
            ProtocolRouter: The global router instance.
        """
        if cls._instance is not None and not force_reload:
            return cls._instance

        with cls._lock:
            if cls._instance is None or force_reload:
                if force_reload and cls._instance:
                    router_logger.warning("📜📑💻 [CONFIG] Force Reloading ProtocolRouter.")
                    # Preserve observers across reloads to prevent telemetry gaps.
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
        """
        Activates the ingest loop and dispatch thread pool.
        
        Spawns the main ingest thread and a pool of worker threads to 
        handle outbound dispatch. Implements a fallback mechanism if
        concurrent futures cannot allocate the requested resources.
        
        Side Effects:
            - Spawns N+1 background threads.
            - Broadcasts a [START] status log.
        """
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
            # Handle edge cases where the thread pool cannot be allocated.
            if "atexit" in str(e):
                router_logger.warning("⚠️ [ROUTER] ThreadPoolExecutor failed. Falling back to single-threaded dispatch.")
                t = threading.Thread(target=self._dispatch_loop, name="ProtocolDispatchFallback", daemon=True)
                t.start()
            else:
                raise
        
        router_logger.success(f"▶️▶️▶️ [START] Protocol Router Active (GUID: {self.GUID}).")

    def stop(self):
        """
        Initiates a graceful shutdown of all routing loops.
        """
        self._running = False
        if self._executor: 
            self._executor.shutdown(wait=False)

    def set_active_state(self, active):
        """
        Transitions the router between Active (Primary) and Passive (Shadow).
        
        In Shadow mode, the router continues to mirror state via MQTT but 
        halts all outbound MIDI, OSC, and SNMP commands to prevent dual-
        primary hardware collisions.
        
        Args:
            active (bool): True for Primary, False for Shadow.
            
        Side Effects:
            - Starts/Stops protocol-specific managers based on state.
        """
        if self.is_active == active: return
        self.is_active = active
        
        state_label = "PRIMARY" if active else "SHADOW"
        router_logger.info(f"🔄 [FAILOVER] Protocol Router transitioning to {state_label} mode.")
        
        # Dynamic lifecycle management for hardware-facing managers.
        managers = [self.osc_manager, self.midi_manager, self.snmp_manager]
        for mgr in managers:
            if not mgr: continue
            try:
                if active:
                    if hasattr(mgr, "start"): mgr.start()
                else:
                    if hasattr(mgr, "stop"): mgr.stop()
            except Exception as e:
                router_logger.error(f"❌ [FAILOVER] Error transitioning manager: {e}")

    # --- Linking APIs ---
    # These methods register transport layers with the central hub.
    def set_mqtt_manager(self, m): self.mqtt_manager = m
    def set_splinker_manager(self, m): self.splinker_manager = m
    def set_osc_manager(self, m): self.osc_manager = m
    def set_midi_manager(self, m): self.midi_manager = m
    def set_snmp_manager(self, m): self.snmp_manager = m
    def set_state_cache(self, c): self.state_cache = c

    # --- Observation APIs ---
    def register_cache_observer(self, cb): self.monitor.register_cache_observer(cb)
    def unregister_cache_observer(self, cb): self.monitor.remove_observer(cb)
    def remove_observer(self, cb): self.monitor.remove_observer(cb)

    def ingest(self, transport_source, topic, value, metadata=None):
        """
        Normalizes and injects a packet into the inbound processing queue.
        
        Args:
            transport_source (str): Origin (e.g., 'MQTT', 'OSC').
            topic (str): The logical address or key.
            value (any): The data payload.
            metadata (dict, optional): Contextual headers.
        """
        normalize_and_ingest(
            transport_source, topic, value, metadata, 
            self.GUID, self.settle_manager, self.inbound_queue,
            self._ingest_silent, self.state_cache
        )

    def _ingest_silent(self, transport_source, topic, value, meta):
        """Internal helper for injecting messages without triggering loops."""
        msg = create_silent_msg(transport_source, topic, value, meta, self.GUID)
        self.inbound_queue.put(msg)

    def _ingest_loop(self):
        """
        Main ingress consumer: Analyzes, decorates, and filters traffic.
        
        Responsibilities:
        - Deep Packet Inspection (DPI) for SNMP MIB resolution.
        - Strategy calculation (Should we drop, log, or forward?).
        - UI Tag generation for frontend compatibility.
        - Firehose telemetry updates.
        """
        while self._running:
            try:
                msg = self.inbound_queue.get(timeout=1.0)
                if msg is None: break
                
                investigate_packet(msg, self.mib_cache)
                strategy = calculate_strategy(msg)
                msg["strategy"] = strategy

                # Splinker integration for cross-protocol cross-patching.
                if self.splinker_manager:
                    try: self.splinker_manager.process_router_event(msg)
                    except Exception as e: router_logger.error(f"🔗🚫🛑 [ROUTER] Splinker Error: {e}")

                msg["ui_tags"] = calculate_ui_tags(msg, self.GUID)
                self.monitor.append_to_firehose(msg)

                if LOCAL_DEBUG:
                    val_str = str(msg['val'])[:100] + ("..." if len(str(msg['val'])) > 100 else "")
                    router_logger.debug(f"📥📡📤 [ROUTER] {strategy} >> {msg['topic']}: {val_str}")

                self.monitor.broadcast_to_observers(msg)
                
                # Filter based on calculated strategy.
                if "IGNORE" not in strategy:
                    self.outbound_queue.put(msg)
                self.inbound_queue.task_done()
            except queue.Empty: continue
            except Exception as e: router_logger.error(f"📥🚫🛑 [ROUTER] Ingest Error: {e}")

    def _dispatch_loop(self):
        """
        Outbound consumer: Executes protocol-specific egress.
        
        Failover Logic:
        - MQTT: Always dispatched for state synchronization.
        - Hardware (OSC/MIDI/SNMP): Only dispatched if self.is_active is True.
        """
        while self._running:
            try:
                msg = self.outbound_queue.get(timeout=1.0)
                if msg is None: break
                
                # Dynamic protocol targeting based on failover state.
                active_managers = {"mqtt": self.mqtt_manager}
                if getattr(self, "is_active", True):
                    active_managers.update({
                        "osc": self.osc_manager,
                        "midi": self.midi_manager, 
                        "snmp": self.snmp_manager
                    })
                
                dispatch_message(msg, active_managers)
                self.outbound_queue.task_done()
            except queue.Empty: continue
            except Exception as e: router_logger.error(f"📤🚫🛑 [ERROR] Dispatch Loop Error: {e}")

    # --- Monitoring / Forensic APIs ---
    def get_splink_relationship(self, ts): return self.monitor.get_splink_relationship(ts)
    def get_dpi_report(self, ts): return self.monitor.get_dpi_report(ts)
    
    def publish_splink(self, s_topic, d_topic, s_val=None, d_val=None):
        """Manually triggers a splink creation via the command router."""
        payload = {"source": s_topic, "dest": d_topic, "source_val": s_val, "dest_val": d_val}
        self.ingest("GUI", "OPEN-AIR/System/Control/Splinker/DirectCreate", payload)
        return True
