# workers/builder/builder_composite/_Horizontal_knob_Value.py
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
from workers.builder.builder_audio.dynamic_gui_create_custom_horizontal_fader import CustomHorizontalFaderCreatorMixin
from workers.builder.builder_audio.dynamic_gui_create_knob import KnobCreatorMixin

app_constants = Config.get_instance()

current_file = f"{os.path.basename(__file__)}"
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2

class HorizontalKnobValueCreatorMixin(CustomHorizontalFaderCreatorMixin, KnobCreatorMixin):
    """
    A mixin class that provides the functionality for creating a
    fader-knob composite widget combined with a text entry box and a knob for fine-tuning.
    """
    def _create_horizontal_knob_value(self, parent_frame, label, config, path, base_mqtt_topic_from_path, state_mirror_engine, subscriber_router):
        current_function_name = inspect.currentframe().f_code.co_name
        if app_constants.global_settings['debug_enabled']:
            debug_logger(message=f"🔬⚡️ Entering '{current_function_name}' to assemble a fader-knob combo for '{label}'.", **_get_log_args())

        try:
            sub_frame = ttk.Frame(parent_frame)

            label_widget = ttk.Label(sub_frame, text=f"{label}:")
            label_widget.pack(side=tk.TOP, fill=tk.X, padx=(DEFAULT_PAD_X, DEFAULT_PAD_Y), pady=(0, DEFAULT_PAD_Y))

            min_val = float(config.get('min', '0'))
            max_val = float(config.get('max', '100'))
            
            # Determine step_value dynamically or from config
            step_value = float(config.get('step', '0'))
            if step_value == 0: # If step not provided or is 0, calculate dynamically
                value_range = max_val - min_val
                if value_range <= 1: # New rule: 1 or under
                    step_value = 0.1
                elif value_range <= 10:
                    step_value = 2
                elif value_range <= 50:
                    step_value = 5
                elif value_range <= 100:
                    step_value = 10
                elif value_range <= 1000:
                    step_value = 50
                else: # value_range > 1000
                    step_value = 500
            
            # Use 'default_value' preference, fallback to 'value', then '0'
            main_value_var = tk.DoubleVar(value=float(config.get('default_value', config.get('value', '0'))))

            resolution = float(config.get('resolution', step_value)) # Use step_value as default resolution if not specified

            # Frame to hold fader and knob side-by-side
            fader_knob_frame = ttk.Frame(sub_frame)
            fader_knob_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
            fader_knob_frame.grid_columnconfigure(0, weight=9) # Fader 90%
            fader_knob_frame.grid_columnconfigure(1, weight=1) # Knob 10%

            # Create Fader (Coarse Adjustment)
            # Create a copy of config for the fader, potentially modifying its range to integer-like
            fader_config = config.copy()
            fader_config['value_min'] = str(math.floor(min_val))
            fader_config['value_max'] = str(math.ceil(max_val))
            fader_config['value_default'] = str(math.floor(main_value_var.get()))

            # The fader needs to update the main_value_var, but only its integer part
            fader_widget = self._create_custom_horizontal_fader(
                fader_knob_frame, None, fader_config, path, base_mqtt_topic_from_path, state_mirror_engine, subscriber_router
            )
            fader_widget.grid(row=0, column=0, sticky="nsew", padx=(DEFAULT_PAD_X, 0))

            # Create Knob (Fine Adjustment for Decimal Part)
            knob_config = config.copy()
            knob_config['min'] = '0'
            knob_config['max'] = str(1 / resolution - 1) # e.g., if res=0.01, max is 99
            knob_config['value_default'] = str(round((main_value_var.get() % 1) / resolution)) # Initial decimal value
            
            knob_widget = self._create_knob(
                fader_knob_frame, None, knob_config, path + "_knob", base_mqtt_topic_from_path, state_mirror_engine, subscriber_router
            )
            knob_widget.grid(row=0, column=1, sticky="nsew", padx=(0, DEFAULT_PAD_X))

            # Entry Box and Units (displaying combined value)
            value_unit_frame = ttk.Frame(sub_frame)
            value_unit_frame.pack(side=tk.TOP, fill=tk.X, expand=True)

            units_label = ttk.Label(value_unit_frame, text=config.get('units', ''))
            units_label.pack(side=tk.RIGHT, padx=(DEFAULT_PAD_X, DEFAULT_PAD_X))

            entry = ttk.Entry(value_unit_frame, width=10, style="Custom.TEntry", textvariable=main_value_var, justify=tk.RIGHT)
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
                    if app_constants.global_settings['debug_enabled']:
                        debug_logger(message=f"Error updating widgets from main_value_var: {e}", **_get_log_args())

            def on_fader_change(*args):
                try:
                    fader_val = fader_widget.variable.get()
                    decimal_val = (main_value_var.get() % 1)
                    new_main_val = fader_val + decimal_val
                    # Round to nearest step_value
                    new_main_val = round(new_main_val / step_value) * step_value
                    main_value_var.set(max(min_val, min(max_val, new_main_val)))
                except (ValueError, tk.TclError) as e:
                    if app_constants.global_settings['debug_enabled']:
                        debug_logger(message=f"Error on fader change: {e}", **_get_log_args())

            def on_knob_change(*args):
                try:
                    knob_val = knob_widget.variable.get()
                    integer_part = math.floor(main_value_var.get())
                    new_decimal_part = knob_val * resolution
                    new_main_val = integer_part + new_decimal_part
                    # Round to nearest step_value
                    new_main_val = round(new_main_val / step_value) * step_value
                    main_value_var.set(max(min_val, min(max_val, new_main_val)))
                except (ValueError, tk.TclError) as e:
                    if app_constants.global_settings['debug_enabled']:
                        debug_logger(message=f"Error on knob change: {e}", **_get_log_args())

            def on_entry_manual_change(event):
                try:
                    new_val = float(entry.get())
                    # Round to nearest step_value
                    new_val = round(new_val / step_value) * step_value
                    main_value_var.set(max(min_val, min(max_val, new_val)))
                except ValueError:
                    if app_constants.global_settings['debug_enabled']:
                        debug_logger(message="Invalid input in entry, please enter a number.", **_get_log_args())

            # Bindings
            fader_widget.variable.trace_add("write", on_fader_change)
            knob_widget.variable.trace_add("write", on_knob_change)
            main_value_var.trace_add("write", update_widgets_from_main_var) # Updates visual widgets

            entry.bind("<FocusOut>", on_entry_manual_change)
            entry.bind("<Return>", on_entry_manual_change)
            
            # Initial update to synchronize all widgets
            update_widgets_from_main_var()

            # MQTT Wiring for the combined main_value_var
            if path:
                self.topic_widgets[path] = (main_value_var, fader_widget, knob_widget)
                widget_id = path
                
                state_mirror_engine.register_widget(widget_id, main_value_var, base_mqtt_topic_from_path, config)
                callback = lambda: state_mirror_engine.broadcast_gui_change_to_mqtt(widget_id)
                bind_variable_trace(main_value_var, callback)
                topic = state_mirror_engine.get_widget_topic(widget_id)
                if topic:
                    subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
                state_mirror_engine.initialize_widget_state(widget_id)

            if app_constants.global_settings['debug_enabled']:
                debug_logger(message=f"✅ SUCCESS! The fader-knob combo '{label}' has materialized!", **_get_log_args())
            return sub_frame

        except Exception as e:
            debug_logger(message=f"❌ Error in {current_function_name} for '{label}': {e}", **_get_log_args())
            if app_constants.global_settings['debug_enabled']:
                debug_logger(message=f"💥 KABOOM! The fader-knob contraption for '{label}' has malfunctioned! Error: {e}", **_get_log_args())
            return None