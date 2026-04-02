# Core/state_cache.py
#
# Modularized State Cache Management. Acts as the central orchestrator 
# for application state caching, persistence, and distribution.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version: 20260331.2225.1

import time
import os
from typing import Any
from loguru import logger
import orjson

LOCAL_DEBUG = False

try:
    from oastateregistry_rs import StateRegistryCore as RustStateRegistry
except ImportError as e:
    logger.critical("🚀❌ [FATAL] Rust State Registry module missing. Pure Rust mode is mandatory.")
    raise e

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import data_logger
from oaLogging.Methods.matrix_gate import matrix_log
from oaConfiguration.FileReaders.config_reader import Config
from oaComMQTT.Core.mqtt_message import MqttMessage
app_constants = Config.get_instance()

# --- EXTRACTED CORE MODULES ---
from ..FileReaders import cache_io_handler
from ..Managers import cache_traffic_controller
from ..Methods import gui_state_restorer
from ..FileReaders.cache_io_handler import CacheLoadError
from .cache_save_engine import CacheSaveEngine
from .cache_search_engine import CacheSearchEngine
from .cache_observer_registry import CacheObserverRegistry

class StateRegistry:
    """The central orchestrator for application state caching, persistence, and distribution."""

    def __init__(self, mqtt_connection_manager: Any, state_mirror_engine: Any = None):
        self.mqtt = mqtt_connection_manager
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = None
        
        # 1. Initialize Cache & Search
        try:
            self.rust_cache = RustStateRegistry()
            matrix_log("core", "data", "__init__", "🚀 Using HIGH-PERFORMANCE RUST state cache.", "DEBUG")
        except Exception as e:
            matrix_log("core", "data", "__init__", f"🚀❌ [FATAL] Rust Cache init failed: {e}", "ERROR")
            raise e

        self.initialize_state()
            
        self.search_engine = CacheSearchEngine()
        self.search_engine.rebuild(self.rust_cache.to_dict())
        
        # 2. Specialized Engines
        self.save_engine = CacheSaveEngine(self.rust_cache, data_logger, LOCAL_DEBUG)
        self.observers = CacheObserverRegistry()
        
        self._last_log_time, self._updates_since_last_log = time.time(), 0
        cache_len = self.rust_cache.len()
        matrix_log("core", "data", "__init__", f"Initialized with {cache_len} entries.", "DEBUG")

    def check_prefix_exists(self, prefix: str) -> bool: return self.search_engine.exists(prefix)
    def register_cache_observer(self, callback: Any): self.observers.register_observer(callback)
    
    def get_cached_value(self, topic: str) -> Any:
        """Retrieves a value from the cache."""
        entry = self.rust_cache.get(topic)
        return entry.get("val") if isinstance(entry, dict) else entry

    def save_preset(self, name: str):
        try:
            path = os.path.join(app_constants.PRESET_REPO_PATH, f"{name}.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            export_cache = self.rust_cache.to_dict()
            with open(path, "wb") as f: f.write(orjson.dumps(export_cache, option=orjson.OPT_INDENT_2))
            matrix_log("core", "data", "save_preset", f"Preset saved: {name}", "SUCCESS")
            return True
        except Exception as e: 
            matrix_log("core", "data", "save_preset", f"Preset failed: {e}", "ERROR")
            return False

    def shutdown(self): self.save_engine.shutdown()

    def subscribe_to_all_topics(self):
        """Subscribes to the root command and transmission topic filters."""
        if self.mqtt:
            base = app_constants.MQTT_BASE_TOPIC
            roots = [f"{base}/Cmd/#", f"{base}/Tx/#", f"{base}/System/Status/#", f"{base}/System/Monitor/#"]
            
            for root in roots:
                matrix_log("core", "data", "subscribe_to_all_topics", f"Subscribing to system root: {root}", "DEBUG")
                self.mqtt.subscribe(root)

    def initialize_state(self) -> None:
        try:
            loaded_cache = cache_io_handler.load_cache()
            self.rust_cache.clear()
            self.rust_cache.update(loaded_cache)
        except FileNotFoundError:
            matrix_log("core", "data", "initialize_state", "No cache to initialize.", "INFO")
            self.rust_cache.clear()
        except CacheLoadError as e:
            matrix_log("core", "data", "initialize_state", f"Critical Cache Corruption during init: {e}.", "ERROR")
            self.rust_cache.clear()
        except Exception as e: 
            matrix_log("core", "data", "initialize_state", f"State initialization failed: {e}", "ERROR")
            self.rust_cache.clear()

        current_cache = self.rust_cache.to_dict()
        if current_cache:
            from oaComBroker.Core.protocol_router.manager import ProtocolRouter
            router = ProtocolRouter.get_instance()
            for topic, payload in current_cache.items():
                val = payload.get("val") if isinstance(payload, dict) else payload
                router.ingest("DISK", topic, val, {"msg_type": "LINK_FEEDBACK", "is_settled": True, "origin_source": "DISK", "boot": True})
            gui_state_restorer.restore_timeline(current_cache, self.state_mirror_engine)

    def handle_external_update(self, topic: str, value: Any, source: str = "EXTERNAL", metadata: dict = None):
        from oaTranslator.Core.manifest.builder import create_manifest
        payload = create_manifest(value, topic, source, metadata)
        
        self.rust_cache.set(topic, payload)
        
        self.save_engine.schedule_save(topic, payload); self.search_engine.add_topic(topic)
        
        from oaComBroker.Core.protocol_router.manager import ProtocolRouter
        ProtocolRouter.get_instance().ingest(source, topic, value, payload)

        self.observers.notify(topic, payload)

    def _parse_mqtt_payload(self, msg: MqttMessage):
        """Standardizes MQTT payload extraction into source, value, and metadata."""
        raw = msg.get_json_payload()
        source, value, metadata = "MQTT", raw, {}
        
        if isinstance(raw, dict):
            if "val" in raw or "value" in raw:
                source = str(raw.get("source", "MQTT")).upper()
                value = raw.get("val") if "val" in raw else raw.get("value")
                metadata = raw.copy()
                for field in ["msg_type", "msg_guid", "origin_source", "is_settled", "full_id", "boot"]:
                    if field in raw: metadata[field] = raw[field]
            else:
                value = raw
                source = "MQTT"
                metadata = {}
        
        return source, value, metadata, raw

    def _update_cache_entry(self, topic, payload):
        """Updates internal cache and schedules persistence."""
        self.rust_cache.set(topic, payload)
        
        self.search_engine.add_topic(topic)
        self.save_engine.schedule_save(topic, payload)
        self._updates_since_last_log += 1
        
        if time.time() - self._last_log_time >= 5.0:
            matrix_log("core", "data", "_update_cache_entry", f"State synced: {self._updates_since_last_log} variables.", "SUCCESS")
            self._last_log_time, self._updates_since_last_log = time.time(), 0

    def handle_incoming_mqtt(self, client, userdata, msg: MqttMessage) -> None:
        topic = msg.topic
        base = app_constants.MQTT_BASE_TOPIC
        normalized = False
        if f"{base}/Cmd/" in topic:
            topic = topic.replace(f"{base}/Cmd/", f"{base}/")
            normalized = True
        elif f"{base}/Tx/" in topic:
            topic = topic.replace(f"{base}/Tx/", f"{base}/")
            normalized = True

        if normalized:
            msg = MqttMessage(
                topic=topic,
                payload=msg.payload,
                qos=msg.qos,
                retain=msg.retain
            )
            
        if self.subscriber_router: 
            self.subscriber_router._on_message(client, userdata, msg)
            
        try:
            source, value, metadata, raw_payload = self._parse_mqtt_payload(msg)

            from oaComBroker.Core.protocol_router.manager import ProtocolRouter
            ProtocolRouter.get_instance().ingest("MQTT", topic, value, metadata)
            self.observers.notify(topic, raw_payload)

            should_process, new_payload = cache_traffic_controller.process_traffic(msg, self.rust_cache)
            if should_process:
                self._update_cache_entry(topic, new_payload)
                
        except Exception: 
            matrix_log("core", "data", "handle_incoming_mqtt", f"Error handling MQTT for {topic}", "ERROR")
