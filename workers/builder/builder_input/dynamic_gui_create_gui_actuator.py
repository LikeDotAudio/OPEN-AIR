# workers/builder/dynamic_gui_create_gui_actuator.py
#
# This file (dynamic_gui_create_gui_actuator.py) provides the GuiActuatorCreatorMixin class for creating simple actuator buttons in the GUI.
# A complete and comprehensive pre-amble that describes the file and the functions within.
# The purpose is to provide clear documentation and versioning.
#
# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# As the current hour is 20, no change is needed.

import os

Current_Date = 20251213  ##Update on the day the change was made
Current_Time = 120000  ## update at the time it was edited and compiled
Current_iteration = 44  ## a running version number - incriments by one each time

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = Current_Date * Current_Time * Current_iteration
current_file = os.path.basename(__file__)


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


import os
import tkinter as tk
from tkinter import ttk
import inspect
import orjson
import time

# --- Module Imports ---
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config
from workers.mqtt.mqtt_publisher_service import publish_payload

app_constants = Config.get_instance()  # Get the singleton instance
from workers.mqtt.mqtt_topic_utils import get_topic

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2
TOPIC_DELIMITER = "/"


class GuiActuatorCreatorMixin:
    """
    A mixin class that provides the functionality for creating a simple
    actuator button widget that triggers an action.
    """

    def _create_gui_actuator(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        # Creates a button that acts as a simple actuator.
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract only widget-specific config from config_data
        label = config_data.get("label_active")  # Use label_active from config_data
        config = config_data  # config_data is the config
        path = config_data.get("path")

        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to construct an actuator for '{label}'.",
                **_get_log_args(),
            )

        try:
            # Create a frame to hold the label and button
            sub_frame = ttk.Frame(parent_widget)  # Use parent_widget here
            sub_frame.grid_rowconfigure(0, weight=1)
            sub_frame.grid_columnconfigure(0, weight=1)

            layout = config.get("layout", {})
            button_height = layout.get("height", 30)
            button_sticky = layout.get("sticky", "ew")
            ipady = (button_height - 20) // 2 if button_height > 20 else 5

            button_text = config.get(
                "label", config.get("label_active", config.get("label_inactive", label))
            )

            button = ttk.Button(sub_frame, text=button_text, style="Custom.TButton")
            button.grid(
                row=0,
                column=0,
                sticky=button_sticky,
                padx=DEFAULT_PAD_X,
                pady=DEFAULT_PAD_Y,
                ipady=ipady,
            )

            # The sub_frame needs to be returned to be placed by the DynamicGuiBuilder's grid.
            # Its packing/gridding is handled by the caller.

            def on_press(event):
                action_path = f"{path}/trigger"
                topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, action_path)
                payload = orjson.dumps({"val": True, "ts": time.time()})

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"▶️ GUI ACTION: Activating actuator '{label}' to path '{action_path}'",
                        file=current_file,
                        version=current_version,
                        function=f"{self.__class__.__name__}.{current_function_name}",
                    )
                self.state_mirror_engine.publish_command(topic, payload)

            def on_release(event):
                action_path = f"{path}/trigger"
                topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, action_path)
                payload = orjson.dumps({"val": False, "ts": time.time()})

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⏹️ GUI ACTION: Deactivating actuator '{label}' to path '{action_path}'",
                        file=current_file,
                        version=current_version,
                        function=f"{self.__class__.__name__}.{current_function_name}",
                    )
                self.state_mirror_engine.publish_command(topic, payload)

            button.bind("<ButtonPress-1>", on_press)
            button.bind("<ButtonRelease-1>", on_release)

            if path:
                self.topic_widgets[path] = button

                # --- New MQTT Wiring ---
                widget_id = path

                # Publish the static configuration of the actuator
                config_topic = get_topic(
                    self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, widget_id, "config"
                )
                config_payload = orjson.dumps(config)
                publish_payload(config_topic, config_payload, retain=True)
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"📢 Published actuator config for '{label}' to '{config_topic}'",
                        **_get_log_args(),
                    )

                # 1. This widget is stateless and directly transmits commands,
                #    so no StringVar to register.

                # 2. No variable trace for outgoing messages, as it's a direct command.

                # 3. Subscribe to topic for incoming messages (to activate/deactivate button)
                #    The topic for status is usually 'path/active' or 'path/label_active'
                status_topic = f"{get_topic('OPEN-AIR', base_mqtt_topic_from_path, widget_id)}/active"
                self.subscriber_router.subscribe_to_topic(
                    status_topic, self._on_actuator_state_update
                )

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ SUCCESS! The actuator '{label}' is ready for action!",
                    **_get_log_args(),
                )
            return sub_frame

        except Exception as e:

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ The actuator '{label}' has short-circuited! Error: {e}",
                    file=current_file,
                    version=current_version,
                    function=current_function_name,
                )
            return None

    def _on_actuator_state_update(self, topic, payload):
        import orjson

        try:
            payload_data = orjson.loads(payload)
            is_active = payload_data.get("val")

            # Derive widget_id from topic
            # Example topic: "OPEN-AIR/Connection/YAK/Frequency/widget_id/active"
            # We need "Connection/YAK/Frequency/widget_id"

            topic_without_active = topic.rsplit(TOPIC_DELIMITER, 1)[0]

            # And remove the 'OPEN-AIR/BASE_MQTT_TOPIC_FROM_PATH/' prefix if it exists
            # We assume self.state_mirror_engine.base_topic is available from the builder instance
            expected_prefix = f"OPEN-AIR{TOPIC_DELIMITER}{self.state_mirror_engine.base_topic}{TOPIC_DELIMITER}"
            if topic_without_active.startswith(expected_prefix):
                key_in_topic_widgets = topic_without_active.replace(
                    expected_prefix, "", 1
                )
            else:
                # Fallback if the prefix doesn't match, or if base_mqtt_topic_from_path was empty
                key_in_topic_widgets = topic_without_active  # As a last resort

            button = self.topic_widgets.get(key_in_topic_widgets)
            if button:
                if is_active:
                    button.config(style="Custom.Selected.TButton")
                else:
                    button.config(style="Custom.TButton")

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"ℹ️ GUI ACTUATOR: Actuator '{key_in_topic_widgets}' state updated to {is_active}",
                        **_get_log_args(),
                    )
            else:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚠️ GUI ACTUATOR: Button widget not found in topic_widgets for key: {key_in_topic_widgets} (from topic: {topic})",
                        **_get_log_args(),
                    )

        except (orjson.JSONDecodeError, AttributeError) as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ Error processing actuator MQTT update for {topic}: {e}. Payload: {payload}"
                )
