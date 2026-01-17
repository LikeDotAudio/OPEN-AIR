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
            # Resting point for correlation meters is usually 0, for VU meters it's min_val
            resting_point = float(config.get("resting_point", min_val))

            lower_colour = config.get("Lower_range_colour", "green")
            upper_colour = config.get("upper_range_Colour", danger_color)
            pointer_colour = config.get("Pointer_colour", accent_color)
            
            needle_thickness = int(config.get("Needle_thickness", 3))
            scale_numbers = config.get("Scale_numbers", True)
            ticks_visible = config.get("Ticks_visible", True)
            curve_thickness = int(config.get("curve_thickness", 4))
            meter_viewable_angle = float(config.get("Meter_viewable_angle", 90.0))
            meter_center_angle = float(config.get("Meter_center_angle", 90.0))
            counter_clockwise = config.get("Counter_Clockwise", False)
            custom_ticks = config.get("custom_ticks", None)
            sub_ticks = int(config.get("sub_ticks", 0))
            
            pointer_style = config.get("Pointer_Style", "line").lower()
            pivot_size = int(config.get("Pivot_size", 10))
            
            # Determine mask default
            # Masking hides the bottom half (below pivot). Useful for standard 90-degree meters.
            default_mask = (meter_viewable_angle <= 100) and (abs(meter_center_angle - 90) < 1)
            mask = config.get("mask", default_mask)
            
            meter_mode = config.get("meter_mode", "mono").lower()
            pointer_colour_2 = config.get("Pointer_colour_2", "#FF0000") # Default Red for 2nd needle

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
            vu_value_var_2 = tk.DoubleVar(value=value_default) if meter_mode == "stereo" else None

            # Calculate required height based on viewable angle
            half_angle = meter_viewable_angle / 2.0
            main_arc_radius = (size - 20) / 2
            center_y = size / 2 + 10
            
            # Default to square aspect ratio (width=height) unless masked
            required_height = size
            
            if mask:
                # Crop to pivot + padding
                required_height = int(center_y + (pivot_size / 2) + 5)

            canvas = tk.Canvas(
                frame,
                width=size,
                height=required_height,
                bg=bg_color,
                highlightthickness=0,
            )
            canvas.pack()

            # Animation State
            frame.anim_current_value = value_default
            frame.anim_target = value_default
            frame.anim_current_value_2 = value_default
            frame.anim_target_2 = value_default
            
            frame.anim_mode = "idle" # idle, tracking, holding, decaying
            frame.anim_hold_start = 0
            frame.anim_running = False

            def draw_current_frame():
                val2 = frame.anim_current_value_2 if meter_mode == "stereo" else None
                self._draw_needle_vu_meter(
                    canvas,
                    size,
                    frame.anim_current_value,
                    min_val,
                    max_val,
                    red_zone_start,
                    pointer_colour,
                    secondary_color,
                    fg_color,
                    upper_colour,
                    lower_colour,
                    needle_thickness,
                    scale_numbers,
                    curve_thickness,
                    ticks_visible,
                    meter_viewable_angle,
                    custom_ticks,
                    value2=val2,
                    pointer_colour2=pointer_colour_2,
                    meter_center_angle=meter_center_angle,
                    counter_clockwise=counter_clockwise,
                    pointer_style=pointer_style,
                    pivot_size=pivot_size,
                    mask=mask,
                    sub_ticks=sub_ticks
                )

            def animate():
                dt = 20.0 # milliseconds per frame (approx 50 FPS)
                full_range = max_val - min_val
                if full_range <= 0: full_range = 1.0

                # --- State Machine Logic ---
                if frame.anim_mode == "holding":
                    # Check if hold time expired
                    if (time.time() * 1000) - frame.anim_hold_start >= hold_time:
                        frame.anim_mode = "decaying"
                    else:
                        # Still holding, just wait
                        canvas.after(int(dt), animate)
                        return

                targets = [frame.anim_target]
                currents = [frame.anim_current_value]
                
                if meter_mode == "stereo":
                    targets.append(frame.anim_target_2)
                    currents.append(frame.anim_current_value_2)

                new_currents = []
                all_done = True

                for i, current in enumerate(currents):
                    # Determine target based on mode
                    if frame.anim_mode == "tracking":
                        target = targets[i]
                    elif frame.anim_mode == "decaying":
                        target = resting_point
                    else: # idle
                        target = current # Don't move

                    diff = target - current
                    
                    # Check for completion of current move
                    if abs(diff) < 0.05: # Threshold
                        new_currents.append(target)
                    else:
                        all_done = False
                        # Calculate step size
                        step = 0.0
                        time_param = 0.0
                        
                        if diff > 0: # Rising
                            # Only rise if tracking. 
                            time_param = glide_time
                        else: # Falling
                            if frame.anim_mode == "tracking":
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
                        new_currents.append(current + step)

                frame.anim_current_value = new_currents[0]
                if meter_mode == "stereo":
                    frame.anim_current_value_2 = new_currents[1]

                draw_current_frame()
                
                if all_done:
                    if frame.anim_mode == "tracking":
                        # Reached tracking target
                        if hold_time > 0:
                            frame.anim_mode = "holding"
                            frame.anim_hold_start = time.time() * 1000
                        else:
                            frame.anim_mode = "decaying"
                        canvas.after(int(dt), animate)
                    elif frame.anim_mode == "decaying":
                        # Reached resting_point (decay complete)
                        frame.anim_mode = "idle"
                        frame.anim_running = False
                else:
                    canvas.after(int(dt), animate)

            def on_value_change(*args):
                # New value received from logic/user
                new_target = vu_value_var.get()
                frame.anim_target = new_target
                frame.anim_mode = "tracking"
                if not frame.anim_running:
                    frame.anim_running = True
                    animate()

            vu_value_var.trace_add("write", on_value_change)
            
            if meter_mode == "stereo":
                def on_value_change_2(*args):
                    new_target = vu_value_var_2.get()
                    frame.anim_target_2 = new_target
                    frame.anim_mode = "tracking"
                    if not frame.anim_running:
                        frame.anim_running = True
                        animate()
                vu_value_var_2.trace_add("write", on_value_change_2)

            # Initial Draw
            draw_current_frame()

            def on_middle_click(event):
                """Jump to a random allowed value."""
                random_val = random.uniform(min_val, max_val)
                vu_value_var.set(random_val)
                if meter_mode == "stereo":
                    random_val_2 = random.uniform(min_val, max_val)
                    vu_value_var_2.set(random_val_2)
                
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🖱️ Middle click on '{label}': jumped to {random_val:.2f}",
                        **_get_log_args(),
                    )

                if state_mirror_engine:
                    state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                    if meter_mode == "stereo":
                         state_mirror_engine.broadcast_gui_change_to_mqtt(path + "_2") # Implicit path for 2nd channel?

            canvas.bind("<Button-2>", on_middle_click)

            if path:
                widget_id = path
                state_mirror_engine.register_widget(
                    widget_id, vu_value_var, base_mqtt_topic_from_path, config
                )
                topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, widget_id)
                self.subscriber_router.subscribe_to_topic(
                    topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui
                )
                
                if meter_mode == "stereo":
                    # Register second variable with suffix
                    widget_id_2 = path + "_2" # Convention for stereo pair?
                    # Or maybe the config should specify paths?
                    # For now, let's append _R or _2
                    state_mirror_engine.register_widget(
                        widget_id_2, vu_value_var_2, base_mqtt_topic_from_path, config
                    )
                    topic_2 = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, widget_id_2)
                    self.subscriber_router.subscribe_to_topic(
                        topic_2, self.state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine.",
                        **_get_log_args(),
                    )
                # Initialize state from cache or broadcast
                state_mirror_engine.initialize_widget_state(path)
                if meter_mode == "stereo":
                     state_mirror_engine.initialize_widget_state(path + "_2")

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
        lower_colour="green",
        needle_thickness=3,
        scale_numbers=True,
        curve_thickness=4,
        ticks_visible=True,
        meter_viewable_angle=90.0,
        custom_ticks=None,
        value2=None,
        pointer_colour2=None,
        meter_center_angle=90.0,
        counter_clockwise=False,
        pointer_style="line",
        pivot_size=10,
        mask=False,
        sub_ticks=0
    ):
        canvas.delete("vu_element")
        # Ensure coordinates are aligned with the pivot center used in creation
        width = size
        center_x = width / 2
        center_y = size / 2 + 10

        main_arc_radius = (width - 20) / 2
        arc_thickness = curve_thickness

        # Calculate start and end angles centered around meter_center_angle
        half_angle = meter_viewable_angle / 2.0
        start_angle_deg = meter_center_angle + half_angle
        end_angle_deg = meter_center_angle - half_angle
        
        extent_deg = start_angle_deg - end_angle_deg

        # --- Draw Ticks and Labels ---
        tick_length = 8
        sub_tick_length = 4
        text_offset_from_arc = 15

        # Ticks should start from the inner edge of the arc
        tick_start_radius = main_arc_radius - (arc_thickness / 2)

        if custom_ticks:
            tick_values = custom_ticks
        else:
            tick_values = [min_val + (i / 5.0 * (max_val - min_val)) for i in range(6)]

        for i, tick_val in enumerate(tick_values):
            # Calculate normalized position (0.0 to 1.0)
            range_val = max_val - min_val
            percentage = (tick_val - min_val) / range_val if range_val != 0 else 0
            
            # Map to angle
            if counter_clockwise:
                current_angle_deg = end_angle_deg + (percentage * extent_deg)
            else:
                current_angle_deg = start_angle_deg - (percentage * extent_deg)
                
            current_angle_rad = math.radians(current_angle_deg)

            # Draw Main Tick
            if ticks_visible:
                x_tick_start = center_x + tick_start_radius * math.cos(current_angle_rad)
                y_tick_start = center_y - tick_start_radius * math.sin(current_angle_rad)
                x_tick_end = center_x + (tick_start_radius - tick_length) * math.cos(current_angle_rad)
                y_tick_end = center_y - (tick_start_radius - tick_length) * math.sin(current_angle_rad)
                canvas.create_line(x_tick_start, y_tick_start, x_tick_end, y_tick_end, fill=fg, width=2, tags="vu_element")

            # Draw Sub-Ticks (between this tick and next)
            if sub_ticks > 0 and i < len(tick_values) - 1:
                next_val = tick_values[i+1]
                for j in range(1, sub_ticks + 1):
                    sub_val = tick_val + (j * (next_val - tick_val) / (sub_ticks + 1))
                    sub_perc = (sub_val - min_val) / range_val if range_val != 0 else 0
                    
                    if counter_clockwise:
                        sub_angle_deg = end_angle_deg + (sub_perc * extent_deg)
                    else:
                        sub_angle_deg = start_angle_deg - (sub_perc * extent_deg)
                    
                    sub_angle_rad = math.radians(sub_angle_deg)
                    
                    sx_tick_start = center_x + tick_start_radius * math.cos(sub_angle_rad)
                    sy_tick_start = center_y - tick_start_radius * math.sin(sub_angle_rad)
                    sx_tick_end = center_x + (tick_start_radius - sub_tick_length) * math.cos(sub_angle_rad)
                    sy_tick_end = center_y - (tick_start_radius - sub_tick_length) * math.sin(sub_angle_rad)
                    canvas.create_line(sx_tick_start, sy_tick_start, sx_tick_end, sy_tick_end, fill=fg, width=1, tags="vu_element")

            # Text label
            if scale_numbers:
                text_radius_pos = main_arc_radius + text_offset_from_arc
                tx = center_x + text_radius_pos * math.cos(current_angle_rad)
                ty = center_y - text_radius_pos * math.sin(current_angle_rad)
                canvas.create_text(
                    tx, ty, text=f"{int(tick_val)}", fill=fg, font=("Helvetica", 8), tags="vu_element"
                )

        # --- Draw Arcs ---
        green_start_norm = (
            (red_zone_start - min_val) / (max_val - min_val) if max_val > min_val else 0
        )
        
        if counter_clockwise:
            # Green Zone: From Min to red_zone_start
            # Min is at end_angle_deg. red_zone_start is at transition angle.
            transition_angle_deg = end_angle_deg + (green_start_norm * extent_deg)
            
            # Lower Color Arc (Green): From End to Transition (CCW)
            canvas.create_arc(
                center_x - main_arc_radius,
                center_y - main_arc_radius,
                center_x + main_arc_radius,
                center_y + main_arc_radius,
                start=end_angle_deg,
                extent=(transition_angle_deg - end_angle_deg),
                style=tk.ARC,
                outline=lower_colour,
                width=arc_thickness,
                tags="vu_element"
            )
            
            # Upper Color Arc (Red): From Transition to Start (CCW)
            canvas.create_arc(
                center_x - main_arc_radius,
                center_y - main_arc_radius,
                center_x + main_arc_radius,
                center_y + main_arc_radius,
                start=transition_angle_deg,
                extent=(start_angle_deg - transition_angle_deg),
                style=tk.ARC,
                outline=upper_colour,
                width=arc_thickness,
                tags="vu_element"
            )
        else:
            # Standard CW
            # Green Zone: From Min to red_zone_start
            # Min is at start_angle_deg. red_zone_start is at transition.
            transition_angle_deg = start_angle_deg - (green_start_norm * extent_deg)
            
            # Lower Color Arc (Green): From Start to Transition (CW)
            # Tkinter arcs draw CCW. So we must draw from Transition to Start? No, Start=Start, Extent=negative.
            # But tk.create_arc extent is always relative to start.
            # To draw CW from Start, we assume Start is the Leftmost (Largest angle).
            # Green segment is Min->Transition.
            # Min is Start. Transition is < Start.
            # So segment is Start -> Transition.
            # In Tkinter, Start=Transition, Extent = (Start - Transition).
            canvas.create_arc(
                center_x - main_arc_radius,
                center_y - main_arc_radius,
                center_x + main_arc_radius,
                center_y + main_arc_radius,
                start=transition_angle_deg,
                extent=(start_angle_deg - transition_angle_deg),
                style=tk.ARC,
                outline=lower_colour,
                width=arc_thickness,
                tags="vu_element"
            )

            # Upper Color Arc (Red): From Transition to End (Max)
            # Segment Transition -> End.
            # Transition > End.
            # Start=End, Extent=(Transition - End)
            canvas.create_arc(
                center_x - main_arc_radius,
                center_y - main_arc_radius,
                center_x + main_arc_radius,
                center_y + main_arc_radius,
                start=end_angle_deg,
                extent=(transition_angle_deg - end_angle_deg),
                style=tk.ARC,
                outline=upper_colour,
                width=arc_thickness,
                tags="vu_element"
            )

        # --- Helper for Drawing Needle ---
        def draw_single_needle(val, color):
            if val < min_val: val = min_val
            if val > max_val: val = max_val

            norm_val = (val - min_val) / (max_val - min_val) if max_val > min_val else 0

            if counter_clockwise:
                needle_angle_deg = end_angle_deg + (norm_val * extent_deg)
            else:
                needle_angle_deg = start_angle_deg - (norm_val * extent_deg)
                
            needle_angle_rad = math.radians(needle_angle_deg)

            # Make needle extend into the numbers
            needle_total_len = main_arc_radius + text_offset_from_arc - 2

            # Tip calculation
            tip_x = center_x + needle_total_len * math.cos(needle_angle_rad)
            tip_y = center_y - needle_total_len * math.sin(needle_angle_rad)

            if pointer_style == "taper" or pointer_style == "teardrop":
                # Base corners calculation
                # Perpendicular to the needle direction
                perp_angle_rad = needle_angle_rad + (math.pi / 2)
                base_radius = pivot_size / 2.0
                
                base_x1 = center_x + base_radius * math.cos(perp_angle_rad)
                base_y1 = center_y - base_radius * math.sin(perp_angle_rad)
                base_x2 = center_x - base_radius * math.cos(perp_angle_rad)
                base_y2 = center_y + base_radius * math.sin(perp_angle_rad)
                
                # Taper is a triangle
                # Teardrop is smoothed. 
                # For teardrop, we can add control points or just use smooth=True
                # A teardrop needs to be rounded at the bottom (pivot).
                # We can simulate this by adding points BEHIND the pivot?
                # Or just relying on the pivot circle to cover the base.
                # Actually, "upside down heart" implies the lobes are at the pivot.
                # If we draw a triangle and smooth it, it might just look like a blob.
                # Let's add a "back" point for teardrop to round it out.
                
                points = [base_x1, base_y1, tip_x, tip_y, base_x2, base_y2]
                
                if pointer_style == "teardrop":
                    # Add a point behind center to round the base
                    back_len = base_radius * 0.8
                    back_x = center_x - back_len * math.cos(needle_angle_rad)
                    back_y = center_y + back_len * math.sin(needle_angle_rad)
                    # Insert back point between base_x2 and base_x1 (closing the loop)
                    points.extend([back_x, back_y])
                    
                canvas.create_polygon(points, fill=color, outline=color, smooth=(pointer_style=="teardrop"), tags="vu_element")
                
            else:
                # Line style
                canvas.create_line(
                    center_x, center_y, tip_x, tip_y, width=needle_thickness, fill=color, capstyle=tk.ROUND, tags="vu_element"
                )

        # --- Draw Needles ---
        draw_single_needle(value, pointer_colour)
        
        if value2 is not None and pointer_colour2:
            draw_single_needle(value2, pointer_colour2)

        # --- Draw Pivot ---
        pivot_radius = pivot_size / 2.0
        canvas.create_oval(
            center_x - pivot_radius,
            center_y - pivot_radius,
            center_x + pivot_radius,
            center_y + pivot_radius,
            fill=fg,
            outline=secondary,
            tags="vu_element"
        )
        
        # Ensure VU meter elements are behind any overlays (like the Knob in composite widgets)
        canvas.tag_lower("vu_element")