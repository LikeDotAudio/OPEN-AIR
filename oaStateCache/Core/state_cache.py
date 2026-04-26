# oaStateCache/Core/state_cache.py
#
# Modularized State Cache Management. Acts as the central orchestrator
# for application state caching, persistence, and distribution.
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
# Version 20260406.2010.1

from __future__ import annotations

import copy
import logging
import os
import time
from typing import Any

import orjson

# --- RUST ACCELERATION LAYER (PyO3) ---

LOCAL_DEBUG = False

try:
    from oaRustCore.oa_state_registry_rs import StateRegistryCore as RustStateRegistry
    HAS_RUST = True
except ImportError:
    logging.warning("⚠️ [STATE_CACHE] oastateregistry_rs not found. "
                    "Falling back to slow Python state registry.")
    HAS_RUST = False
except Exception as e:
    logging.error(f"❌ [STATE_CACHE] Failed to initialize Rust Registry: {e}")
    HAS_RUST = False

class PythonStateRegistry:
    """Standard Python dictionary fallback for environments lacking Rust."""
    def __init__(self): self._data = {}
    def set(self, k, v):
        # ⚡ V3.1.23 RECURSION GUARD:
        # Block corrupted topics with repeated protocol tokens.
        if any(x + "/" + x + "/" in str(k) for x in ["OSC", "MIDI", "GUI", "oaGui", "MQTT"]):
            return
        self._data[k] = v
    def get(self, k): return self._data.get(k)
    def len(self): return len(self._data)
    def clear(self): self._data.clear()
    def update(self, d): self._data.update(d)
    def to_dict(self): return copy.deepcopy(self._data)
    def items(self): return self._data.items()

# --- Standard Debug Logging Setup ---
from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Core.logger import data_logger
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

# --- EXTRACTED CORE MODULES ---
from ..FileReaders import cache_io_handler
from ..FileReaders.cache_io_handler import CacheLoadError
from ..Managers import cache_traffic_controller
from ..Methods import gui_state_restorer
from .cache_observer_registry import CacheObserverRegistry
from .cache_save_engine import CacheSaveEngine
from .cache_search_engine import CacheSearchEngine


class StateRegistry:
    """
    The central orchestrator for application state caching and distribution.

    Responsibilities:
        - Atomic Persistence: Manages high-speed disk flushes via Rust core.
        - State Mirroring: Synchronizes MQTT fabric with local memory.
        - Observation: Notifies UI components of external state changes.
        - Search: Provides prefix-based lookup for partial topic matching.

    Constraints:
        - Operates within the Core Partition (Data Layer).
        - Requires 'oaStateCache.Methods.oaStateRegistry_rs' for performance.
        - Single instance enforced via the Manager pattern.
    """

    def __init__(self, mqtt_connection_manager: Any, state_mirror_engine: Any = None):
        """
        Initializes the state registry and prepares persistence engines.

        Args:
            mqtt_connection_manager: Global handler for network egress.
            state_mirror_engine (optional): UI-facing sync engine.
        """
        self.mqtt = mqtt_connection_manager
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = None

        # 1. Initialize High-Performance Storage
        if HAS_RUST:
            try:
                self.rust_cache = RustStateRegistry()
                matrix_log("core", "data", "__init__",
                           "🚀 [START] Using HIGH-PERFORMANCE RUST state cache.",
                           "DEBUG")
            except Exception as e:
                matrix_log("core", "data", "__init__",
                           f"🚀❌ [FATAL] Rust Cache init failed: {e}. "
                           "Falling back to Python.", "ERROR")
                self.rust_cache = PythonStateRegistry()
        else:
            self.rust_cache = PythonStateRegistry()

        self.initialize_state()

        self.search_engine = CacheSearchEngine()
        self.search_engine.rebuild(self.rust_cache.to_dict())

        # 2. Specialized Egress Engines
        self.save_engine = CacheSaveEngine(self.rust_cache, data_logger,
                                          LOCAL_DEBUG)
        self.observers = CacheObserverRegistry()

        self._last_log_time, self._updates_since_last_log = time.time(), 0
        cache_len = self.rust_cache.len()
        matrix_log("core", "data", "__init__",
                   f"✅ [READY] Initialized with {cache_len} entries.", "DEBUG")

    def check_prefix_exists(self, prefix: str) -> bool:
        """Fast lookup for topic namespaces."""
        return self.search_engine.exists(prefix)

    def register_cache_observer(self, callback: Any):
        """Binds a listener to global state update events."""
        self.observers.register_observer(callback)

    def get_cached_value(self, topic: str) -> Any:
        """
        Retrieves a value from the cache with dictionary unwrapping.

        Args:
            topic (str): The canonical MQTT topic key.

        Returns:
            Any: The literal value ('value' field) or raw payload.
        """
        entry = self.rust_cache.get(topic)
        return entry.get("value") if isinstance(entry, dict) else entry

    def set_value(self, topic: str, payload: Any) -> bool:
        """
        Commits a topic and payload to the registry with a recursion guard.
        
        Returns:
            bool: True if the value was committed, False if rejected by guard.
        """
        # ⚡ V3.1.23 RECURSION GUARD:
        # Block corrupted topics with repeated protocol tokens (e.g., OSC/OSC/).
        if any(x + "/" + x + "/" in str(topic) for x in ["OSC", "MIDI", "GUI", "oaGui", "MQTT"]):
            if app_constants.ROUTER_INGEST_LOGS:
                matrix_log("core", "data", "set_value", f"🛡️ [GUARD] Rejecting corrupted recursive topic: {topic}", "DEBUG")
            return False

        self.rust_cache.set(topic, payload)
        return True

    def save_preset(self, name: str):
        """
        Exports the current global state to a JSON preset file.

        Args:
            name (str): Unique filename for the snapshot.

        Returns:
            bool: True if the file was written to the preset repo.
        """
        try:
            path = os.path.join(app_constants.PRESET_REPO_PATH, f"{name}.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            export_cache = self.rust_cache.to_dict()
            with open(path, "wb") as f:
                f.write(orjson.dumps(export_cache, option=orjson.OPT_INDENT_2))
            matrix_log("core", "data", "save_preset", f"💾 [SAVE] Preset: {name}",
                       "SUCCESS")
            return True
        except Exception as e:
            matrix_log("core", "data", "save_preset", f"❌ [SAVE] Failed: {e}",
                       "ERROR")
            return False

    def clear_all_state(self):
        """
        Wipes the in-memory state registry and rebuilds the search engine.
        Used by system purge routines to ensure memory doesn't overwrite a deleted disk cache.
        """
        self.rust_cache.clear()
        self.search_engine.rebuild({})
        matrix_log("core", "data", "clear_all_state", "🗑️ [CACHE] In-memory state registry cleared.", "INFO")

    def shutdown(self):
        """Gracefully terminates the save engine threads."""
        self.save_engine.shutdown()

    def subscribe_to_all_topics(self):
        """Standardized subscription to system-critical MQTT roots."""
        if self.mqtt:
            base = app_constants.MQTT_BASE_TOPIC
            roots = [
                f"{base}/Cmd/#", f"{base}/Tx/#", f"{base}/System/Status/#",
                f"{base}/System/Monitor/#", f"{base}/System/Control/#",
                f"{base}/Assets/#", f"{base}/Spectrum/#", f"{base}/GUI/#",
                f"{base}/oaGui/#", f"{base}/MIDI/#", f"{base}/OSC/#",
                f"{base}/NMOS/#", f"{base}/AES70/#", f"{base}/SMPTE2138/#",
                f"{base}/EMBER/#"
            ]

            for root in roots:
                matrix_log("core", "data", "subscribe_to_all_topics",
                           f"🎧 [LISTEN] Root: {root}", "DEBUG")
                self.mqtt.subscribe(root)

    def initialize_state(self) -> None:
        """
        Loads the persistent cache from disk and populates the registry.

        Side Effects:
            - Performs blocking I/O.
            - Updates the StateMirrorEngine if attached.
        """
        try:
            loaded_cache = cache_io_handler.load_cache()
            self.rust_cache.clear()

            # ⚡ V3.1.23 PURITY CHECK:
            # Filter the loaded cache to remove any legacy recursive entries.
            clean_cache = {}
            for t, p in loaded_cache.items():
                if self.set_value(t, p):
                    clean_cache[t] = p

        except FileNotFoundError:
            matrix_log("core", "data", "initialize_state",
                       "🪣 [CACHE] No cache to initialize.", "INFO")
            self.rust_cache.clear()
            clean_cache = {}
        except CacheLoadError as e:
            matrix_log("core", "data", "initialize_state",
                       f"🔥 [OUTAGE] Cache Corruption: {e}.", "ERROR")
            self.rust_cache.clear()
            clean_cache = {}
        except Exception as e:
            matrix_log("core", "data", "initialize_state",
                       f"❌ [INIT] State failure: {e}", "ERROR")
            self.rust_cache.clear()
            clean_cache = {}

        if clean_cache:
            # ⚡ ARCHITECTURAL PURITY:
            # The State Cache is NOT a router input. We populate the local memory
            # and search engine, but we do NOT ingest these values into the
            # Protocol Router's event pipeline.
            # Mirroring to UI remains for immediate visibility.
            gui_state_restorer.restore_timeline(clean_cache,
                                                self.state_mirror_engine)

    def handle_external_update(self, topic: str, value: Any,
                               source: str = "EXTERNAL", metadata: dict = None):
        """
        Wraps a raw update into a manifest and commits it to the registry.

        Args:
            topic (str): MQTT topic path.
            value (Any): The new literal value.
            source (str): Origin identifier (e.g. 'GUI', 'VISA').
            metadata (dict): Optional identity tags for the manifest.
        """
        from oaStateCache.Core.manifest.builder import create_manifest
        payload = create_manifest(value, topic, source, metadata)

        self.rust_cache.set(topic, payload)
        self.save_engine.schedule_save(topic, payload)
        self.search_engine.add_topic(topic)

        from oaComBroker.Core.protocol_router.manager import ProtocolRouter
        ProtocolRouter.get_instance().ingest(source, topic, value, payload)

        self.observers.notify(topic, payload)

    def _parse_mqtt_payload(self, message: MqttMessage):
        """Standardizes MQTT payload extraction into source, value, and metadata."""
        raw = message.get_json_payload()
        source, value, metadata = "MQTT", raw, {}

        if isinstance(raw, dict):
            if "value" in raw or "value" in raw:
                source = str(raw.get("source", "MQTT")).upper()
                value = raw.get("value") if "value" in raw else raw.get("value")
                metadata = raw.copy()
                for field in ["message_type", "message_guid", "origin_source",
                              "is_settled", "full_id", "boot"]:
                    if field in raw: metadata[field] = raw[field]
            else:
                value = raw
                source = "MQTT"
                metadata = {}

        return source, value, metadata, raw

    def _update_cache_entry(self, topic, payload):
        """Internal atomic update for local memory and search tree."""
        if not self.set_value(topic, payload):
            return

        self.search_engine.add_topic(topic)
        self.save_engine.schedule_save(topic, payload)
        self._updates_since_last_log += 1

        # Forensic logging throttle.
        if time.time() - self._last_log_time >= 5.0:
            matrix_log("core", "data", "_update_cache_entry",
                       f"🔄 [SYNC] Synchronized: {self._updates_since_last_log} "
                       "variables.", "SUCCESS")
            self._last_log_time, self._updates_since_last_log = time.time(), 0

    def handle_incoming_mqtt(self, client, userdata, message: MqttMessage) -> None:
        """
        Primary MQTT ingestion hook.

        Normalizes topic paths (stripping Cmd/Tx prefixes) and updates the 
        cache based on traffic controller policy.

        Args:
            message (MqttMessage): Incoming network package.
        """
        topic = message.topic
        base = app_constants.MQTT_BASE_TOPIC
        normalized = False
        if f"{base}/Cmd/" in topic:
            topic = topic.replace(f"{base}/Cmd/", f"{base}/")
            normalized = True
        elif f"{base}/Tx/" in topic:
            topic = topic.replace(f"{base}/Tx/", f"{base}/")
            normalized = True

        if normalized:
            message = MqttMessage(topic=topic, payload=message.payload,
                              qos=message.qos, retain=message.retain)

        if self.subscriber_router:
            self.subscriber_router._on_message(client, userdata, message)

        # ⚡ EXCLUSION: Skip state ingestion for high-bandwidth ST2138 traffic.
        if topic.startswith("st2138/"):
            return

        try:
            source, value, metadata, raw_payload = self._parse_mqtt_payload(message)

            # ⚡ V3.1.25 GLOBAL PURGE COMMAND
            if topic.endswith("/System/Control/ClearCache"):
                if str(value).lower() in ["true", "1"]:
                    if app_constants.ROUTER_INGEST_LOGS:
                        matrix_log("core", "data", "handle_incoming_mqtt", "📡🗑️ [CACHE] Received global clear cache command over MQTT. Wiping memory.", "WARNING")
                    self.clear_all_state()
                return

            # ⚡ V3.1.16 REFLECTION DETECTION
            # Identify if this message was authored by the local instance.
            message_src_id = metadata.get("src") or metadata.get("full_id")
            is_reflection = (message_src_id == app_constants.FULL_INSTANCE_ID)

            if is_reflection:
                metadata["is_reflection"] = True
                if app_constants.ROUTER_INGEST_LOGS:
                    matrix_log("core", "data", "handle_incoming_mqtt", f"🛡️ [ECHO] Reflection detected for {topic}. Ingesting for visibility.", "TRACE")

            from oaComBroker.Core.protocol_router.manager import ProtocolRouter
            ProtocolRouter.get_instance().ingest("MQTT", topic, value, metadata)
            self.observers.notify(topic, raw_payload)

            # --- CACHE POLICY ---
            # Self-reflections are NOT committed to the local cache because we
            # already have the definitive state in memory (or will soon).
            if is_reflection:
                return

            should_process, new_payload = cache_traffic_controller.process_traffic(
                message, self.rust_cache)
            if should_process:
                if self.set_value(topic, new_payload):
                    self.search_engine.add_topic(topic)
                    self.save_engine.schedule_save(topic, new_payload)
                    self._updates_since_last_log += 1

        except Exception as e:
            import traceback
            error_message = f"🔥 Error handling MQTT for {topic}: {e}\n" \
                        f"{traceback.format_exc()}"
            matrix_log("core", "data", "handle_incoming_mqtt", error_message, "ERROR")
