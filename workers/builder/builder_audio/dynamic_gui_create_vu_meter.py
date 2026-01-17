# workers/builder/dynamic_gui_create_vu_meter.py

import tkinter as tk
from tkinter import ttk
import random
import time
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.styling.style import THEMES, DEFAULT_THEME
import os
from workers.mqtt.mqtt_topic_utils import get_topic


class VUMeterCreatorMixin:
    def _create_vu_meter(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        """Creates a VU meter widget that is state-aware."""
        current_function_name = "_create_vu_meter"

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
                message=f"🔬⚡️ Entering '{current_function_name}' to calibrate a VU meter for '{label}'.",
                **_get_log_args(),
            )

        # Theme Resolution
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg_color = colors.get("bg", "#2b2b2b")
        fg_color = colors.get("fg", "#dcdcdc")
        accent_color = colors.get("accent", "#33A1FD")
        secondary_color = colors.get("secondary", "#444444")

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
            min_val = float(config.get("min", -20.0))
            max_val = float(config.get("max", 3.0))
            value_default = float(config.get("value_default", min_val))
            red_zone_start = float(config.get("upper_range", 0.0))
            middle_zone_start = float(config.get("middle_range", red_zone_start))
            
            # Layout & Features
            base_width = int(layout_config.get("width", config.get("width", 200)))
            bar_height = int(layout_config.get("height", config.get("height", 20)))
            
            show_ticks = config.get("show_ticks", False)
            sub_ticks = int(config.get("sub_ticks", 0))
            tick_color = config.get("tick_color", bg_color) # Default to background color ("invisible" scale)
            scale_position = config.get("scale_position", "bottom").lower() # top, bottom, none
            show_peak_hold = config.get("show_peak_hold", False)
            peak_hold_time = float(config.get("peak_hold_time", 2000)) # ms

            # Calculate total canvas size
            pad_x = 5
            peak_led_size = bar_height if show_peak_hold else 0
            peak_led_gap = 5 if show_peak_hold else 0
            
            total_width = base_width + peak_led_gap + peak_led_size + (pad_x * 2)
            
            tick_height = 5 if show_ticks else 0
            text_height = 10 if scale_position != "none" else 0
            vertical_padding = tick_height + text_height + 5 if (show_ticks or scale_position != "none") else 0
            
            total_height = bar_height + vertical_padding
            
            bar_y = 0
            if scale_position == "top":
                bar_y = vertical_padding

            lower_colour = config.get("Lower_range_colour", "green")
            middle_colour = config.get("Middle_range_colour", "yellow")
            upper_colour = config.get("upper_range_Colour", "red")
            pointer_colour = config.get("Pointer_colour", "yellow")

            # Animation Parameters (Default: 100ms)
            glide_time = float(config.get("glide_time", 100))
            dwell_time = float(config.get("dwell_time", 100))
            hold_time = float(config.get("hold_time", 0))
            fall_time = float(config.get("fall_time", 100))

            vu_value_var = tk.DoubleVar(value=value_default)

            canvas = tk.Canvas(
                frame, width=total_width, height=total_height, bg="gray", highlightthickness=0
            )
            canvas.pack()

            # --- Draw Background Bar ---
            # Zone 1: Min -> Middle
            zone1_end = (middle_zone_start - min_val) / (max_val - min_val) * base_width
            zone1_end = max(0, min(base_width, zone1_end))
            
            # Zone 2: Middle -> Upper
            zone2_end = (red_zone_start - min_val) / (max_val - min_val) * base_width
            zone2_end = max(0, min(base_width, zone2_end))
            
            # Draw Zones
            # Lower (Min -> Middle)
            canvas.create_rectangle(pad_x, bar_y, pad_x + zone1_end, bar_y + bar_height, fill=lower_colour, outline="")
            
            # Middle (Middle -> Upper)
            if zone2_end > zone1_end:
                canvas.create_rectangle(pad_x + zone1_end, bar_y, pad_x + zone2_end, bar_y + bar_height, fill=middle_colour, outline="")
            
            # Upper (Upper -> Max)
            if base_width > zone2_end:
                canvas.create_rectangle(pad_x + zone2_end, bar_y, pad_x + base_width, bar_y + bar_height, fill=upper_colour, outline="")

            # --- Draw Ticks & Scale ---
            if show_ticks or scale_position != "none":
                tick_y_start = bar_y + bar_height if scale_position == "bottom" else bar_y
                tick_direction = 1 if scale_position == "bottom" else -1
                
                # Simple linear ticks with sub-ticks
                num_main_ticks = 5
                
                for i in range(num_main_ticks + 1):
                    # Main Tick
                    norm = i / num_main_ticks
                    val = min_val + norm * (max_val - min_val)
                    x_pos = pad_x + (norm * base_width)
                    
                    if show_ticks:
                        canvas.create_line(x_pos, tick_y_start, x_pos, tick_y_start + (tick_height * tick_direction), fill=tick_color, width=2)
                    
                    if scale_position != "none":
                        text_y = tick_y_start + ((tick_height + 5) * tick_direction)
                        anchor = "n" if scale_position == "bottom" else "s"
                        canvas.create_text(x_pos, text_y, text=f"{int(val)}", fill=tick_color, font=("Helvetica", 8), anchor=anchor)
                    
                    # Sub Ticks
                    if i < num_main_ticks and sub_ticks > 0:
                        step_width = base_width / num_main_ticks
                        sub_step = step_width / (sub_ticks + 1)
                        for j in range(1, sub_ticks + 1):
                            sub_x = x_pos + (j * sub_step)
                            if show_ticks:
                                # Sub ticks are half height
                                canvas.create_line(sub_x, tick_y_start, sub_x, tick_y_start + ((tick_height * 0.5) * tick_direction), fill=tick_color, width=1)

            # --- Draw Indicator ---
            indicator = canvas.create_rectangle(
                pad_x, bar_y, pad_x + 5, bar_y + bar_height, fill=pointer_colour, outline=""
            )

            # --- Draw Peak Hold LED ---
            peak_led = None
            if show_peak_hold:
                led_x = pad_x + base_width + peak_led_gap
                peak_led = canvas.create_rectangle(
                    led_x, bar_y, led_x + peak_led_size, bar_y + bar_height,
                    fill="#444444", outline="black"
                )
                
                def reset_peak(event):
                    frame.anim_peak_expiry = 0
                    canvas.itemconfig(peak_led, fill="#444444")
                
                canvas.tag_bind(peak_led, "<Button-1>", reset_peak)

            # Animation State
            frame.anim_current_value = value_default
            frame.anim_target = value_default
            frame.anim_mode = "idle" # idle, tracking, holding, decaying
            frame.anim_hold_start = 0
            frame.anim_running = False
            frame.anim_peak_expiry = 0

            def draw_indicator():
                val = frame.anim_current_value
                if val < min_val: val = min_val
                if val > max_val: val = max_val
                
                # Indicator Position
                x_pos = (
                    (val - min_val) / (max_val - min_val) * base_width
                    if max_val > min_val
                    else 0
                )
                canvas.coords(indicator, pad_x + x_pos - 2.5, bar_y, pad_x + x_pos + 2.5, bar_y + bar_height)
                
                # Peak Hold Logic
                if show_peak_hold and peak_led:
                    now_ms = time.time() * 1000
                    if val >= red_zone_start:
                        canvas.itemconfig(peak_led, fill="red")
                        frame.anim_peak_expiry = now_ms + peak_hold_time
                    elif now_ms > frame.anim_peak_expiry:
                        canvas.itemconfig(peak_led, fill="#444444")

            def animate():
                current = frame.anim_current_value
                dt = 20.0 # ms per frame
                full_range = max_val - min_val
                if full_range <= 0: full_range = 1.0

                if frame.anim_mode == "holding":
                    if (time.time() * 1000) - frame.anim_hold_start >= hold_time:
                        frame.anim_mode = "decaying"
                    else:
                        canvas.after(int(dt), animate)
                        return

                if frame.anim_mode == "tracking":
                    target = frame.anim_target
                elif frame.anim_mode == "decaying":
                    target = min_val
                else:
                    target = current

                diff = target - current
                if abs(diff) < 0.05:
                    frame.anim_current_value = target
                    draw_indicator()
                    if frame.anim_mode == "tracking":
                        if hold_time > 0:
                            frame.anim_mode = "holding"
                            frame.anim_hold_start = time.time() * 1000
                        else:
                            frame.anim_mode = "decaying"
                        canvas.after(int(dt), animate)
                        return
                    else:
                        frame.anim_mode = "idle"
                        frame.anim_running = False
                        return

                step = 0.0
                time_param = glide_time if diff > 0 else (dwell_time if frame.anim_mode == "tracking" else fall_time)
                
                if time_param <= 0:
                    step = diff
                else:
                    max_step = (full_range / time_param) * dt
                    step = min(diff, max_step) if diff > 0 else max(diff, -max_step)

                frame.anim_current_value += step
                draw_indicator()
                canvas.after(int(dt), animate)

            def on_value_change(*args):
                frame.anim_target = vu_value_var.get()
                frame.anim_mode = "tracking"
                if not frame.anim_running:
                    frame.anim_running = True
                    animate()

            vu_value_var.trace_add("write", on_value_change)
            draw_indicator()

            def on_middle_click(event):
                """Jump to a random allowed value."""
                random_val = random.uniform(min_val, max_val)
                vu_value_var.set(random_val)
                if state_mirror_engine:
                    state_mirror_engine.broadcast_gui_change_to_mqtt(path)

            canvas.bind("<Button-2>", on_middle_click)

            if path:
                widget_id = path
                state_mirror_engine.register_widget(
                    widget_id, vu_value_var, base_mqtt_topic_from_path, config
                )

                # Subscribe to the topic for incoming messages
                from workers.mqtt.mqtt_topic_utils import get_topic

                topic = get_topic(
                    self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, widget_id
                )
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
                    message=f"✅ SUCCESS! The VU meter '{label}' is now registering on the Richter scale!",
                    **_get_log_args(),
                )

            return frame
        except Exception as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ The VU meter for '{label}' has overloaded! Error: {e}",
                    **_get_log_args(),
                )
            return None
