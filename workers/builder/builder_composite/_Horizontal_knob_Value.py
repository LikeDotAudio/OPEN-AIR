# builder_composite/_Horizontal_knob_Value.py
#
# A mixin class that provides the functionality for creating a fader-knob composite widget combined with a text entry box and a knob for fine-tuning.
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
import math
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config
from workers.handlers.widget_event_binder import bind_variable_trace
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.builder.builder_audio.dynamic_gui_create_custom_horizontal_fader import (
    CustomHorizontalFaderCreatorMixin,
)
from workers.builder.builder_audio.dynamic_gui_create_knob import KnobCreatorMixin

app_constants = Config.get_instance()

current_file = f"{os.path.basename(__file__)}"
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2


class HorizontalKnobValueCreatorMixin(
    CustomHorizontalFaderCreatorMixin, KnobCreatorMixin
):
    """
    A mixin class that provides the functionality for creating a
    fader-knob composite widget combined with a text entry box and a knob for fine-tuning.
    """

    # Creates a composite widget consisting of a horizontal fader for coarse adjustment,
    # a knob for fine-tuning, and a text entry box for precise value input.
    # This method orchestrates the creation and synchronization of these individual components
    # and connects the main value to the state management engine.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): The configuration for the composite widget.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     ttk.Frame: The created frame containing the composite widget, or None on failure.
    def _create_horizontal_knob_value(self, parent_widget, config_data, **kwargs):
        current_function_name = inspect.currentframe().f_code.co_name

        # Extract only widget-specific config from config_data
        label = config_data.get("label_active", "")  # Use label from config_data
        path = config_data.get("path", "")  # Path for this widget

        # Access global context directly from self
        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to assemble a fader-knob combo for '{label}'.",
                **_get_log_args(),
            )

        try:
            sub_frame = ttk.Frame(parent_widget)  # Use parent_widget here

            label_widget = ttk.Label(sub_frame, text=f"{label}:")
            label_widget.pack(
                side=tk.TOP,
                fill=tk.X,
                padx=(DEFAULT_PAD_X, DEFAULT_PAD_Y),
                pady=(0, DEFAULT_PAD_Y),
            )

            min_val = float(config_data.get("min", "0"))
            max_val = float(config_data.get("max", "100"))

            # Calculate value_range once, upfront
            value_range = max_val - min_val

            # Determine tick_mark_interval dynamically or from config_data
            tick_mark_interval = float(
                config_data.get("step", "0")
            )  # 'step' config_data now defines visual tick marks
            if (
                tick_mark_interval == 0
            ):  # If not provided or is 0, calculate dynamically for visual ticks
                if value_range <= 1:  # New rule: 1 or under
                    tick_mark_interval = 0.1
                elif value_range <= 10:
                    tick_mark_interval = 2
                elif value_range <= 50:
                    tick_mark_interval = 5
                elif value_range <= 100:
                    tick_mark_interval = 10
                elif value_range <= 1000:
                    tick_mark_interval = 50
                else:  # value_range > 1000
                    tick_mark_interval = 500

            # Define actual numerical step for value updates
            numerical_step = float(config_data.get("numerical_step", "0"))
            if (
                numerical_step == 0
            ):  # If numerical_step not provided or is 0, calculate dynamically
                # Use a sensible default based on the range or a fixed fine value
                if value_range <= 1:
                    numerical_step = 0.01  # For small ranges, allow very fine control
                elif value_range <= 100:
                    numerical_step = 0.1
                elif value_range <= 1000:
                    numerical_step = 1
                else:
                    numerical_step = 10

            # The 'resolution' for the knob itself might be different, typically finer
            # Use 'resolution' from config_data, fallback to numerical_step if not provided, then a very fine default
            resolution = float(config_data.get("resolution", numerical_step))
            if resolution == 0:  # Ensure resolution is never zero
                resolution = (
                    0.001  # A very fine default for the knob's smallest increment
                )

            # Use 'default_value' preference, fallback to 'value', then '0'
            main_value_var = tk.DoubleVar(
                value=float(
                    config_data.get("default_value", config_data.get("value", "0"))
                )
            )

            # Frame to hold fader and knob side-by-side
            fader_knob_frame = ttk.Frame(sub_frame)
            fader_knob_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
            fader_knob_frame.grid_columnconfigure(0, weight=9)  # Fader 90%
            fader_knob_frame.grid_columnconfigure(1, weight=1)  # Knob 10%

            # Create Fader (Coarse Adjustment)
            # Create a copy of config_data for the fader, potentially modifying its range to integer-like
            fader_config = config_data.copy()
            fader_config["value_min"] = str(math.floor(min_val))
            fader_config["value_max"] = str(math.ceil(max_val))
            fader_config["value_default"] = str(math.floor(main_value_var.get()))
            fader_config["path"] = path + "/fader"

            # The fader needs to update the main_value_var, but only its integer part
            fader_widget = self._create_custom_horizontal_fader(
                fader_knob_frame, fader_config
            )
            fader_widget.grid(row=0, column=0, sticky="nsew", padx=(DEFAULT_PAD_X, 0))

            # Create Knob (Fine Adjustment for Decimal Part)
            knob_config = config_data.copy()
            knob_config["min"] = "0"
            knob_config["max"] = str(1 / resolution - 1)  # e.g., if res=0.01, max is 99
            knob_config["value_default"] = str(
                round((main_value_var.get() % 1) / resolution)
            )  # Initial decimal value
            knob_config["path"] = path + "/knob"
            knob_config["base_mqtt_topic_from_path"] = base_mqtt_topic_from_path
            knob_config["state_mirror_engine"] = self.state_mirror_engine
            knob_config["subscriber_router"] = self.subscriber_router
            knob_config["label_active"] = label + " Knob"  # Label for knob

            knob_widget = self._create_knob(fader_knob_frame, knob_config)
            knob_widget.grid(row=0, column=1, sticky="nsew", padx=(0, DEFAULT_PAD_X))

            # Entry Box and Units (displaying combined value)
            value_unit_frame = ttk.Frame(sub_frame)
            value_unit_frame.pack(side=tk.TOP, fill=tk.X, expand=True)

            units_label = ttk.Label(value_unit_frame, text=config_data.get("units", ""))
            units_label.pack(side=tk.RIGHT, padx=(DEFAULT_PAD_X, DEFAULT_PAD_X))

            entry = ttk.Entry(
                value_unit_frame,
                width=10,
                style="Custom.TEntry",
                textvariable=main_value_var,
                justify=tk.RIGHT,
            )
            entry.pack(side=tk.RIGHT, padx=(DEFAULT_PAD_X, 0))

            # --- Synchronization Logic ---
            def update_widgets_from_main_var(*args):
                try:
                    current_val = main_value_var.get()
                    # Update Fader (integer part)
                    fader_widget.variable.set(math.floor(current_val))
                    # Update Knob (decimal part)
                    decimal_part = current_val % 1
                    knob_widget.variable.set(round(decimal_part / resolution))
                except (ValueError, tk.TclError) as e:
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"Error updating widgets from main_value_var: {e}",
                            **_get_log_args(),
                        )

            def on_fader_change(*args):
                try:
                    fader_val = fader_widget.variable.get()
                    decimal_val = main_value_var.get() % 1
                    new_main_val = fader_val + decimal_val
                    # Round to nearest numerical_step
                    new_main_val = round(new_main_val / numerical_step) * numerical_step
                    main_value_var.set(max(min_val, min(max_val, new_main_val)))
                except (ValueError, tk.TclError) as e:
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"Error on fader change: {e}", **_get_log_args()
                        )

            def on_knob_change(*args):
                try:
                    knob_val = knob_widget.variable.get()
                    integer_part = math.floor(main_value_var.get())
                    new_decimal_part = knob_val * resolution
                    new_main_val = integer_part + new_decimal_part
                    # Round to nearest numerical_step
                    new_main_val = round(new_main_val / numerical_step) * numerical_step
                    main_value_var.set(max(min_val, min(max_val, new_main_val)))
                except (ValueError, tk.TclError) as e:
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"Error on knob change: {e}", **_get_log_args()
                        )

            def on_entry_manual_change(event):
                try:
                    new_val = float(entry.get())
                    # Round to nearest numerical_step
                    new_val = round(new_val / numerical_step) * numerical_step
                    main_value_var.set(max(min_val, min(max_val, new_val)))
                except ValueError:
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message="Invalid input in entry, please enter a number.",
                            **_get_log_args(),
                        )

            # Bindings
            fader_widget.variable.trace_add("write", on_fader_change)
            knob_widget.variable.trace_add("write", on_knob_change)
            main_value_var.trace_add(
                "write", update_widgets_from_main_var
            )  # Updates visual widgets

            entry.bind("<FocusOut>", on_entry_manual_change)
            entry.bind("<Return>", on_entry_manual_change)

            # Initial update to synchronize all widgets
            update_widgets_from_main_var()

            # MQTT Wiring for the combined main_value_var
            if path:
                self.topic_widgets[path] = (main_value_var, fader_widget, knob_widget)
                widget_id = path

                state_mirror_engine.register_widget(
                    widget_id, main_value_var, base_mqtt_topic_from_path, config_data
                )
                callback = lambda: state_mirror_engine.broadcast_gui_change_to_mqtt(
                    widget_id
                )
                bind_variable_trace(main_value_var, callback)
                topic = state_mirror_engine.get_widget_topic(widget_id)
                if topic:
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )
                state_mirror_engine.initialize_widget_state(widget_id)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ SUCCESS! The fader-knob combo '{label}' has materialized!",
                    **_get_log_args(),
                )
            return sub_frame

        except Exception as e:
            debug_logger(
                message=f"❌ Error in {current_function_name} for '{label}': {e}",
                **_get_log_args(),
            )
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"💥 KABOOM! The fader-knob contraption for '{label}' has malfunctioned! Error: {e}",
                    **_get_log_args(),
                )
            return None