# builder_text/dynamic_gui_create_value_box.py
#
# This file provides the ValueBoxCreatorMixin class for creating editable text box widgets in the GUI.
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
import inspect

# --- Module Imports ---
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance
from workers.handlers.widget_event_binder import bind_variable_trace
from workers.mqtt.mqtt_topic_utils import get_topic

# --- Global Scope Variables ---
current_file = f"{os.path.basename(__file__)}"

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2


class ValueBoxCreatorMixin:
    """
    A mixin class that provides the functionality for creating an
    editable text box widget.
    """

    # Creates an editable text box widget for displaying and modifying a single value.
    # This method sets up a Tkinter Entry widget with an associated label and optional units.
    # Its value is bound to a StringVar and integrated with the state management engine,
    # allowing for bidirectional synchronization via MQTT.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the value box widget.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     ttk.Frame: The created frame containing the value box widget, or None on failure.
    def _create_value_box(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        """Creates an editable text box (_Value)."""
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract only widget-specific config from config_data
        label = config_data.get("label_active")
        config = config_data  # config_data is the config
        path = config_data.get("path")

        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to brew a value box for '{label}'.",
                **_get_log_args(),
            )

        try:
            sub_frame = ttk.Frame(parent_widget)  # Use parent_widget here

            label_widget = ttk.Label(sub_frame, text=f"{label}:")
            label_widget.pack(side=tk.LEFT, padx=(DEFAULT_PAD_X, DEFAULT_PAD_X))

            entry_value = tk.StringVar(value=config.get("value", ""))
            entry = ttk.Entry(
                sub_frame, textvariable=entry_value, style="Custom.TEntry"
            )
            entry.pack(side=tk.LEFT, padx=DEFAULT_PAD_X)

            if config.get("units"):
                units_label = ttk.Label(sub_frame, text=config["units"])
                units_label.pack(side=tk.LEFT, padx=(0, DEFAULT_PAD_X))

            if path:
                self.topic_widgets[path] = entry

                # --- New MQTT Wiring ---
                if state_mirror_engine and subscriber_router:  # Now explicitly passed
                    widget_id = path

                    # 1. Register widget
                    state_mirror_engine.register_widget(
                        widget_id, entry_value, base_mqtt_topic_from_path, config
                    )

                    # 2. Bind variable trace for outgoing messages
                    callback = (
                        lambda *args: state_mirror_engine.broadcast_gui_change_to_mqtt(
                            widget_id
                        )
                    )  # Added *args
                    bind_variable_trace(entry_value, callback)

                    # 3. Subscribe to topic for incoming messages
                    topic = get_topic(
                        self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, widget_id
                    )
                    self.subscriber_router.subscribe_to_topic(
                        topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                    # 4. Initialize state from cache or broadcast
                    self.state_mirror_engine.initialize_widget_state(widget_id)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ SUCCESS! The value box '{label}' has been perfectly crafted!",
                    **_get_log_args(),
                )
            return sub_frame

        except Exception as e:
            debug_logger(
                message=f"❌ Error in {current_function_name} for '{label}': {e}"
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"💥 KABOOM! The value box for '{label}' has spectacularly failed! Error: {e}",
                    **_get_log_args(),
                )
            return None