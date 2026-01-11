# builder_input/dynamic_gui_create_gui_actuator.py
#
# This file provides the GuiActuatorCreatorMixin class for creating simple actuator buttons in the GUI.
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
# Version 20250821.200641.1

import os
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
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

    # Creates a button that acts as a simple actuator, triggering actions via MQTT.
    # This method sets up a button that, when pressed and released, publishes MQTT
    # commands to a specified topic. It also publishes the button's configuration
    # and subscribes to status updates.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the actuator button.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     ttk.Frame: The created frame containing the actuator button, or None on failure.
    def _create_gui_actuator(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        """Creates a button that acts as a simple actuator."""
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
            button_height_from_layout = layout.get("height")
            button_width_from_layout = layout.get("width")
            button_sticky = layout.get("sticky", "ew")

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"DEBUG: Layout height: {button_height_from_layout}, width: {button_width_from_layout}",
                    **_get_log_args(),
                )

            # Control sub_frame dimensions based on layout
            if button_width_from_layout is not None or button_height_from_layout is not None:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"DEBUG: Calling sub_frame.grid_propagate(False)",
                        **_get_log_args(),
                    )
                sub_frame.grid_propagate(False) # Stop sub_frame from resizing to content

                if button_height_from_layout is not None:
                    sub_frame.config(height=button_height_from_layout)
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"DEBUG: Configured sub_frame height: {button_height_from_layout}",
                            **_get_log_args(),
                        )

                if button_width_from_layout is not None:
                    sub_frame.config(width=button_width_from_layout)
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"DEBUG: Configured sub_frame width: {button_width_from_layout}",
                            **_get_log_args(),
                        )
                elif button_height_from_layout is not None: # Height is present, but width is not
                    # Calculate width based on text + 40px margin
                    button_text = config.get(
                        "label", config.get("label_active", config.get("label_inactive", label))
                    )
                    try:
                        # Get the default font for ttk.Button
                        style = ttk.Style()
                        font_name = style.lookup('TButton', 'font')
                        if font_name:
                            # Create a Font object to measure text
                            button_font = tkFont.Font(font=font_name)
                            text_pixel_width = button_font.measure(button_text)
                            desired_sub_frame_width = text_pixel_width + 40 # text width + 20px on each side
                            sub_frame.config(width=desired_sub_frame_width)
                            if app_constants.global_settings["debug_enabled"]:
                                debug_logger(
                                    message=f"DEBUG: Calculated desired width for text '{button_text}': {desired_sub_frame_width}",
                                    **_get_log_args(),
                                )
                        else:
                            # Fallback if font cannot be determined
                            sub_frame.config(width=100) # Arbitrary default width
                            if app_constants.global_settings["debug_enabled"]:
                                debug_logger(
                                    message=f"DEBUG: Fallback width 100 (font_name not found)",
                                    **_get_log_args(),
                                )
                    except Exception as e:
                        # Fallback for any error during font measurement
                        sub_frame.config(width=100) # Arbitrary default width
                        if app_constants.global_settings["debug_enabled"]:
                            debug_logger(
                                message=f"DEBUG: Fallback width 100 (exception during font measure: {e})",
                                **_get_log_args(),
                            )


            button_text = config.get(
                "label", config.get("label_active", config.get("label_inactive", label))
            )

            button = ttk.Button(sub_frame, text=button_text, style="Custom.TButton")

            # Place the button in the grid, letting sub_frame control pixel dimensions.
            # ipady and ipadx are no longer directly set here for overall sizing.
            button.grid(
                row=0,
                column=0,
                sticky=button_sticky,
                padx=DEFAULT_PAD_X,
                pady=DEFAULT_PAD_Y,
            )

            # Update the Tkinter event queue to ensure widgets are drawn and dimensions are available
            sub_frame.update_idletasks()
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"DEBUG: Actual sub_frame dimensions after configuration: width={sub_frame.winfo_width()}, height={sub_frame.winfo_height()}",
                    **_get_log_args(),
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

    # Callback function to update the visual state of the actuator button based on MQTT messages.
    # This method parses an incoming MQTT payload, extracts the active state (True/False),
    # and updates the button's style accordingly to indicate its active or inactive status.
    # Inputs:
    #     topic (str): The MQTT topic the message was received on.
    #     payload: The MQTT message payload containing the active state.
    # Outputs:
    #     None.
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