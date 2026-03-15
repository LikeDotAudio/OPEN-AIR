# State_Cache/state_cache_manager.py
#
# Manages the overall state cache system, orchestrating I/O, traffic control, and GUI restoration.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260222.Optimized.1

import inspect
import threading
import queue
import time
import orjson
from typing import Dict, Any, Set

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, data_logger
from loguru import logger

from managers.configini.config_reader import Config
from workers.Command_Router.mqtt.mqtt_message import MqttMessage

app_constants = Config.get_instance()

from . import cache_io_handler
from . import cache_traffic_controller
from . import gui_state_restorer

class StateCacheManager:
    """
    The public API for the state cache system.
    Implemented with a Write-Behind Cache (Debounced) and Delta Tracking.
    """

    def __init__(self, mqtt_connection_manager: Any, state_mirror_engine: Any = None):
        self.mqtt_connection_manager = mqtt_connection_manager
        self.state_mirror_engine = state_mirror_engine
        
        # ⚡ OPTIMIZATION: Prefix presence map for O(1) tab existence checks
        self._active_prefixes: Set[str] = set()
        
        # ⚡ OPTIMIZATION: Pre-warm the cache from disk immediately
        try:
            self.cache = cache_io_handler.load_cache()
            self._update_prefix_set()
            if LOCAL_DEBUG:
                data_logger.debug(
                    f"🧠💾🗂️ [CACHE] StateCacheManager: Pre-warmed with "
                    f"{len(self.cache)} entries."
                )
        except Exception:
            self.cache = {}
            data_logger.exception(
                "🧠💾❌ [ERROR] StateCacheManager: Failed to pre-warm cache"
            )

        self.subscriber_router = None
        self._last_log_time = time.time()
        self._updates_since_last_log = 0

        # --- Observer Pattern ---
        self._observers = []

        # --- Debounced Serialization State ---
        self._pending_deltas = {}
        self._delta_lock = threading.Lock()
        self._last_activity_time = time.time()
        self._DEBOUNCE_DELAY = 2.0  # 2 seconds of silence before disk commit
        self._MAX_STALE_TIME = 30.0 # Force save if changes persist but no silence

        # Asynchronous Save Worker
        self._save_queue = queue.Queue()
        self._save_thread = threading.Thread(target=self._save_worker, daemon=True)
        self._save_thread.start()

    def _update_prefix_set(self):
        """Rebuilds the prefix set from the current cache keys."""
        new_prefixes = set()
        for topic in self.cache:
            # Add segments to allow partial prefix matching
            parts = topic.split('/')
            for i in range(1, len(parts)):
                new_prefixes.add('/'.join(parts[:i]) + '/')
        self._active_prefixes = new_prefixes

    def check_prefix_exists(self, prefix: str) -> bool:
        """
        ⚡ OPTIMIZATION: O(1) check if any cached topics start with the given prefix.
        Used by StateMirrorEngine to skip initialization for empty tabs.
        """
        if not prefix.endswith('/'): prefix += '/'
        return prefix in self._active_prefixes

    def _save_worker(self):
        """
        Background worker that implements debounced write-behind cache.
        HIGH-PERFORMANCE: High-frequency MQTT traffic is held in memory and
        committed to disk only after a period of user/network inactivity.
        """
        last_commit_time = time.time()
        
        while True:
            try:
                # ⚡ PERFORMANCE: Check the queue for incoming delta traffic
                try:
                    item = self._save_queue.get(timeout=1.0)
                    if item is None: break 
                    
                    topic, payload = item
                    with self._delta_lock:
                        self._pending_deltas[topic] = payload
                        self._last_activity_time = time.time()
                    self._save_queue.task_done()
                except queue.Empty: pass
                
                # Check if we should commit to disk
                now = time.time()
                with self._delta_lock:
                    has_pending = len(self._pending_deltas) > 0
                    silence_duration = now - self._last_activity_time
                    stale_duration = now - last_commit_time
                    
                    # Commit Condition: Silence for X seconds OR max stale time reached
                    if has_pending and (silence_duration >= self._DEBOUNCE_DELAY or stale_duration >= self._MAX_STALE_TIME):
                        num_deltas = len(self._pending_deltas)
                        
                        # Apply deltas to the master cache and serializing
                        # ⚡ DELTA-ONLY COMMITS: Merge pending into the main cache
                        self.cache.update(self._pending_deltas)
                        self._pending_deltas.clear()
                        
                        # Write the full state (standard for JSON persistence)
                        # Future optimization: Partial files for massive datasets
                        cache_io_handler.save_cache(self.cache)
                        
                        last_commit_time = now
                        if LOCAL_DEBUG:
                            data_logger.success(
                                f"💾✍️🆗 [SUCCESS] Debounced Commit: "
                                f"{num_deltas} deltas saved to disk."
                            )
                        
            except Exception: 
                data_logger.exception(
                    "🧠💾❌ [ERROR] Error in state cache save worker"
                )

    def save_preset(self, preset_name: str):
        """
        OcaPreset paradigm: Snapshots the current in-memory state to an isolated file.
        """
        try:
            from workers.initialization import worker_project_paths as app_constants
            preset_filename = f"{preset_name}.preset.json"
            preset_path = os.path.join("DATA", "state", "presets", preset_filename)
            os.makedirs(os.path.dirname(preset_path), exist_ok=True)
            
            with open(preset_path, "wb") as f:
                f.write(orjson.dumps(self.cache, option=orjson.OPT_INDENT_2))
            
            if LOCAL_DEBUG:
                data_logger.success(
                    f"📸💾✨ [SUCCESS] Preset Snapshot saved: {preset_filename}"
                )
            return True
        except Exception as e:
            data_logger.error(
                f"🧠💾❌ [ERROR] Failed to save preset {preset_name}: {e}"
            )
            return False

    def shutdown(self):
        if LOCAL_DEBUG:
            data_logger.debug(
                "🧠💾🔌 [CACHE] StateCacheManager: Shutting down save worker..."
            )
        self._save_queue.put(None)
        if self._save_thread.is_alive():
            self._save_thread.join(timeout=2.0)
        if LOCAL_DEBUG:
            data_logger.debug(
                "🧠💾✅ [CACHE] StateCacheManager: Save worker offline."
            )

    def subscribe_to_all_topics(self):
        topic = "OPEN-AIR/#"
        self.mqtt_connection_manager.subscribe(topic)
        if LOCAL_DEBUG:
            data_logger.debug(
                f"🧠📡🌐 [CACHE] Subscribing to topic: {topic}"
            )

    def initialize_state(self) -> None:
        if LOCAL_DEBUG:
            data_logger.debug(
                "🧠💾🧐 [CACHE] Initializing timeline from cache..."
            )
        try:
            self.cache = cache_io_handler.load_cache()
            self._update_prefix_set()
            if self.cache:
                # ⚡ INGEST: Notify the Central Router of the INITIAL DISK LOAD
                # ⚡ ANTI-FEEDBACK SPEC: Disk loads are LINK_FEEDBACK and is_settled: True
                # This ensures we restore the visual state without triggering a new settling/broadcast cycle.
                from workers.Command_Router.protocol_router import ProtocolRouter
                router = ProtocolRouter.get_instance()
                for topic, payload in self.cache.items():
                    val = payload.get("val") if isinstance(payload, dict) else payload
                    router.ingest("DISK", topic, val, {
                        "msg_type": "LINK_FEEDBACK",
                        "is_settled": True,
                        "origin_source": "DISK",
                        "boot": True # ⚡ BOOT TAG: Silent acceptance by Core/Others
                    })

                gui_state_restorer.restore_timeline(self.cache, self.state_mirror_engine)
                if LOCAL_DEBUG:
                    data_logger.success(
                        "🧠💾✅ [SUCCESS] Timeline restoration triggered."
                    )
            else:
                if LOCAL_DEBUG:
                    data_logger.debug("🧠💾🐣 [CACHE] Cache is empty.")
        except Exception:
            data_logger.exception(
                "🧠💾❌ [ERROR] State initialization failed"
            )
            self.cache = {} 

    def add_observer(self, callback: Any):
        """Registers a callback function for state changes."""
        self._observers.append(callback)

    def get(self, topic: str) -> Any:
        """
        Public API to retrieve a value from the cache.
        Returns the unwrapped 'val' or None if the topic doesn't exist.
        """
        entry = self.cache.get(topic)
        if entry is None: return None
        return entry.get("val") if isinstance(entry, dict) else entry

    def handle_external_update(self, topic: str, value: Any, source: str = "EXTERNAL", metadata: dict = None):
        """
        ⚡ CENTRALIZED ROUTER: Directly injects a state change from any protocol.
        Pipes to the ProtocolRouter for deep inspection and broadcast.
        """
        from workers.logic.manifest.builder import create_manifest
        payload = create_manifest(value, topic, source, metadata)
        
        # 1. Update In-Memory Cache and schedule Disk Persistence
        self.cache[topic] = payload
        self._save_queue.put((topic, payload))
        self._update_prefix_set_single(topic)
        
        # 2. Pipe to Central Protocol Router (Hub & Spoke)
        from workers.Command_Router.protocol_router import ProtocolRouter
        ProtocolRouter.get_instance().ingest(source, topic, value, payload)

        # 3. Synchronize to MQTT Broker (The primary bus)
        # ⚡ BROADCAST: Publish to MQTT if this is a local GUI change OR a Hardware event from CORE
        if self.mqtt_connection_manager:
            # ⚡ LOOP PREVENTION: Never publish internal System Monitor traffic to the broker
            if "/System/Monitor/" in topic:
                pass 
            elif source == "GUI" or (source in ["MIDI", "SNMP", "OSC", "VISA"] and not self.state_mirror_engine):
                self.mqtt_connection_manager.publish(topic, orjson.dumps(payload).decode())

        # 4. Notify Protocol Observers (Local UI, etc.)
        for observer in self._observers:
            try: observer(topic, payload)
            except: pass

    def handle_incoming_mqtt(self, client, userdata, msg: MqttMessage) -> None:
        """
        ⚡ CENTRALIZED ROUTER: Processes incoming MQTT traffic.
        Pipes to the ProtocolRouter for deep inspection.
        """
        topic = msg.topic

        # Dispatch to the subscriber router for wildcard/exact callback matching
        if self.subscriber_router:
            self.subscriber_router._on_message(client, userdata, msg)

        # Extract payload and metadata
        try:
            # 1. ALWAYS Pipe to Central Protocol Router for live monitoring (DPI)
            # We do this BEFORE the traffic controller so we see EVERYTHING in the firehose
            raw_payload = msg.get_json_payload()
            meta = {}
            source = "MQTT"
            val = raw_payload

            if isinstance(raw_payload, dict):
                source = str(raw_payload.get("source", "MQTT")).upper()
                val = raw_payload.get("val")
                # ⚡ IDENTITY PRESERVATION: Carry over full payload as metadata
                meta = raw_payload.copy()
                
                # ⚡ SPEC PROMOTION: Ensure spec fields are at top level for Router logic
                for field in ["msg_type", "msg_guid", "origin_source", "is_settled", "full_id", "boot"]:
                    if field in raw_payload:
                        meta[field] = raw_payload[field]

            from workers.Command_Router.protocol_router import ProtocolRouter
            ProtocolRouter.get_instance().ingest("MQTT", topic, val, meta)

            # 2. Notify Protocol Observers (Local UI monitors, etc.)
            for observer in self._observers:
                try: observer(topic, raw_payload)
                except: pass

            # 3. State Cache Filtering (Purity Check)
            should_process, new_payload = cache_traffic_controller.process_traffic(msg, self.cache)
            if should_process:
                # Ensure source is tagged
                source = str(new_payload.get("source", "MQTT")).upper() if isinstance(new_payload, dict) else "MQTT"
                
                self.cache[topic] = new_payload
                self._update_prefix_set_single(topic)
                
                self._updates_since_last_log += 1
                now = time.time()
                if now - self._last_log_time >= 5.0:
                    if LOCAL_DEBUG:
                        data_logger.success(
                            f"🧠⚓💾 [CACHE] State Mirror: "
                            f"{self._updates_since_last_log} variables synced."
                        )
                    self._last_log_time, self._updates_since_last_log = now, 0
                self._save_queue.put((topic, new_payload))

            # 4. Standard MQTT Dispatch
            if self.subscriber_router:
                self.subscriber_router._on_message(client, userdata, msg)
        except Exception:
             data_logger.exception(
                 f"🧠💾❌ [ERROR] Error handling MQTT for {topic}"
             )

    def _update_prefix_set_single(self, topic: str):
        """⚡ OPTIMIZATION: Incrementally update prefix set for a single topic."""
        parts = topic.split('/')
        for i in range(1, len(parts)):
            self._active_prefixes.add('/'.join(parts[:i]) + '/')
