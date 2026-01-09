# builder_input/dynamic_gui_create_gui_button_toggle.py
#
# This file provides the GuiButtonToggleCreatorMixin class for creating toggle button widgets in the GUI.
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
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
import inspect
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance
from workers.handlers.widget_event_binder import bind_variable_trace
from workers.mqtt.mqtt_topic_utils import get_topic


# --- Global Scope Variables ---
current_file = f"{os.path.basename(__file__)}"

TOPIC_DELIMITER = "/"


class GuiButtonToggleCreatorMixin:
    # Creates a single button that toggles between two states (e.g., ON/OFF).
    # This method sets up a button with dynamic text and styling based on its boolean state.
    # It supports both normal toggling behavior and a "latching" mode when the Shift key is pressed,
    # and integrates with the state management engine for MQTT synchronization.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the toggle button.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     ttk.Frame: The created frame containing the toggle button, or None on failure.
    def _create_gui_button_toggle(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        """Creates a single button that toggles between two states (e.g., ON/OFF)."""
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract only widget-specific config from config_data
        label = config_data.get("label_active")
        config = config_data  # config_data is the config
        path = config_data.get("path")  # Path for this widget

        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to engineer a toggle button for '{label}'.",
                **_get_log_args(),
            )

        try:
            sub_frame = ttk.Frame(parent_widget)  # Use parent_widget here

            options_map = config.get("options", {})
            on_config = options_map.get("ON", {})
            off_config = options_map.get("OFF", {})
            on_text = on_config.get("label_active", "ON")
            off_text = off_config.get("label_inactive", "OFF")

            is_on = options_map.get("ON", {}).get("selected", False)

            state_var = tk.BooleanVar(value=is_on)

            button = ttk.Button(sub_frame, text=on_text if is_on else off_text)
            button.pack(side=tk.LEFT, padx=5, pady=2)

            def update_button_state(*args):
                # Updates the button's appearance based on its current state.
                current_state = state_var.get()
                if (
                    current_state
                ):  # Correct logic: The button is ON, so use the 'Selected' style.
                    button.config(text=on_text, style="Custom.Selected.TButton")
                else:  # The button is OFF, so use the default 'TButton' style.
                    button.config(text=off_text, style="Custom.TButton")

            def on_button_click(event):
                # Shift key is bit 1 of the state mask
                is_shift_pressed = (event.state & 0x0001) != 0

                if is_shift_pressed:
                    # Latching behavior: if it's already on, do nothing. If it's off, turn it on and keep it on.
                    if not state_var.get():
                        state_var.set(True)
                else:
                    # Normal toggle behavior
                    state_var.set(not state_var.get())

            button.bind("<Button-1>", on_button_click)
            update_button_state()  # Set initial text and style

            if path:
                self.topic_widgets[path] = (state_var, update_button_state)

                # --- New MQTT Wiring ---
                widget_id = path

                # 1. Register widget
                state_mirror_engine.register_widget(
                    widget_id, state_var, base_mqtt_topic_from_path, config
                )

                # 2. Bind variable trace for outgoing messages
                callback = lambda: state_mirror_engine.broadcast_gui_change_to_mqtt(
                    widget_id
                )
                bind_variable_trace(state_var, callback)

                # 3. Also trace changes to update the button state
                state_var.trace_add("write", update_button_state)

                # 4. Subscribe to topic for incoming messages
                topic = state_mirror_engine.get_widget_topic(widget_id)
                if topic:
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                # 5. Initialize the widget's state from the cache or broadcast.
                state_mirror_engine.initialize_widget_state(widget_id)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ SUCCESS! The toggle button '{label}' is alive!",
                    **_get_log_args(),
                )
            return sub_frame

        except Exception as e:
            debug_logger(
                message=f"❌ Error in {current_function_name} for '{label}': {e}"
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"💥 KABOOM! The toggle button for '{label}' went into a paradoxical state! Error: {e}",
                    **_get_log_args(),
                )
            return None