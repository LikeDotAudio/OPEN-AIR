# workers/builder/dynamic_gui_create_needle_vu_meter.py
#
# A needle-style VU Meter that respects the global theme configuration.
# Version 20251223.220000.ThemeFix

import tkinter as tk
from tkinter import ttk
import math
from managers.configini.config_reader import Config                                                                          

app_constants = Config.get_instance() # Get the singleton instance      
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args 
from workers.styling.style import THEMES, DEFAULT_THEME
import os
from workers.mqtt.mqtt_topic_utils import get_topic # <--- ADD THIS LINE

class NeedleVUMeterCreatorMixin:
    def _create_needle_vu_meter(self, parent_widget, config_data): # Updated signature
        """Creates a needle-style VU meter widget."""
        current_function_name = "_create_needle_vu_meter"
        
        # Extract arguments from config_data
        label = config_data.get("label_active")
        config = config_data # config_data is the config
        path = config_data.get("path")
        base_mqtt_topic_from_path = config_data.get("base_mqtt_topic_from_path")
        state_mirror_engine = config_data.get("state_mirror_engine")
        subscriber_router = config_data.get("subscriber_router")

        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🔬⚡️ Entering '{current_function_name}' to calibrate a themed needle VU meter for '{label}'.",
                **_get_log_args()
            )

        # Theme Resolution
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg_color = colors.get("bg", "#2b2b2b")
        fg_color = colors.get("fg", "#dcdcdc")
        accent_color = colors.get("accent", "#33A1FD")
        secondary_color = colors.get("secondary", "#444444")
        danger_color = "#FF4500"  # Consistent Danger Red

        frame = ttk.Frame(parent_widget) # Use parent_widget here

        if label:
            ttk.Label(frame, text=label).pack(side=tk.TOP, pady=(0, 5))

        try:
            size = config.get("size", 150)
            min_val = float(config.get("min", -20.0))
            max_val = float(config.get("max", 3.0))
            red_zone_start = float(config.get("upper_range", 0.0))
            value_default = float(config.get("value_default", min_val))

            vu_value_var = tk.DoubleVar(value=value_default)

            canvas = tk.Canvas(frame, width=size, height=size/2 + 20, bg=bg_color, highlightthickness=0)
            canvas.pack()

            def update_visuals(*args):
                self._draw_needle_vu_meter(
                    canvas, size, vu_value_var.get(), min_val, max_val, red_zone_start,
                    accent_color, secondary_color, fg_color, danger_color
                )

            vu_value_var.trace_add("write", update_visuals)
            
            # Initial Draw
            update_visuals()

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
                    message=f"✅ SUCCESS! The themed needle VU meter for '{label}' is twitching with life!",
                    **_get_log_args()
                )
            
            return frame

        except Exception as e:
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"❌ The needle VU meter for '{label}' has flatlined! Error: {e}",
                    **_get_log_args()
                )
            return None

    def _draw_needle_vu_meter(self, canvas, size, value, min_val, max_val, red_zone_start, accent, secondary, fg, danger):
        canvas.delete("all")
        width = size
        height = size / 2 + 20

        center_x = width / 2
        center_y = height - 10 

        main_arc_radius = (width - 20) / 2
        arc_thickness = 4

        start_angle_deg = 135
        end_angle_deg = 45
        extent_deg = start_angle_deg - end_angle_deg

        # --- Draw Ticks and Labels ---
        tick_length = 8
        text_offset_from_arc = 15

        # Ticks should start from the inner edge of the arc
        tick_start_radius = main_arc_radius - (arc_thickness / 2)

        for i in range(6): 
            percentage = i / 5.0
            tick_val = min_val + (percentage * (max_val - min_val))
            
            current_angle_deg = start_angle_deg - (percentage * extent_deg)
            current_angle_rad = math.radians(current_angle_deg)

            # Tick line: starts on inner arc edge, goes inwards
            x_tick_start = center_x + tick_start_radius * math.cos(current_angle_rad)
            y_tick_start = center_y - tick_start_radius * math.sin(current_angle_rad)
            
            x_tick_end = center_x + (tick_start_radius - tick_length) * math.cos(current_angle_rad)
            y_tick_end = center_y - (tick_start_radius - tick_length) * math.sin(current_angle_rad)
            
            canvas.create_line(x_tick_start, y_tick_start, x_tick_end, y_tick_end, fill=fg, width=2)
            
            # Text label: position further OUT from the arc
            text_radius_pos = main_arc_radius + text_offset_from_arc
            tx = center_x + text_radius_pos * math.cos(current_angle_rad)
            ty = center_y - text_radius_pos * math.sin(current_angle_rad)
            canvas.create_text(tx, ty, text=f"{int(tick_val)}", fill=fg, font=("Helvetica", 8))

        # --- Draw Arcs ---
        green_start_norm = (red_zone_start - min_val) / (max_val - min_val) if max_val > min_val else 0
        green_start_angle_deg = start_angle_deg - (green_start_norm * extent_deg)
        
        canvas.create_arc(
            10, 10, width - 10, width - 10, 
            start=green_start_angle_deg, 
            extent=(start_angle_deg - green_start_angle_deg), 
            style=tk.ARC, outline="green", width=arc_thickness
        )

        canvas.create_arc(
            10, 10, width - 10, width - 10, 
            start=end_angle_deg, 
            extent=(green_start_angle_deg - end_angle_deg), 
            style=tk.ARC, outline=danger, width=arc_thickness
        )

        # --- Draw Needle ---
        if value < min_val: value = min_val
        if value > max_val: value = max_val
        
        norm_val = (value - min_val) / (max_val - min_val) if max_val > min_val else 0
        
        needle_angle_deg = start_angle_deg - (norm_val * extent_deg)
        needle_angle_rad = math.radians(needle_angle_deg)
        
        # Make needle extend into the numbers
        needle_total_len = main_arc_radius + text_offset_from_arc - 2

        x = center_x + needle_total_len * math.cos(needle_angle_rad)
        y = center_y - needle_total_len * math.sin(needle_angle_rad)
        
        canvas.create_line(center_x, center_y, x, y, width=3, fill=accent, capstyle=tk.ROUND)
        
        # --- Draw Pivot ---
        canvas.create_oval(center_x - 5, center_y - 5, center_x + 5, center_y + 5, fill=fg, outline=secondary)