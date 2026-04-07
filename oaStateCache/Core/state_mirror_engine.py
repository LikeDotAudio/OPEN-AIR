# oaTranslator/Core/state_mirror_engine.py
#
# Orchestrates bidirectional synchronization between the local GUI state 
# and the MQTT broker. Implements throttling and change-only filtering.
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
# Version 20260406.1930.1

import orjson
import time
import tkinter as tk
import contextlib
import threading
from loguru import logger

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
state_logger = logger.bind(subsystem="STATE_ENGINE")

from oaConfigurationManager.FileReaders.config_reader import Config
from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage
app_constants = Config.get_instance()

from oaComProtocols.oaComMQTT.Core import mqtt_publisher_service

# --- EXTRACTED CORE MODULES ---
from oaStateCache.Core.topic_calculator import TopicCalculator
from oaStateCache.Core.registry_mixin import RegistryMixin
from oaStateCache.Core.sync_queue_mixin import SyncQueueMixin
from oaStateCache.Core.value_processor import ValueProcessor

class StateMirrorEngine(RegistryMixin, SyncQueueMixin):
    """
    Manages the synchronization of GUI widget states with an MQTT broker.

    Responsibilities:
        - Bidirectional State Sync: Mirrors local UI variables to MQTT topics.
        - Throttling: Prevents flooding the broker with high-frequency UI events.
        - Change Filtering: Only broadcasts when the value meaningfully changes.
        - Registry Integration: Maintains a map of topics to UI widgets.

    Constraints:
        - Operates within the UI Partition.
        - Requires a valid 'root' Tkinter instance for thread-safe UI updates.
        - Depends on 'oaComProtocols.oaComMQTT' for network egress.
    """

    def __init__(self, base_topic, subscriber_router, root, state_cache_manager):
        """
        Initializes the state mirror engine.

        Args:
            base_topic (str): The root MQTT topic for this UI instance.
            subscriber_router: The router handling incoming MQTT subscriptions.
            root (tk.Tk): The primary Tkinter root for event loop scheduling.
            state_cache_manager: Local cache for initial state resolution.
        """
        self.base_topic = base_topic
        self.subscriber_router = subscriber_router
        self.root = root
        self.state_cache_manager = state_cache_manager
        
        self.topic_calculator = TopicCalculator(base_topic)
        self._initialize_registry()
        self._initialize_queues()

        # Inert mode allows head-less operation during tests or CLI mode.
        self.is_inert = (root is None)
        self.GUID = app_constants.FULL_INSTANCE_ID
        
        self._silent_update = False
        self._suppress_broadcast = False
        self._binding_suspended = False
        self._last_global_broadcast_ts = 0
        self._GLOBAL_THROTTLE_MS = 0.020 

    def shutdown(self):
        """
        Gracefully terminates background registration and sync threads.

        Side Effects:
            - Joins the registration thread.
            - Logs the shutdown status.
        """
        self._registration_queue.put(None)
        if self._reg_thread.is_alive():
            self._reg_thread.join(timeout=2.0)
        matrix_log("ui", "state_mirror", "shutdown", 
                   "⏹️ [STOPPED] StateMirrorEngine shutdown complete.", "INFO")

    @contextlib.contextmanager
    def suspend_bindings(self):
        """
        Context manager to temporarily ignore UI trace events.

        Use this during batch updates to prevent feedback loops.
        """
        self._binding_suspended = True
        try:
            yield
        finally:
            self._binding_suspended = False

    def register_widget(self, widget_id, tk_variable, tab_name, config, 
                        update_callback=None, instance=None):
        """
        Links a UI widget's variable to an MQTT topic.

        Args:
            widget_id (str): Unique identifier for the widget.
            tk_variable (tk.Variable): The Tkinter variable to track.
            tab_name (str): The UI tab context for topic calculation.
            config (dict): The widget's JSON definition/manifest.
            update_callback (callable, optional): Invoked on external changes.
            instance (object, optional): Reference to the widget class instance.

        Returns:
            str: The fully qualified MQTT topic mapped to this widget.
        """
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
            # Automated hook into Tkinter's trace system.
            if not self._silent_update and not self._binding_suspended:
                 self.broadcast_gui_change_to_mqtt(widget_id)
        
        tk_variable.trace_add("write", _auto_broadcast)
        self._registration_queue.put(widget_id)
        return full_topic

    def initialize_widget_state(self, widget_id):
        """
        Polls the local cache to set the widget's initial visual state.

        Args:
            widget_id (str): The ID of the widget to initialize.

        Returns:
            bool: True if initial state was successfully applied from cache.
        """
        widget_info = self._get_widget_info(widget_id)
        if not widget_info or not self.state_cache_manager: return False
        
        full_topic = widget_info["topic"]
        cached = self.state_cache_manager.rust_cache.get(full_topic)
        if cached is None: return False
        
        try:
            data = cached if isinstance(cached, (dict, list)) else orjson.loads(cached)
            raw_val = ValueProcessor.extract_value(data, widget_info["config"])
            final_val = ValueProcessor.normalize(raw_val, widget_info["var"], 
                                                widget_info["config"])

            if final_val is not None:
                widget_info["last_sent_val"] = final_val
                self.update_queue.put((widget_info["var"], final_val, widget_id))
                self._schedule_queue_processing() 
                if widget_info["update_callback"]:
                    self.root.after(0, lambda: self._safe_execute_callback(
                        widget_info["update_callback"], data, widget_id))
            return True
        except Exception as e:
            matrix_log("ui", "state_mirror", "initialize_widget_state", 
                       f"❌ [CACHE] Init failure for {widget_id}: {e}", "ERROR")
            return False

    def announce_all_widgets(self):
        """
        Forces a full broadcast of all local UI states to the broker.

        Typically used on startup or network reconnection to ensure the 
        Core partition is synchronized with the current UI.
        """
        if self.is_inert or self._suppress_broadcast: return
        
        matrix_log("ui", "state_mirror", "announce_all_widgets", 
                   "🗣️ [YELLING] Announcing full system state...", "INFO")
        
        self._last_global_broadcast_ts = 0
        
        for widget_id in list(self.registered_widgets.keys()):
            widget_info = self._get_widget_info(widget_id)
            if not widget_info: continue
            widget_info["last_broadcast_ts"] = 0
            self.broadcast_gui_change_to_mqtt(widget_id, extra_payload={"boot": True})

    def broadcast_gui_change_to_mqtt(self, widget_id, extra_payload=None):
        """
        Calculates and publishes a local UI change to the MQTT broker.

        Implements throttling and settled-state logic to minimize network 
        chatter during active user interaction (e.g., sliding a fader).

        Args:
            widget_id (str): The identifier of the widget that changed.
            extra_payload (dict, optional): Metadata to merge into the manifest.
        """
        if not widget_id or self.is_inert or self._suppress_broadcast or \
           self._silent_update or self._binding_suspended:
            return
            
        # Ignore high-frequency internal metadata topics.
        if "/visibility/" in widget_id or "/left_meter" in widget_id or \
           "/right_meter" in widget_id:
            return

        widget_info = self._get_widget_info(widget_id)
        if not widget_info: return
        
        instance = widget_info.get("instance")
        is_locked = getattr(instance, "is_locked", False)
        is_settled = not getattr(instance, "is_sliding", False)
        
        metadata = extra_payload or {}
        if "LOCKED" not in metadata: metadata["LOCKED"] = is_locked
        if "SETTLED" not in metadata: metadata["SETTLED"] = is_settled

        # --- Structural Identity Injection ---
        cfg = widget_info.get("config", {})
        if "bin_id" in cfg: metadata["bin_id"] = cfg["bin_id"]
        if "block_name" in cfg: metadata["block_name"] = cfg["block_name"]
        if "field_name" in cfg: metadata["field_name"] = cfg["field_name"]
        
        now = time.time()
        # Global and per-widget throttling gates.
        if (now - self._last_global_broadcast_ts) < self._GLOBAL_THROTTLE_MS: return
        if (now - widget_info.get("last_broadcast_ts", 0)) < 0.050: return
        
        try:
            current_val = widget_info["var"].get()
        except Exception as e:
            matrix_log("ui", "state_mirror", "broadcast_gui_change_to_mqtt", 
                       f"❌ [GUI] Value retrieval failure for {widget_id}: {e}", 
                       "ERROR")
            return

        # Change-only filter.
        if current_val == widget_info.get("last_sent_val"): return

        widget_info["last_sent_val"] = current_val
        widget_info["last_broadcast_ts"] = now
        self._last_global_broadcast_ts = now
        
        # Route through cache manager if available, otherwise publish direct.
        if self.state_cache_manager:
            self.state_cache_manager.handle_external_update(
                widget_info["topic"], current_val, source="GUI", metadata=metadata)
        else:
            from oaStateCache.Core.manifest.builder import create_manifest
            payload = create_manifest(current_val, widget_info["topic"], 
                                      "GUI", metadata)
            mqtt_publisher_service.publish_payload(
                widget_info["topic"], orjson.dumps(payload).decode())

    def sync_incoming_mqtt_to_gui(self, msg: MqttMessage):
        """
        Parses an incoming MQTT message and updates the corresponding UI widget.

        Args:
            msg (MqttMessage): The raw message from the broker.
        """
        if self.is_inert or not msg.payload: return
        try:
            data = msg.payload if isinstance(msg.payload, (dict, list)) else orjson.loads(msg.payload)
            if not isinstance(data, dict): return
            
            # Prevent feedback loops from our own broadcasts.
            from oaStateCache.Core.manifest.echo_canceller import is_echo
            if is_echo(data): return

            widget_id = self.topic_to_widget_id.get(msg.topic)
            widget_info = self._get_widget_info(widget_id) if widget_id else None
            if not widget_info: return
            
            # Prevent remote updates from overriding a widget currently 
            # under local user control (ghost-touch protection).
            from oaStateCache.Core.manifest.ghost_lock import is_ghost_touch_locked
            if is_ghost_touch_locked(data, widget_info.get("instance")): return
                
            raw_val = ValueProcessor.extract_value(data, widget_info["config"])
            final_val = ValueProcessor.normalize(raw_val, widget_info["var"], 
                                                widget_info["config"])

            if final_val is not None:
                widget_info["last_sent_val"] = final_val
                # If we are the origin (rare), set immediately. 
                # Otherwise, queue for the main thread.
                if data.get("origin_source") == widget_id:
                    self._silent_update = True
                    try: 
                        widget_info["var"].set(final_val)
                    finally: 
                        self._silent_update = False
                else:
                    self.update_queue.put((widget_info["var"], final_val, widget_id))
                    self._schedule_queue_processing()
                
                if widget_info["update_callback"]:
                    self.root.after(0, lambda: self._safe_execute_callback(
                        widget_info["update_callback"], data, widget_id))
                    
        except Exception as e:
            matrix_log("ui", "state_mirror", "sync_incoming_mqtt_to_gui", 
                       f"❌ [SYNC] Sync failure for {msg.topic}: {e}", "ERROR")

    def _safe_execute_callback(self, callback, data, widget_id):
        """Executes a widget-level callback while suppressing trace triggers."""
        self._silent_update = True
        try:
            callback(data)
        except Exception as e:
            matrix_log("ui", "state_mirror", "_safe_execute_callback", 
                       f"❌ [CALLBACK] Failure for {widget_id}: {e}", "ERROR")
        finally:
            self._silent_update = False

    def calculate_topic(self, widget_id: str, tab_name: str) -> str:
        """Utility for resolving FQ MQTT topics."""
        return self.topic_calculator.calculate(widget_id, tab_name)

    def publish_command(self, topic: str, payload: str):
        """Direct pass-through to the MQTT service for non-widget commands."""
        if not self.is_inert and not self._silent_update:
            mqtt_publisher_service.publish_payload(topic, payload)
