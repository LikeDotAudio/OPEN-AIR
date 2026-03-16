# workers/logic/state_mirror_engine.py
#
# facilitators bidirectional synchronization between local UI and MQTT.
# Version 20260315.Modular.1

import orjson
import time
import tkinter as tk
import contextlib
import threading
from loguru import logger

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from workers.logger.logger import initialize_logging, set_log_directory
state_logger = logger.bind(subsystem="STATE_ENGINE")

from managers.configini.config_reader import Config
from workers.Command_Router.mqtt.mqtt_message import MqttMessage
app_constants = Config.get_instance()

from workers.Command_Router.mqtt import mqtt_publisher_service

# --- EXTRACTED CORE MODULES ---
from workers.logic.core.topic_calculator import TopicCalculator
from workers.logic.core.registry_mixin import RegistryMixin
from workers.logic.core.sync_queue_mixin import SyncQueueMixin
from workers.logic.core.value_processor import ValueProcessor

class StateMirrorEngine(RegistryMixin, SyncQueueMixin):
    """
    Orchestrates GUI state mirroring with MQTT using a modular architecture.
    """

    def __init__(self, base_topic, subscriber_router, root, state_cache_manager):
        self.base_topic = base_topic
        self.subscriber_router = subscriber_router
        self.root = root
        self.state_cache_manager = state_cache_manager
        
        self.topic_calculator = TopicCalculator(base_topic)
        self._initialize_registry()
        self._initialize_queues()

        self.is_inert = (root is None)
        self.GUID = app_constants.INSTANCE_GUID
        
        self._silent_update = False
        self._suppress_broadcast = False
        self._binding_suspended = False
        self._last_global_broadcast_ts = 0
        self._GLOBAL_THROTTLE_MS = 0.020 

    def shutdown(self):
        self._registration_queue.put(None)
        if self._reg_thread.is_alive():
            self._reg_thread.join(timeout=2.0)

    @contextlib.contextmanager
    def suspend_bindings(self):
        self._binding_suspended = True
        try: yield
        finally: self._binding_suspended = False

    def register_widget(self, widget_id, tk_variable, tab_name, config, update_callback=None, instance=None):
        if self.is_inert: return None
        
        dynamics = config.get("dynamics", {})
        topic_override = dynamics.get("path") or dynamics.get("sub")
        full_topic = self.topic_calculator.calculate(topic_override or widget_id, tab_name)

        info = {
            "var": tk_variable, "tab": tab_name, "id": widget_id,
            "config": config, "update_callback": update_callback,
            "topic": full_topic, "last_broadcast_ts": 0,
            "last_sent_val": None, "instance": instance
        }
        self._register_to_internal_dicts(widget_id, info)
            
        def _auto_broadcast(*args):
            if not self._silent_update and not self._binding_suspended:
                 self.broadcast_gui_change_to_mqtt(widget_id)
        
        tk_variable.trace_add("write", _auto_broadcast)
        self._registration_queue.put(widget_id)
        return full_topic

    def initialize_widget_state(self, widget_id):
        widget_info = self._get_widget_info(widget_id)
        if not widget_info or not self.state_cache_manager: return False
        
        full_topic = widget_info["topic"]
        if full_topic not in self.state_cache_manager.cache: return False
        
        cached = self.state_cache_manager.cache[full_topic]
        try:
            data = cached if isinstance(cached, (dict, list)) else orjson.loads(cached)
            raw_val = ValueProcessor.extract_value(data, widget_info["config"])
            final_val = ValueProcessor.normalize(raw_val, widget_info["var"], widget_info["config"])

            if final_val is not None:
                widget_info["last_sent_val"] = final_val
                self.update_queue.put((widget_info["var"], final_val, widget_id))
                self._schedule_queue_processing() 
                if widget_info["update_callback"]:
                    self.root.after(0, lambda: self._safe_execute_callback(widget_info["update_callback"], data, widget_id))
            return True
        except Exception as e:
            state_logger.error(f"Failed to initialize widget state for {widget_id}: {e}")
            return False

    def broadcast_gui_change_to_mqtt(self, widget_id, extra_payload=None):
        if not widget_id or self.is_inert or self._suppress_broadcast or self._silent_update or self._binding_suspended:
            return
            
        if "/visibility/" in widget_id or "/left_meter" in widget_id or "/right_meter" in widget_id:
            return

        widget_info = self._get_widget_info(widget_id)
        if not widget_info: return
        
        # ⚡ AUTO-METADATA: Extract interaction state from widget instance
        instance = widget_info.get("instance")
        is_locked = getattr(instance, "is_locked", False)
        is_settled = not getattr(instance, "is_sliding", False)
        
        metadata = extra_payload or {}
        if "LOCKED" not in metadata: metadata["LOCKED"] = is_locked
        if "SETTLED" not in metadata: metadata["SETTLED"] = is_settled
        
        now = time.time()
        if (now - self._last_global_broadcast_ts) < self._GLOBAL_THROTTLE_MS: return
        if (now - widget_info.get("last_broadcast_ts", 0)) < 0.050: return
        
        try:
            current_val = widget_info["var"].get()
        except Exception as e:
            state_logger.error(f"Failed to get value for widget {widget_id}: {e}")
            return

        if current_val == widget_info.get("last_sent_val"): return

        widget_info["last_sent_val"] = current_val
        widget_info["last_broadcast_ts"] = now
        self._last_global_broadcast_ts = now
        
        if self.state_cache_manager:
            self.state_cache_manager.handle_external_update(widget_info["topic"], current_val, source="GUI", metadata=metadata)
        else:
            from workers.logic.manifest.builder import create_manifest
            payload = create_manifest(current_val, widget_info["topic"], "GUI", metadata)
            mqtt_publisher_service.publish_payload(widget_info["topic"], orjson.dumps(payload).decode())

    def sync_incoming_mqtt_to_gui(self, msg: MqttMessage):
        if self.is_inert or not msg.payload: return
        try:
            data = msg.payload if isinstance(msg.payload, (dict, list)) else orjson.loads(msg.payload)
            if not isinstance(data, dict): return
            
            from workers.logic.manifest.echo_canceller import is_echo
            if is_echo(data): return

            widget_id = self.topic_to_widget_id.get(msg.topic)
            widget_info = self._get_widget_info(widget_id) if widget_id else None
            if not widget_info: return
            
            from workers.logic.manifest.ghost_lock import is_ghost_touch_locked
            if is_ghost_touch_locked(data, widget_info.get("instance")): return
                
            raw_val = ValueProcessor.extract_value(data, widget_info["config"])
            final_val = ValueProcessor.normalize(raw_val, widget_info["var"], widget_info["config"])

            if final_val is not None:
                widget_info["last_sent_val"] = final_val
                if data.get("origin_source") == widget_id:
                    self._silent_update = True
                    try: widget_info["var"].set(final_val)
                    finally: self._silent_update = False
                else:
                    self.update_queue.put((widget_info["var"], final_val, widget_id))
                    self._schedule_queue_processing()
                
                if widget_info["update_callback"]:
                    self.root.after(0, lambda: self._safe_execute_callback(widget_info["update_callback"], data, widget_id))
        except Exception as e:
            state_logger.error(f"Error syncing incoming MQTT to GUI for topic {msg.topic}: {e}")

    def _safe_execute_callback(self, callback, data, widget_id):
        self._silent_update = True
        try:
            callback(data)
        except Exception as e:
            state_logger.error(f"Error executing callback for widget {widget_id}: {e}")
        finally:
            self._silent_update = False

    def calculate_topic(self, widget_id: str, tab_name: str) -> str:
        """Shim for backward compatibility with legacy widget callers."""
        return self.topic_calculator.calculate(widget_id, tab_name)

    def publish_command(self, topic: str, payload: str):
        if not self.is_inert and not self._silent_update:
            mqtt_publisher_service.publish_payload(topic, payload)
