# builder_audio/dynamic_gui_create_needle_vu_meter.py
#
# A needle-style VU Meter that respects the global theme configuration.
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
import math
import random
import time  # <--- ADD THIS LINE
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.styling.style import THEMES, DEFAULT_THEME
import os
from workers.mqtt.mqtt_topic_utils import get_topic  # <--- ADD THIS LINE


class NeedleVUMeterCreatorMixin:
    # Creates a needle-style VU meter widget.
    # This method sets up the VU meter, including its visual appearance and its connection
    # to the state management engine for real-time updates.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): The configuration for the VU meter.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     ttk.Frame: The created VU meter frame widget, or None on failure.
    def _create_needle_vu_meter(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        """Creates a needle-style VU meter widget."""
        current_function_name = "_create_needle_vu_meter"

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
                message=f"🔬⚡️ Entering '{current_function_name}' to calibrate a themed needle VU meter for '{label}'.",
                **_get_log_args(),
            )

        # Theme Resolution
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg_color = colors.get("bg", "#2b2b2b")
        fg_color = colors.get("fg", "#dcdcdc")
        accent_color = colors.get("accent", "#33A1FD")
        secondary_color = colors.get("secondary", "#444444")
        danger_color = "#FF4500"  # Consistent Danger Red

        frame = ttk.Frame(parent_widget)  # Use parent_widget here

        layout_config = config.get("layout", {})
        font_size = layout_config.get("font", 10)
        custom_font = ("Helvetica", font_size)
        custom_colour = layout_config.get("colour", None)

        show_label = config.get("show_label", True)
        if label and show_label:
            lbl = ttk.Label(frame, text=label, font=custom_font)
            if custom_colour:
                lbl.configure(foreground=custom_colour)
            lbl.pack(side=tk.TOP, pady=(0, 5))

        try:
            size = int(layout_config.get("width", config.get("size", 150)))
            min_val = float(config.get("min", -20.0))
            max_val = float(config.get("max", 3.0))
            red_zone_start = float(config.get("upper_range", 0.0))
            value_default = float(config.get("value_default", min_val))

            lower_colour = config.get("Lower_range_colour", "green")
            upper_colour = config.get("upper_range_Colour", danger_color)
            pointer_colour = config.get("Pointer_colour", accent_color)
            
            # Animation Parameters (Default: 100ms)
            # Glide: Time (ms) to traverse full scale upwards
            glide_time = float(config.get("glide_time", 100))
            # Dwell: Time (ms) to traverse full scale downwards (to a specific target)
            dwell_time = float(config.get("dwell_time", 100))
            # Hold: Time (ms) to hold value before auto-decaying
            hold_time = float(config.get("hold_time", 0))
            # Fall: Time (ms) to traverse full scale downwards (auto-decay to min)
            fall_time = float(config.get("fall_time", 100))

            vu_value_var = tk.DoubleVar(value=value_default)

            canvas = tk.Canvas(
                frame,
                width=size,
                height=size / 2 + 20,
                bg=bg_color,
                highlightthickness=0,
            )
            canvas.pack()

            # Animation State
            self.anim_current_value = value_default
            self.anim_target = value_default
            self.anim_mode = "idle" # idle, tracking, holding, decaying
            self.anim_hold_start = 0
            self.anim_running = False

            def draw_current_frame():
                self._draw_needle_vu_meter(
                    canvas,
                    size,
                    self.anim_current_value,
                    min_val,
                    max_val,
                    red_zone_start,
                    pointer_colour,
                    secondary_color,
                    fg_color,
                    upper_colour,
                    lower_colour
                )

            def animate():
                current = self.anim_current_value
                dt = 20.0 # milliseconds per frame (approx 50 FPS)
                full_range = max_val - min_val
                if full_range <= 0: full_range = 1.0

                # --- State Machine Logic ---
                if self.anim_mode == "holding":
                    # Check if hold time expired
                    if (time.time() * 1000) - self.anim_hold_start >= hold_time:
                        self.anim_mode = "decaying"
                    else:
                        # Still holding, just wait
                        canvas.after(int(dt), animate)
                        return

                # Determine target based on mode
                if self.anim_mode == "tracking":
                    target = self.anim_target
                elif self.anim_mode == "decaying":
                    target = min_val
                else: # idle
                    target = current # Don't move

                diff = target - current
                
                # Check for completion of current move
                if abs(diff) < 0.05: # Threshold
                    self.anim_current_value = target
                    draw_current_frame()
                    
                    if self.anim_mode == "tracking":
                        # Reached tracking target
                        if hold_time > 0:
                            self.anim_mode = "holding"
                            self.anim_hold_start = time.time() * 1000
                        else:
                            self.anim_mode = "decaying"
                        
                        # Continue animation next frame
                        canvas.after(int(dt), animate)
                        return
                    elif self.anim_mode == "decaying":
                        # Reached min_val (decay complete)
                        self.anim_mode = "idle"
                        self.anim_running = False
                        return
                    else:
                        # Should not happen often if logic is correct
                        self.anim_running = False
                        return

                # Calculate step size
                step = 0.0
                time_param = 0.0
                
                if diff > 0: # Rising
                    # Only rise if tracking. 
                    time_param = glide_time
                else: # Falling
                    if self.anim_mode == "tracking":
                        time_param = dwell_time
                    else:
                        time_param = fall_time
                
                if time_param <= 0:
                    step = diff # Instant
                else:
                    max_step = (full_range / time_param) * dt
                    # Clamp step to diff to avoid overshoot
                    if diff > 0:
                        step = min(diff, max_step)
                    else:
                        step = max(diff, -max_step)

                self.anim_current_value += step
                draw_current_frame()
                
                canvas.after(int(dt), animate)

            def on_value_change(*args):
                # New value received from logic/user
                new_target = vu_value_var.get()
                
                # Update target and switch to tracking mode immediately
                self.anim_target = new_target
                self.anim_mode = "tracking"
                
                if not self.anim_running:
                    self.anim_running = True
                    animate()

            vu_value_var.trace_add("write", on_value_change)

            # Initial Draw
            draw_current_frame()

            def on_middle_click(event):
                """Jump to a random allowed value."""
                random_val = random.uniform(min_val, max_val)
                vu_value_var.set(random_val)
                
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🖱️ Middle click on '{label}': jumped to {random_val:.2f}",
                        **_get_log_args(),
                    )

                if state_mirror_engine:
                    state_mirror_engine.broadcast_gui_change_to_mqtt(path)

            canvas.bind("<Button-2>", on_middle_click)

            if path:
                widget_id = path
                state_mirror_engine.register_widget(
                    widget_id, vu_value_var, base_mqtt_topic_from_path, config
                )

                # Subscribe to the topic for incoming messages
                topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, widget_id)
                self.subscriber_router.subscribe_to_topic(
                    topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui
                )

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine.",
                        **_get_log_args(),
                    )
                # Initialize state from cache or broadcast
                state_mirror_engine.initialize_widget_state(path)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ SUCCESS! The themed needle VU meter for '{label}' is twitching with life!",
                    **_get_log_args(),
                )

            return frame

        except Exception as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ The needle VU meter for '{label}' has flatlined! Error: {e}",
                    **_get_log_args(),
                )
            return None

    # Draws the needle-style VU meter on the canvas.
    # This method renders all the visual elements of the VU meter, including the background arc,
    # tick marks, labels, and the needle that indicates the current value.
    # Inputs:
    #     canvas: The tkinter canvas to draw on.
    #     size (int): The size of the meter.
    #     value (float): The current value to display.
    #     min_val, max_val (float): The min/max range of the meter.
    #     red_zone_start (float): The value at which the red zone begins.
    #     accent, secondary, fg, danger (str): Color values from the theme.
    #     lower_colour (str): The colour for the lower range.
    # Outputs:
    #     None.
    def _draw_needle_vu_meter(
        self,
        canvas,
        size,
        value,
        min_val,
        max_val,
        red_zone_start,
        pointer_colour,
        secondary,
        fg,
        upper_colour,
        lower_colour="green"
    ):
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

            x_tick_end = center_x + (tick_start_radius - tick_length) * math.cos(
                current_angle_rad
            )
            y_tick_end = center_y - (tick_start_radius - tick_length) * math.sin(
                current_angle_rad
            )

            canvas.create_line(
                x_tick_start, y_tick_start, x_tick_end, y_tick_end, fill=fg, width=2
            )

            # Text label: position further OUT from the arc
            text_radius_pos = main_arc_radius + text_offset_from_arc
            tx = center_x + text_radius_pos * math.cos(current_angle_rad)
            ty = center_y - text_radius_pos * math.sin(current_angle_rad)
            canvas.create_text(
                tx, ty, text=f"{int(tick_val)}", fill=fg, font=("Helvetica", 8)
            )

        # --- Draw Arcs ---
        green_start_norm = (
            (red_zone_start - min_val) / (max_val - min_val) if max_val > min_val else 0
        )
        green_start_angle_deg = start_angle_deg - (green_start_norm * extent_deg)

        canvas.create_arc(
            10,
            10,
            width - 10,
            width - 10,
            start=green_start_angle_deg,
            extent=(start_angle_deg - green_start_angle_deg),
            style=tk.ARC,
            outline=lower_colour,
            width=arc_thickness,
        )

        canvas.create_arc(
            10,
            10,
            width - 10,
            width - 10,
            start=end_angle_deg,
            extent=(green_start_angle_deg - end_angle_deg),
            style=tk.ARC,
            outline=upper_colour,
            width=arc_thickness,
        )

        # --- Draw Needle ---
        if value < min_val:
            value = min_val
        if value > max_val:
            value = max_val

        norm_val = (value - min_val) / (max_val - min_val) if max_val > min_val else 0

        needle_angle_deg = start_angle_deg - (norm_val * extent_deg)
        needle_angle_rad = math.radians(needle_angle_deg)

        # Make needle extend into the numbers
        needle_total_len = main_arc_radius + text_offset_from_arc - 2

        x = center_x + needle_total_len * math.cos(needle_angle_rad)
        y = center_y - needle_total_len * math.sin(needle_angle_rad)

        canvas.create_line(
            center_x, center_y, x, y, width=3, fill=pointer_colour, capstyle=tk.ROUND
        )

        # --- Draw Pivot ---
        canvas.create_oval(
            center_x - 5,
            center_y - 5,
            center_x + 5,
            center_y + 5,
            fill=fg,
            outline=secondary,
        )