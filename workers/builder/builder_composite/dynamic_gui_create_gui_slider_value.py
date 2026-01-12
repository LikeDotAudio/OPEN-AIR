# builder_composite/dynamic_gui_create_gui_slider_value.py
#
# This file provides the SliderValueCreatorMixin class for creating slider widgets with text entry in the GUI.
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


class SliderValueCreatorMixin:
    """
    A mixin class that provides the functionality for creating a
    slider widget combined with a text entry box.
    """

    # Creates a composite widget consisting of a slider and a text entry box.
    # This method sets up a slider for adjusting a numerical value, along with a text entry
    # field for precise input. The two are synchronized and connected to the state management engine.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): The configuration for the slider widget.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     ttk.Frame: The created frame containing the composite widget, or None on failure.
    def _create_slider_value(self, parent_widget, config_data, **kwargs):
        # Creates a slider and an entry box for a numerical value.
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract only widget-specific config from config_data
        label = config_data.get(
            "label_active", ""
        )  # Assuming label comes from config_data
        path = config_data.get("path")  # Path needs to be passed in config_data

        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to assemble a slider for '{label}'.",
                **_get_log_args(),
            )

        try:
            sub_frame = ttk.Frame(parent_widget)  # Use parent_widget here

            layout_config = config_data.get("layout", {})
            font_size = layout_config.get("font", 12)
            custom_font = ("Helvetica", font_size)

            # --- Layout Refactor: Start ---
            # Line 1: Label
            label_widget = ttk.Label(sub_frame, text=f"{label}:", font=custom_font)
            label_widget.pack(
                side=tk.TOP,
                fill=tk.X,
                padx=(DEFAULT_PAD_X, DEFAULT_PAD_Y),
                pady=(0, DEFAULT_PAD_Y),
            )

            # Line 2: Slider
            min_val = float(config_data.get("min", "0"))
            max_val = float(config_data.get("max", "100"))

            # 🟢️️️ New fix: Create a custom style for a thicker slider
            style = ttk.Style(sub_frame)
            style_name = f"Thicker.{font_size}.Horizontal.TScale"
            
            slider_width = layout_config.get("width", 200)
            slider_height = layout_config.get("height", 40)

            style.configure(style_name, sliderlength=font_size * 2)
            slider = ttk.Scale(
                sub_frame,
                from_=min_val,
                to=max_val,
                orient=tk.HORIZONTAL,
                style=style_name,
            )

            slider.pack(
                side=tk.TOP,
                fill=tk.X,
                expand=True,
                padx=DEFAULT_PAD_X,
                pady=(0, DEFAULT_PAD_Y),
            )

            # Line 3: Textbox and Units
            value_unit_frame = ttk.Frame(sub_frame)
            value_unit_frame.pack(side=tk.TOP, fill=tk.X, expand=True)

            units_label = ttk.Label(value_unit_frame, text=config_data.get("units", ""), font=custom_font)
            units_label.pack(side=tk.RIGHT, padx=(DEFAULT_PAD_X, DEFAULT_PAD_X))

            entry_value = tk.StringVar(value=config_data.get("value", "0"))
            entry = ttk.Entry(
                value_unit_frame,
                width=7,
                style="Custom.TEntry",
                textvariable=entry_value,
                justify=tk.RIGHT,
                font=custom_font
            )
            entry.pack(side=tk.RIGHT, padx=(DEFAULT_PAD_X, 0))

            try:
                initial_val = float(entry_value.get())
                slider.set(initial_val)
            except (ValueError, tk.TclError):
                slider.set(min_val)
            # --- Layout Refactor: End ---

            def on_slider_move(val):
                entry_value.set(f"{float(val):.2f}")

            def on_entry_change(event):
                try:
                    new_val = float(entry.get())
                    if min_val <= new_val <= max_val:
                        slider.set(new_val)
                except ValueError:
                    debug_logger(message="Invalid input, please enter a number.")

            slider.config(command=on_slider_move)
            entry.bind("<FocusOut>", on_entry_change)
            entry.bind("<Return>", on_entry_change)

            # --- New Logic: Trace for external updates ---
            def _update_slider_from_entry_var(*args):
                if not entry_value.get():  # Check for empty string
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message="Empty string in entry_value for slider. Ignoring update.",
                            **_get_log_args(),
                        )
                    return  # Exit early if the string is empty

                try:
                    new_val = float(entry_value.get())
                    # Ensure the value is within the slider's range before setting
                    if min_val <= new_val <= max_val:
                        slider.set(new_val)
                    elif new_val < min_val:
                        slider.set(min_val)
                    elif new_val > max_val:
                        slider.set(max_val)
                except (ValueError, tk.TclError):
                    # Handle cases where entry_value might not be a valid float
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"Invalid value in entry_value for slider: {entry_value.get()}",
                            **_get_log_args(),
                        )

            # Bind the trace to the entry_value
            entry_value.trace_add("write", _update_slider_from_entry_var)

            if path:
                self.topic_widgets[path] = (entry_value, slider)

                # --- New MQTT Wiring ---
                widget_id = path

                # 1. Register widget
                state_mirror_engine.register_widget(
                    widget_id, entry_value, base_mqtt_topic_from_path, config_data
                )

                # 2. Bind variable trace for outgoing messages
                callback = lambda: state_mirror_engine.broadcast_gui_change_to_mqtt(
                    widget_id
                )
                bind_variable_trace(entry_value, callback)

                # 3. Subscribe to topic for incoming messages
                topic = state_mirror_engine.get_widget_topic(widget_id)
                if topic:
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                # 4. Initialize the widget state from cache or broadcast initial state
                state_mirror_engine.initialize_widget_state(widget_id)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ SUCCESS! The slider '{label}' has materialized!",
                    **_get_log_args(),
                )
            return sub_frame

        except Exception as e:
            debug_logger(
                message=f"❌ Error in {current_function_name} for '{label}': {e}"
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"💥 KABOOM! The slider contraption for '{label}' has malfunctioned! Error: {e}",
                    **_get_log_args(),
                )
            return None