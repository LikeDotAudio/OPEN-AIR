# workers/builder/dynamic_gui_create_vu_meter.py

import tkinter as tk
from tkinter import ttk
import math
from managers.configini.config_reader import Config                                                                          

app_constants = Config.get_instance() # Get the singleton instance      
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args 
import os
from workers.mqtt.mqtt_topic_utils import get_topic

class VUMeterCreatorMixin:
    def _create_vu_meter(self, parent_frame, label, config, path, base_mqtt_topic_from_path, state_mirror_engine, subscriber_router):
        """Creates a VU meter widget that is state-aware."""
        current_function_name = "_create_vu_meter"
        
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to calibrate a VU meter for '{label}'.",
                **_get_log_args()
            )

        frame = ttk.Frame(parent_frame)

        if label:
            ttk.Label(frame, text=label).pack(side=tk.TOP, pady=(0, 5))

        try:
            min_val = float(config.get("min", -20.0))
            max_val = float(config.get("max", 3.0))
            value_default = float(config.get("value_default", min_val))
            red_zone_start = float(config.get("upper_range", 0.0))
            width = int(config.get("width", 200))
            height = int(config.get("height", 20))

            vu_value_var = tk.DoubleVar(value=value_default)

            canvas = tk.Canvas(frame, width=width, height=height, bg='gray', highlightthickness=0)
            canvas.pack()

            # Draw the background
            red_zone_x = (red_zone_start - min_val) / (max_val - min_val) * width if max_val > min_val else 0
            canvas.create_rectangle(0, 0, red_zone_x, height, fill='green', outline='')
            canvas.create_rectangle(red_zone_x, 0, width, height, fill='red', outline='')
            
            # The indicator
            indicator = canvas.create_rectangle(0, 0, 5, height, fill='yellow', outline='')

            def update_visuals(*args):
                """Updates the indicator position based on the tk.DoubleVar."""
                current_value = vu_value_var.get()
                
                if current_value < min_val:
                    current_value = min_val
                if current_value > max_val:
                    current_value = max_val
                
                x_pos = (current_value - min_val) / (max_val - min_val) * width if max_val > min_val else 0
                canvas.coords(indicator, x_pos - 2.5, 0, x_pos + 2.5, height)

                if app_constants.global_settings['debug_enabled']:
                    debug_logger(message=f"🎶 VU meter '{label}' updated to {current_value}", **_get_log_args())

            vu_value_var.trace_add("write", update_visuals)
            update_visuals() # Initial draw

            if path:
                widget_id = path
                state_mirror_engine.register_widget(widget_id, vu_value_var, base_mqtt_topic_from_path, config)

                # Subscribe to the topic for incoming messages
                from workers.mqtt.mqtt_topic_utils import get_topic
                topic = get_topic("OPEN-AIR", base_mqtt_topic_from_path, widget_id)
                subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)

                if app_constants.global_settings['debug_enabled']:
                    debug_logger(
                        message=f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine.",
                        **_get_log_args()
                    )
                # Initialize state from cache or broadcast
                state_mirror_engine.initialize_widget_state(path)

            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"✅ SUCCESS! The VU meter '{label}' is now registering on the Richter scale!",
                    **_get_log_args()
                )
            
            return frame
        except Exception as e:
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"❌ The VU meter for '{label}' has overloaded! Error: {e}",
                    **_get_log_args()
                )
            return None