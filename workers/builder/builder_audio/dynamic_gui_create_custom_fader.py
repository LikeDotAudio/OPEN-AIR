# builder_audio/dynamic_gui_create_custom_fader.py
#
# A vertical fader widget that adapts to the system theme.
# Includes mousewheel support and middle-click reset.
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
import sys
import os
from managers.configini.config_reader import Config
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.styling.style import THEMES, DEFAULT_THEME
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.handlers.widget_event_binder import bind_variable_trace

app_constants = Config.get_instance()

class CustomFaderFrame(tk.Frame):
    def __init__(self, master, variable, config, path, state_mirror_engine, command):
        # Extract parameters from config and provide defaults
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        fader_style = colors.get("fader_style", {})
        self.bg_color = colors.get("bg", "#2b2b2b")
        self.accent_color = colors.get("accent", "#33A1FD")
        self.neutral_color = colors.get("neutral", "#dcdcdc")
        self.track_col = colors.get("secondary", "#444444")
        self.handle_col = colors.get("fg", "#dcdcdc")

        self.min_val = float(config.get("value_min", -100.0))
        self.max_val = float(config.get("value_max", 0.0))
        self.log_exponent = float(config.get("log_exponent", 1.0))
        self.reff_point = float(
            config.get("reff_point", (self.min_val + self.max_val) / 2.0)
        )
        self.border_width = int(config.get("border_width", 0))
        self.border_color = config.get("border_color", "black")
        self.show_value = config.get("show_value", True)
        self.show_units = config.get("show_units", False)
        self.label_color = config.get("label_color", "white")
        self.value_color = config.get("value_color", "white")
        self.label_text = config.get("label_active", "")
        self.outline_col = "black"
        self.outline_width = 1
        
        # Ticks logic: config can provide "custom_ticks" explicitly or "ticks"
        self.custom_ticks = config.get("custom_ticks", config.get("ticks", None))
        
        # Custom styling
        self.tick_size = config.get("tick_size", fader_style.get("tick_size", 0.1))
        self.tick_thickness = int(config.get("tick_thickness", fader_style.get("tick_thickness", 1)))
        tick_font_family = config.get("tick_font_family", fader_style.get("tick_font_family", "Helvetica"))
        tick_font_size = config.get("tick_font_size", fader_style.get("tick_font_size", 10))
        self.tick_font = (tick_font_family, tick_font_size)
        self.tick_color = config.get("tick_color", fader_style.get("tick_color", "light grey"))
        
        self.unit_text = config.get("unit_text", "")
        self.unit_color = config.get("unit_color", self.value_color)
        self.unit_position = config.get("unit_position", "right") # "left" or "right" of the number

        self.value_follow = config.get("value_follow", fader_style.get("value_follow", True))
        self.movement_value_display = config.get("movement_value_display", True) # Master toggle for floating display
        self.value_highlight_color = config.get("value_highlight_color", fader_style.get("value_highlight_color", "#f4902c"))
        
        # Fader visual customization
        self.fader_cap_scale = float(config.get("fader_cap_scale", 1.0))
        self.fader_track_color = config.get("fader_track_color", config.get("fader_colour", self.track_col))
        self.fader_grip_color = config.get("fader_grip_color", self.handle_col)

        self.is_sliding = False

        super().__init__(
            master,
            bg=self.bg_color,
            bd=self.border_width,
            relief="solid",
            highlightbackground=self.border_color,
            highlightthickness=self.border_width,
        )
        self.variable = variable
        self.path = path
        self.state_mirror_engine = state_mirror_engine
        self.command = command
        self.temp_entry = None

    def _jump_to_reff_point(self, event):
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"⚡ User invoked Quantum Jump! Resetting to {self.reff_point}",
                **_get_log_args(),
            )

        self.variable.set(self.reff_point)
        if self.state_mirror_engine:
            self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _open_manual_entry(self, event):
        if self.temp_entry and self.temp_entry.winfo_exists():
            return

        self.temp_entry = tk.Entry(self, width=8, justify="center")
        self.temp_entry.place(x=event.x - 20, y=event.y - 10)
        current_val = self.variable.get()
        self.temp_entry.insert(0, str(current_val))
        self.temp_entry.select_range(0, tk.END)
        self.temp_entry.focus_set()
        self.temp_entry.bind("<Return>", self._submit_manual_entry)
        self.temp_entry.bind("<FocusOut>", self._submit_manual_entry)
        self.temp_entry.bind("<Escape>", self._destroy_manual_entry)

    def _submit_manual_entry(self, event):
        raw_value = self.temp_entry.get()
        try:
            new_value = float(raw_value)
            if self.min_val <= new_value <= self.max_val:
                self.variable.set(new_value)
                if self.state_mirror_engine:
                    self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)
            else:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚠️ Value {new_value} out of bounds! Ignoring.",
                        **_get_log_args(),
                    )
        except ValueError:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ Invalid manual entry: '{raw_value}' is not a number.",
                    **_get_log_args(),
                )
        self._destroy_manual_entry(event)

    def _destroy_manual_entry(self, event):
        if self.temp_entry and self.temp_entry.winfo_exists():
            self.temp_entry.destroy()
            self.temp_entry = None


class CustomFaderCreatorMixin:
    def _create_custom_fader(self, parent_widget, config_data, **kwargs):
        label = config_data.get("label_active")
        config = config_data
        path = config_data.get("path")

        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg_color = colors.get("bg", "#2b2b2b")
        fg_color = colors.get("fg", "#dcdcdc")
        accent_color = colors.get("accent", "#33A1FD")
        secondary_color = colors.get("secondary", "#444444")

        min_val = float(config.get("value_min", -100.0))
        max_val = float(config.get("value_max", 0.0))
        value_default = float(config.get("value_default", 75.0))

        fader_value_var = tk.DoubleVar(value=value_default)

        def on_drag_or_click_callback(event):
            canvas = event.widget
            height = canvas.winfo_height()
            norm_y_inverted = (event.y - 20) / (height - 40)
            norm_y_inverted = max(0.0, min(1.0, norm_y_inverted))
            norm_pos = 1.0 - norm_y_inverted
            if frame.log_exponent != 1.0 and (frame.max_val - frame.min_val) != 0:
                log_norm_pos = max(0.0000001, norm_pos) ** frame.log_exponent
            else:
                log_norm_pos = norm_pos
            current_value = frame.min_val + log_norm_pos * (frame.max_val - frame.min_val)
            frame.variable.set(current_value)
            if state_mirror_engine:
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        frame = CustomFaderFrame(
            parent_widget,
            variable=fader_value_var,
            config=config,
            path=path,
            state_mirror_engine=self.state_mirror_engine,
            command=on_drag_or_click_callback,
        )

        layout_config = config.get("layout", {})
        font_size = layout_config.get("font", 10)
        custom_font = ("Helvetica", font_size)
        custom_colour = layout_config.get("colour", None)

        if label:
            lbl = tk.Label(frame, text=label, font=custom_font, background=bg_color, foreground=fg_color)
            if custom_colour:
                lbl.configure(foreground=custom_colour)
            lbl.pack(side=tk.TOP, pady=(0, 5))

        try:
            width = layout_config.get("width", 60)
            height = layout_config.get("height", 200)

            canvas = tk.Canvas(
                frame, width=width, height=height, bg=bg_color, highlightthickness=0
            )
            canvas.pack(fill=tk.BOTH, expand=True)
            canvas.update_idletasks()

            value_label = tk.Label(
                frame, text=f"{int(fader_value_var.get())}", font=("Helvetica", 8), background=bg_color, foreground=fg_color
            )
            value_label.pack(side=tk.BOTTOM)

            visual_props = {"secondary": secondary_color}
            hover_color = "#999999"

            def on_fader_value_change(*args):
                current_fader_val = fader_value_var.get()
                current_w = canvas.winfo_width()
                current_h = canvas.winfo_height()
                if current_w <= 1: current_w = width
                if current_h <= 1: current_h = height

                self._draw_fader(frame, canvas, current_w, current_h, current_fader_val, visual_props["secondary"])

                norm_val = (
                    (current_fader_val - frame.min_val) / (frame.max_val - frame.min_val)
                    if (frame.max_val - frame.min_val) != 0 else 0
                )
                active_color = frame.neutral_color if abs(norm_val) < 0.01 else frame.value_highlight_color
                
                val_text = f"{int(current_fader_val)}"
                if frame.show_units and frame.unit_text:
                    if frame.unit_position == "left":
                        val_text = f"{frame.unit_text} {val_text}"
                    else:
                        val_text = f"{val_text} {frame.unit_text}"
                
                value_label.config(text=val_text, foreground=active_color)

            fader_value_var.trace_add("write", on_fader_value_change)
            on_fader_value_change()

            def on_mousewheel(event):
                current_val = fader_value_var.get()
                val_range = frame.max_val - frame.min_val
                step = val_range * 0.05
                delta = 0
                if sys.platform == "linux":
                    if event.num == 4: delta = 1
                    elif event.num == 5: delta = -1
                else:
                    delta = 1 if event.delta > 0 else -1
                new_val = current_val + (delta * step)
                new_val = max(frame.min_val, min(frame.max_val, new_val))
                
                # Show value display briefly during mousewheel
                frame.is_sliding = True
                fader_value_var.set(new_val)
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                
                # Reset sliding state after a short delay
                canvas.after(500, lambda: setattr(frame, 'is_sliding', False) or on_fader_value_change())

            def _bind_mousewheel(event):
                canvas.bind_all("<MouseWheel>", on_mousewheel)
                canvas.bind_all("<Button-4>", on_mousewheel)
                canvas.bind_all("<Button-5>", on_mousewheel)
                visual_props["secondary"] = hover_color
                on_fader_value_change()

            def _unbind_mousewheel(event):
                canvas.unbind_all("<MouseWheel>")
                canvas.unbind_all("<Button-4>")
                canvas.unbind_all("<Button-5>")
                visual_props["secondary"] = secondary_color
                on_fader_value_change()

            canvas.bind("<Enter>", _bind_mousewheel)
            canvas.bind("<Leave>", _unbind_mousewheel)

            def start_sliding(event):
                frame.is_sliding = True
                frame.command(event)

            def stop_sliding(event):
                frame.is_sliding = False
                on_fader_value_change()

            canvas.bind("<Button-1>", start_sliding)
            canvas.bind("<B1-Motion>", frame.command)
            canvas.bind("<ButtonRelease-1>", stop_sliding)
            canvas.bind("<Button-2>", frame._jump_to_reff_point)
            canvas.bind("<Control-Button-1>", frame._jump_to_reff_point)
            canvas.bind("<Alt-Button-1>", frame._open_manual_entry)
            canvas.bind("<Configure>", lambda e: on_fader_value_change())

            if path:
                state_mirror_engine.register_widget(path, fader_value_var, base_mqtt_topic_from_path, config)
                topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, path)
                self.subscriber_router.subscribe_to_topic(topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui)
                state_mirror_engine.initialize_widget_state(path)

            return frame
        except Exception as e:
            debug_logger(message=f"❌ The custom fader for '{label}' melted! Error: {e}")
            return None

    def _draw_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1, x1 + radius, y1, x2 - radius, y1, x2 - radius, y1,
            x2, y1, x2, y1 + radius, x2, y1 + radius, x2, y2 - radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x2 - radius, y2,
            x1 + radius, y2, x1 + radius, y2, x1, y2, x1, y2 - radius,
            x1, y2 - radius, x1, y1 + radius, x1, y1 + radius, x1, y1,
        ]
        return canvas.create_polygon(points, **kwargs, smooth=True)

    def _draw_fader(self, frame_instance, canvas, width, height, value, track_color=None):
        canvas.delete("all")
        cx = width / 2
        # Use customized track color
        t_col = frame_instance.fader_track_color if frame_instance.fader_track_color else (track_color if track_color else frame_instance.track_col)
        
        canvas.create_line(cx, 20, cx, height - 20, fill=t_col, width=4, capstyle=tk.ROUND)
        
        norm_value = ((value - frame_instance.min_val) / (frame_instance.max_val - frame_instance.min_val) if (frame_instance.max_val - frame_instance.min_val) != 0 else 0)
        norm_value = max(0.0, min(1.0, norm_value))
        display_norm_pos = max(0.0000001, norm_value) ** (1.0 / frame_instance.log_exponent) if frame_instance.log_exponent != 1.0 else norm_value
        handle_y = (height - 40) * (1.0 - display_norm_pos) + 20
        
        tick_length_half = width * frame_instance.tick_size
        
        # Use custom_ticks if provided, otherwise default generation
        if frame_instance.custom_ticks is not None:
             tick_values = frame_instance.custom_ticks
        else:
             value_range = frame_instance.max_val - frame_instance.min_val
             if value_range <= 10:
                 tick_interval = 2
             elif value_range <= 50:
                 tick_interval = 5
             elif value_range <= 100:
                 tick_interval = 10
             elif value_range <= 1000:
                 tick_interval = 100
             elif value_range <= 5000:
                 tick_interval = 250
             elif value_range <= 10000:
                 tick_interval = 1000
             else:
                 tick_interval = 2500

             tick_values = []
             if tick_interval > 0:
                 current_tick = (
                     math.ceil(frame_instance.min_val / tick_interval) * tick_interval
                 )
                 while current_tick <= frame_instance.max_val:
                     tick_values.append(current_tick)
                     current_tick += tick_interval

        for i, tick_value in enumerate(tick_values):
            linear_tick_norm = max(0.0, min(1.0, (tick_value - frame_instance.min_val) / (frame_instance.max_val - frame_instance.min_val) if (frame_instance.max_val - frame_instance.min_val) != 0 else 0))
            display_tick_norm = max(0.0000001, linear_tick_norm) ** (1.0 / frame_instance.log_exponent) if frame_instance.log_exponent != 1.0 else linear_tick_norm
            tick_y_pos = (height - 40) * (1 - display_tick_norm) + 20
            
            canvas.create_line(cx - tick_length_half, tick_y_pos, cx + tick_length_half, tick_y_pos, fill=frame_instance.tick_color, width=frame_instance.tick_thickness)
            
            # Simple logic to avoid overlapping text on every tick if auto-generated, but if custom, show all?
            # Keeping the i%2 logic for auto, but for custom maybe show all.
            show_label = True
            if frame_instance.custom_ticks is None and i % 2 != 0:
                show_label = False
            
            if show_label:
                t_text = str(int(tick_value))
                canvas.create_text(cx + 15, tick_y_pos, text=t_text, fill=frame_instance.tick_color, font=frame_instance.tick_font, anchor="w")
        
        # Scale Fader Cap
        scale = frame_instance.fader_cap_scale
        cap_width, cap_height = 40 * scale, 50 * scale
        
        grip_col = frame_instance.fader_grip_color if frame_instance.fader_grip_color else frame_instance.handle_col
        
        self._draw_rounded_rectangle(canvas, cx - cap_width / 2, handle_y - cap_height / 2, cx + cap_width / 2, handle_y + cap_height / 2, radius=10 * scale, fill=grip_col, outline=t_col)
        
        # Floating Value Display
        if frame_instance.movement_value_display and frame_instance.value_follow and frame_instance.is_sliding:
            # Simple value, no units, smaller font
            val_str = f"{value:.1f}" # Slightly less precision for small text
            
            # Position bottom of text at the center line of fader cap
            text_y = handle_y
            
            # Smaller font for movement display
            small_font = ("Helvetica", 6)
            
            # Use grip_col for contrast (assuming grip is usually contrasting with track/bg, or needs to match it)
            # Wait, user said "colour needs to be the fader grip colour".
            # If the background of text is the fader cap (which is grip_col), then text being grip_col would be invisible.
            # "colour needs to be the fader grip colour" -> Text color = grip color.
            # But the text is drawn ON TOP of the fader cap?
            # If text is on top of cap, and cap is grip_col, text needs to be contrasting (e.g. track_col or bg_color).
            # OR, maybe the user implies the text is "etched" into it, or they just want that color.
            # However, "so there is some contrast" suggests they expect it to contrast against something.
            # If the text is floating *above* the cap (on the canvas background?), then grip_col text on bg_color is fine.
            # If the text is drawn *over* the cap rectangle, and cap is grip_col, then text=grip_col is invisible.
            
            # Let's look at Z-order.
            # 1. Track (Line)
            # 2. Ticks
            # 3. Cap (Rounded Rect, fill=grip_col)
            # 4. Floating Value (Text)
            # 5. Grip Lines
            
            # The text is drawn AFTER the cap. So it is on top of the cap.
            # If I set text fill=grip_col, and cap fill=grip_col, it will be invisible.
            # User said: "the colour needs to be the fader grip colour so there is some contrast"
            # This implies the text might be NOT over the cap, or they are confused about the colors.
            # OR, maybe they want the text to look like the grip color but placed elsewhere?
            # "bottom of the text should be at the center line". Center line of what? The fader cap handle_y.
            # If the cap is 50px tall, handle_y is the middle.
            # If text is anchor="s" at handle_y, the text sits in the TOP HALF of the fader cap.
            # Since the cap is filled with grip_col, text in grip_col will be invisible.
            
            # Re-reading: "the colour needs to be the fader grip colour so there is some contrast"
            # Maybe they mean the text color should be the TRACK color?
            # Or maybe the "fader grip colour" is dark and they want the text to be that color against a light background?
            # But here the text is on the cap.
            
            # Let's check the code:
            # grip_col = frame_instance.fader_grip_color
            # t_col = frame_instance.fader_track_color (used for outline and grip lines)
            
            # If I use t_col (track color), that usually contrasts with grip color (as seen in grip lines).
            # The grip lines use t_col.
            # Maybe the user meant "match the grip lines" or "contrast with the grip".
            # "colour needs to be the fader grip colour" is very specific though.
            
            # Hypothsis: The user might be thinking of "contrast" against the *background* if the text was outside?
            # But here it is inside.
            
            # Let's look at the instruction again: "and the colour needs to be the fader grip colour so there is some contrast"
            # This phrasing is tricky. "Make it X so it contrasts". Implies X contrasts with the background.
            # Background is the fader cap (filled with grip_col).
            # So grip_col contrasts with grip_col? No.
            
            # Maybe they mean "fader TRACK colour"? Track is usually dark/contrasting.
            # OR maybe they mean the text should be the *Inverse*?
            
            # Let's assume they made a typo and meant "fader TRACK color" or "outline color" which is `t_col`.
            # `t_col` is used for the grip lines on the cap. The text is effectively another "marking" on the cap.
            # So `t_col` is the safest bet for visibility/style consistency.
            # Wait, if I literally follow "colour needs to be the fader grip colour", I will make invisible text.
            # Unless... `grip_col` is NOT the fill of the cap?
            # `self._draw_rounded_rectangle(..., fill=grip_col, ...)` -> Yes it is.
            
            # I will assume they meant "contrast WITH the fader grip colour" -> use `t_col` (Track/Line color).
            # That matches the "Grip Lines" which are also drawn on the cap using `t_col`.
            
            # However, looking at the previous prompt/context, often users say "make it green" when it's already green.
            # But "so there is some contrast" is the key.
            # I will use `t_col` (Track Color) which is the color of the lines on the grip.
            # This makes the text look like it's part of the grip markings.
            
            canvas.create_text(cx, text_y, text=val_str, fill=t_col, font=small_font, anchor="s")
            
        # Grip Lines (scaled)
        canvas.create_line(cx - cap_width * 0.45, handle_y, cx + cap_width * 0.45, handle_y, fill=t_col, width=2)
        y_offset = cap_height * 0.25
        canvas.create_line(cx - cap_width * 0.3, handle_y - y_offset, cx + cap_width * 0.3, handle_y - y_offset, fill=t_col, width=1)
        canvas.create_line(cx - cap_width * 0.3, handle_y + y_offset, cx + cap_width * 0.3, handle_y + y_offset, fill=t_col, width=1)