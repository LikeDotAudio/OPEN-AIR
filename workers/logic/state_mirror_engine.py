# workers/logic/state_mirror_engine.py
#
# This file defines the StateMirrorEngine class, which synchronizes GUI state with the MQTT broker.
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
# Version 20260108.120700.1

import orjson
import inspect
import uuid
import time
import queue
import tkinter as tk
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config
from workers.mqtt import mqtt_publisher_service

app_constants = Config.get_instance()  # Get the singleton instance

import workers.mqtt.mqtt_topic_utils as mqtt_topic_utils

# Globals
current_version = "20251225.004500.1"
current_version_hash = 20251225 * 4500 * 1


class StateMirrorEngine:
    def __init__(self, base_topic, subscriber_router, root, state_cache_manager):
        """
        Initializes the StateMirrorEngine.

        Args:
            base_topic (str): The base MQTT topic for the application.
            subscriber_router (MqttSubscriberRouter): The MQTT subscriber router.
            root (tk.Tk): The root Tkinter window.
            state_cache_manager (StateCacheManager): The state cache manager.
            
        Returns:
            None
        """
        self.base_topic = base_topic
        self.subscriber_router = subscriber_router
        self.root = root
        self.state_cache_manager = state_cache_manager
        self.registered_widgets = {}
        self.topic_to_widget_id = {}
        self.GUID = str(uuid.uuid4())
        self._silent_update = False
        self._suppress_broadcast = False
        self.update_queue = queue.Queue()
        self.root.after(100, self._process_queue)

    def _process_queue(self):
        """
        Processes the GUI update queue from the main thread.
        
        Args:
            None
            
        Returns:
            None
        """
        try:
            while not self.update_queue.empty():
                tk_var, value, widget_id = self.update_queue.get_nowait()

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚡ De-queuing update for GUI Widget '{widget_id}' to {value}",
                        **_get_log_args(),
                    )

                self._silent_update = True
                try:
                    tk_var.set(value)
                finally:
                    self._silent_update = False
        finally:
            self.root.after(100, self._process_queue)

    def register_widget(
        self, widget_id, tk_variable, tab_name, config, update_callback=None
    ):
        """
        Registers a widget to be tracked by the engine.

        Args:
            widget_id (str): The unique ID of the widget.
            tk_variable (tk.Variable): The Tkinter variable associated with the widget.
            tab_name (str): The name of the tab the widget belongs to.
            config (dict): The configuration dictionary for the widget.
            update_callback (function, optional): A callback function to update the widget. Defaults to None.

        Returns:
            None
        """
        # 1. Sanitize the Tab Name (Remove redundant Root)
        clean_tab = tab_name
        if self.base_topic and clean_tab and clean_tab.startswith(self.base_topic):
            # If tab_name is just "OPEN-AIR", it becomes empty.
            # If it is "OPEN-AIR/oscilloscope", it becomes "oscilloscope"
            clean_tab = clean_tab[len(self.base_topic) :].strip("/")

        # 2. Sanitize the Widget ID (Remove leading slash)
        clean_id = widget_id.lstrip("/")

        # 3. Construct Clean Topic
        # Uses standard join, filtering out empty parts
        parts = [self.base_topic, clean_tab, clean_id]
        full_topic = "/".join([p for p in parts if p])

        self.registered_widgets[widget_id] = {
            "var": tk_variable,
            "tab": clean_tab,  # Store the clean version
            "id": widget_id,
            "config": config,
            "update_callback": update_callback,
            "topic": full_topic,
        }
        self.topic_to_widget_id[full_topic] = widget_id

    def initialize_widget_state(self, widget_id):
        """
        Initializes a widget's state from the cache or broadcasts its initial state.

        Args:
            widget_id (str): The unique ID of the widget.

        Returns:
            bool: True if the state was loaded from the cache, False otherwise.
        """
        if widget_id not in self.registered_widgets:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"⚠️ Attempted to initialize state for unregistered widget_id: {widget_id}",
                    **_get_log_args(),
                )
            return False

        widget_info = self.registered_widgets[widget_id]
        full_topic = widget_info["topic"]

        widget_config = widget_info.get("config", {})
        widget_type = widget_config.get("type")
        update_callback = widget_info.get("update_callback")

        if widget_type == "OcaTable" and update_callback:
            data_topic = full_topic

            cached_data = {}
            if self.state_cache_manager:
                # Look for the '/data/' sub-topic created by the new JSON structure
                prefix = data_topic + "/data/"
                for topic, payload in self.state_cache_manager.cache.items():
                    if topic.startswith(prefix):
                        item_key = topic[len(prefix) :]

                        # We only want direct children of /data/, e.g. .../Table/data/23
                        # not .../Table/data/23/some_other_field
                        if "/" in item_key:
                            continue

                        try:
                            # The cache stores the raw payload dict, not JSON string
                            cached_data[item_key] = payload
                        except (orjson.JSONDecodeError, TypeError):
                            pass

            if cached_data:
                debug_logger(
                    message=f"🧠 Found cached state for table '{widget_id}'. Applying from snapshot.",
                    **_get_log_args(),
                )
                update_callback(cached_data)
                return True
            else:
                debug_logger(
                    message=f"🧠 No cached state for table '{widget_id}'. Static data will be used if available.",
                    **_get_log_args(),
                )
                return False

        if self.state_cache_manager and full_topic in self.state_cache_manager.cache:
            # State exists in cache, so update the GUI widget
            cached_payload = self.state_cache_manager.cache[full_topic]
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🧠 Found cached state for {widget_id}. Applying from snapshot.",
                    **_get_log_args(),
                )

            # Re-using logic from sync_incoming_mqtt_to_gui
            try:
                data = cached_payload  # The cache stores a dict, not a JSON string
                tk_var = widget_info["var"]
                new_value = data.get("val", None)

                current_val = tk_var.get()

                if str(current_val) != str(new_value):
                    widget_config = widget_info["config"]
                    widget_type = widget_config.get("type")

                    final_value = None

                    if widget_type == "_GuiButtonToggle":
                        if isinstance(new_value, bool):
                            final_value = new_value
                        else:
                            if str(new_value).lower() in ("true", "1", "on"):
                                final_value = True
                            elif str(new_value).lower() in ("false", "0", "off"):
                                final_value = False

                    elif widget_type in [
                        "_CustomFader",
                        "_sliderValue",
                        "_Knob",
                        "_VUMeter",
                        "_NeedleVUMeter",
                        "_Panner",
                    ]:
                        try:
                            new_value_float = float(new_value)
                            min_val = float(widget_config.get("min", -1e9))
                            max_val = float(widget_config.get("max", 1e9))
                            final_value = max(min_val, min(max_val, new_value_float))
                        except (ValueError, TypeError):
                            return False
                    else:
                        final_value = new_value

                    if final_value is not None:
                        # Put the update task into the queue instead of calling .set() directly
                        self.update_queue.put((tk_var, final_value, widget_id))
                return True
            except Exception as e:
                debug_logger(
                    message=f"❌ Error applying cached state for {widget_id}: {e}",
                    **_get_log_args(),
                )
                return False

        else:
            # State does not exist in cache, so broadcast initial state
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🧠 No cached state for {widget_id}. Broadcasting initial state.",
                    **_get_log_args(),
                )
            self.broadcast_gui_change_to_mqtt(widget_id)
            return False

    def broadcast_gui_change_to_mqtt(self, widget_id):
        """
        Broadcasts a GUI change to the MQTT broker.

        Args:
            widget_id (str): The unique ID of the widget that changed.
            
        Returns:
            None
        """
        if self._suppress_broadcast:
            return

        if self._silent_update:
            return

        if widget_id in self.registered_widgets:
            widget_info = self.registered_widgets[widget_id]
            full_topic = widget_info["topic"]
            tk_var = widget_info["var"]
            current_tk_var_value = tk_var.get()
            widget_config = widget_info["config"]

            serializable_config = widget_config.copy()
            serializable_config.pop("state_mirror_engine", None)
            serializable_config.pop("subscriber_router", None)

            payload_data = {
                "val": current_tk_var_value,
                "ts": time.time(),
                "GUID": self.GUID,
            }

            for key, value in serializable_config.items():
                if key == "layout":
                    continue
                elif key == "value":
                    payload_data["static_config_value"] = value
                else:
                    payload_data[key] = value

            payload_json = orjson.dumps(payload_data)

            mqtt_publisher_service.publish_payload(full_topic, payload_json)
        else:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"⚠️ Attempted to broadcast change for unregistered widget_id: {widget_id}",
                    **_get_log_args(),
                )

    def is_widget_registered(self, widget_id: str) -> bool:
        """
        Checks if a widget is registered.

        Args:
            widget_id (str): The unique ID of the widget.

        Returns:
            bool: True if the widget is registered, False otherwise.
        """
        return widget_id in self.registered_widgets

    def get_widget_topic(self, widget_id):
        """
        Returns the full MQTT topic for a registered widget.

        Args:
            widget_id (str): The unique ID of the widget.

        Returns:
            str: The full MQTT topic for the widget, or None if the widget is not registered.
        """
        if widget_id in self.registered_widgets:
            return self.registered_widgets[widget_id]["topic"]
        return None

    def publish_command(self, topic: str, payload: str):
        """
        Publishes a command to the MQTT broker.

        Args:
            topic (str): The MQTT topic to publish to.
            payload (str): The payload to publish.
            
        Returns:
            None
        """
        if self._silent_update:
            return

        mqtt_publisher_service.publish_payload(topic, payload)
        debug_logger(
            message=f"📤 Published command to topic {topic}", **_get_log_args()
        )

    def sync_incoming_mqtt_to_gui(self, topic, payload):
        """
        Handles incoming MQTT messages and updates the GUI accordingly.

        Args:
            topic (str): The MQTT topic the message was received on.
            payload (str or dict): The payload of the message.
            
        Returns:
            None
        """
        try:
            data = None
            if isinstance(payload, dict):
                data = payload
            else:
                if isinstance(payload, bytes):
                    payload_str = payload.decode("utf-8")
                else:
                    payload_str = str(payload)

                stripped_payload = payload_str.strip()
                if not stripped_payload.startswith(("{", "[")):
                    return

                data = orjson.loads(stripped_payload)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"📥 MQTT Message Received: Topic='{topic}', Payload='{payload}'",
                    **_get_log_args(),
                )

            sender_GUID = data.get("GUID", None)
            if sender_GUID == self.GUID:
                return  # It's an echo of our own message, ignore.

            if topic in self.topic_to_widget_id:
                widget_id = self.topic_to_widget_id[topic]
                widget_info = self.registered_widgets[widget_id]
                tk_var = widget_info["var"]
                new_value = data.get("val", None)

                current_val = tk_var.get()

                if str(current_val) != str(new_value):
                    widget_config = widget_info["config"]
                    widget_type = widget_config.get("type")

                    final_value = None

                    if widget_type == "_GuiButtonToggle":
                        if isinstance(new_value, bool):
                            final_value = new_value
                        else:
                            if str(new_value).lower() in ("true", "1", "on"):
                                final_value = True
                            elif str(new_value).lower() in ("false", "0", "off"):
                                final_value = False

                    elif widget_type in [
                        "_CustomFader",
                        "_sliderValue",
                        "_Knob",
                        "_VUMeter",
                        "_NeedleVUMeter",
                        "_Panner",
                    ]:
                        try:
                            new_value_float = float(new_value)
                            min_val = float(widget_config.get("min", -1e9))
                            max_val = float(widget_config.get("max", 1e9))
                            final_value = max(min_val, min(max_val, new_value_float))
                        except (ValueError, TypeError):
                            return
                    else:
                        final_value = new_value

                    if final_value is not None:
                        try:
                            self._suppress_broadcast = True
                            # Put the update task into the queue instead of calling .set() directly
                            self.update_queue.put(
                                (tk_var, final_value, widget_info["id"])
                            )
                        finally:
                            self._suppress_broadcast = False
            else:
                pass

        except Exception as e:
            debug_logger(
                message=f"❌ The Flux Capacitor is cracking! Error in sync_incoming_mqtt_to_gui: {e}",
                **_get_log_args(),
            )