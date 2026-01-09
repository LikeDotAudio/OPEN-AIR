# builder_input/dynamic_gui_create_inc_dec_buttons.py
#
# A mixin for creating increment and decrement buttons with a value display, synchronized via MQTT.
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

import tkinter as tk
from tkinter import ttk
from managers.configini.config_reader import Config
from workers.mqtt.mqtt_topic_utils import get_topic

app_constants = Config.get_instance()  # Get the singleton instance
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
import os


class IncDecButtonsCreatorMixin:
    # Creates a set of increment and decrement buttons along with a display for their current value.
    # This method sets up two buttons (up/down arrows) that, when pressed, modify a numerical
    # value. The current value is displayed, and the entire widget is synchronized via MQTT.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the increment/decrement buttons.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     ttk.Frame: The created frame containing the increment/decrement buttons and value display.
    def _create_inc_dec_buttons(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        """Creates increment/decrement buttons."""
        current_function_name = "_create_inc_dec_buttons"

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
                message=f"🔬⚡️ Entering '{current_function_name}' to forge increment/decrement buttons for '{label}'.",
                **_get_log_args(),
            )

        frame = ttk.Frame(parent_widget)  # Use parent_widget here

        if label:
            ttk.Label(frame, text=label).pack(side=tk.LEFT, padx=(0, 10))

        # Initial value and range (optional, can be used for boundary checks)
        value_default = config.get("value_default", 0)
        increment_amount = config.get("increment", 1)

        current_value = tk.IntVar(value=value_default)

        value_display = ttk.Label(frame, textvariable=current_value)
        value_display.pack(side=tk.RIGHT, padx=(10, 0))

        def _increment():
            new_value = current_value.get() + increment_amount
            current_value.set(new_value)
            # MQTT publish will now be handled by the trace bound to current_value

        def _decrement():
            new_value = current_value.get() - increment_amount
            current_value.set(new_value)
            # MQTT publish will now be handled by the trace bound to current_value

        dec_button = ttk.Button(frame, text="⬇", command=_decrement)
        dec_button.pack(side=tk.RIGHT)

        inc_button = ttk.Button(frame, text="⬆", command=_increment)
        inc_button.pack(side=tk.RIGHT, padx=(5, 0))

        # --- New MQTT Wiring for Inc/Dec Buttons ---
        if path:  # state_mirror_engine and subscriber_router are now explicitly passed
            widget_id = path

            # 1. Register widget
            state_mirror_engine.register_widget(
                widget_id, current_value, base_mqtt_topic_from_path, config
            )

            # 2. Subscribe to this widget's topic to receive updates
            topic = self.state_mirror_engine.get_widget_topic(widget_id)
            if topic:
                self.subscriber_router.subscribe_to_topic(
                    topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui
                )

            # 3. Bind variable trace for outgoing messages
            # Use a lambda that calls broadcast_gui_change_to_mqtt
            callback = (
                lambda *args: self.state_mirror_engine.broadcast_gui_change_to_mqtt(
                    widget_id
                )
            )
            current_value.trace_add("write", callback)

            # 4. Initialize state from cache or broadcast
            self.state_mirror_engine.initialize_widget_state(widget_id)

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"✅ SUCCESS! The increment/decrement buttons for '{label}' are operational and MQTT-synced!",
                **_get_log_args(),
            )
        return frame