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
from workers.builder.builder_audio.dynamic_gui_create_dial import DialCreatorMixin


app_constants = Config.get_instance()

current_file = f"{os.path.basename(__file__)}"
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2


class HorizontalDialValueCreatorMixin(
    CustomHorizontalFaderCreatorMixin, DialCreatorMixin
):
    """
    A mixin class that provides the functionality for creating a
    fader-knob composite widget combined with a text entry box and a knob for fine-tuning.
    """

    def _get_format_string(self, step):
        if step == 0:
            return "{}"
        if step == int(step):
            return "{:.0f}"
        
        decimal_places = 0
        if step < 1:
            decimal_places = len(str(step).split('.')[-1])
        
        return f"{{:.{decimal_places}f}}"

    def _create_horizontal_dial_value(self, parent_widget, config_data, **kwargs):
        current_function_name = inspect.currentframe().f_code.co_name

        label = config_data.get("label_active", "")
        path = config_data.get("path", "")

        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to assemble a fader-dial combo for '{label}'.",
                **_get_log_args(),
            )

        try:
            sub_frame = ttk.Frame(parent_widget)

            label_widget = ttk.Label(sub_frame, text=f"{label}:")
            label_widget.pack(
                side=tk.TOP,
                fill=tk.X,
                padx=(DEFAULT_PAD_X, DEFAULT_PAD_Y),
                pady=(0, DEFAULT_PAD_Y),
            )

            min_val = float(config_data.get("min", "0"))
            max_val = float(config_data.get("max", "100"))
            numerical_step = float(config_data.get("step", "0.01"))

            format_string = self._get_format_string(numerical_step)
            resolution = numerical_step

            initial_value = float(
                config_data.get("default_value", config_data.get("value", "0"))
            )
            main_value_var = tk.DoubleVar(value=initial_value)
            entry_string_var = tk.StringVar(value=format_string.format(initial_value))

            fader_dial_frame = ttk.Frame(sub_frame)
            fader_dial_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
            fader_dial_frame.grid_columnconfigure(0, weight=9)
            fader_dial_frame.grid_columnconfigure(1, weight=1)

            fader_config = config_data.copy()
            fader_config["value_min"] = str(math.floor(min_val))
            fader_config["value_max"] = str(math.ceil(max_val))
            fader_config["value_default"] = str(math.floor(initial_value))
            fader_config["path"] = path + "/fader"
            
            fader_widget = self._create_custom_horizontal_fader(
                fader_dial_frame, fader_config
            )
            fader_widget.grid(row=0, column=0, sticky="nsew", padx=(DEFAULT_PAD_X, 0))

            dial_config = config_data.copy()
            dial_config["min"] = "0"
            dial_config["max"] = str(1 / resolution - 1)
            dial_config["value_default"] = str(round((initial_value % 1) / resolution))
            dial_config["path"] = path + "/dial"
            dial_config["base_mqtt_topic_from_path"] = base_mqtt_topic_from_path
            dial_config["state_mirror_engine"] = self.state_mirror_engine
            dial_config["subscriber_router"] = self.subscriber_router
            dial_config["label_active"] = label + " Dial"
            
            dial_widget = self._create_dial(fader_dial_frame, dial_config)
            dial_widget.grid(row=0, column=1, sticky="nsew", padx=(0, DEFAULT_PAD_X))

            value_unit_frame = ttk.Frame(sub_frame)
            value_unit_frame.pack(side=tk.TOP, fill=tk.X, expand=True)

            units_label = ttk.Label(value_unit_frame, text=config_data.get("units", ""))
            units_label.pack(side=tk.RIGHT, padx=(DEFAULT_PAD_X, DEFAULT_PAD_X))

            entry = ttk.Entry(
                value_unit_frame,
                width=10,
                style="Custom.TEntry",
                textvariable=entry_string_var,
                justify=tk.RIGHT,
            )
            entry.pack(side=tk.RIGHT, padx=(DEFAULT_PAD_X, 0))

            def update_widgets_from_main_var(*args):
                try:
                    current_val = main_value_var.get()
                    entry_string_var.set(format_string.format(current_val))
                    fader_widget.variable.set(math.floor(current_val))
                    decimal_part = current_val % 1
                    dial_widget.variable.set(round(decimal_part / resolution))
                except (ValueError, tk.TclError) as e:
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(message=f"Error updating widgets from main_value_var: {e}", **_get_log_args())

            def on_fader_change(*args):
                try:
                    fader_val = fader_widget.variable.get()
                    decimal_val = main_value_var.get() % 1
                    new_main_val = fader_val + decimal_val
                    new_main_val = round(new_main_val / numerical_step) * numerical_step
                    main_value_var.set(max(min_val, min(max_val, new_main_val)))
                except (ValueError, tk.TclError) as e:
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(message=f"Error on fader change: {e}", **_get_log_args())

            def on_dial_change(*args):
                try:
                    dial_val = dial_widget.variable.get()
                    integer_part = math.floor(main_value_var.get())
                    new_decimal_part = dial_val * resolution
                    new_main_val = integer_part + new_decimal_part
                    new_main_val = round(new_main_val / numerical_step) * numerical_step
                    main_value_var.set(max(min_val, min(max_val, new_main_val)))
                except (ValueError, tk.TclError) as e:
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(message=f"Error on dial change: {e}", **_get_log_args())

            def on_entry_manual_change(event):
                try:
                    new_val = float(entry_string_var.get())
                    new_val = round(new_val / numerical_step) * numerical_step
                    main_value_var.set(max(min_val, min(max_val, new_val)))
                except ValueError:
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(message="Invalid input in entry, please enter a number.", **_get_log_args())
                    entry_string_var.set(format_string.format(main_value_var.get()))

            fader_widget.variable.trace_add("write", on_fader_change)
            dial_widget.variable.trace_add("write", on_dial_change)
            main_value_var.trace_add("write", update_widgets_from_main_var)

            entry.bind("<FocusOut>", on_entry_manual_change)
            entry.bind("<Return>", on_entry_manual_change)

            update_widgets_from_main_var()

            if path:
                self.topic_widgets[path] = (main_value_var, fader_widget, dial_widget)
                widget_id = path
                state_mirror_engine.register_widget(widget_id, main_value_var, base_mqtt_topic_from_path, config_data)
                callback = lambda: state_mirror_engine.broadcast_gui_change_to_mqtt(widget_id)
                bind_variable_trace(main_value_var, callback)
                topic = state_mirror_engine.get_widget_topic(widget_id)
                if topic:
                    subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
                state_mirror_engine.initialize_widget_state(widget_id)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(message=f"✅ SUCCESS! The fader-dial combo '{label}' has materialized!", **_get_log_args())
            return sub_frame

        except Exception as e:
            debug_logger(message=f"❌ Error in {current_function_name} for '{label}': {e}", **_get_log_args())
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(message=f"💥 KABOOM! The fader-dial contraption for '{label}' has malfunctioned! Error: {e}", **_get_log_args())
            return None
