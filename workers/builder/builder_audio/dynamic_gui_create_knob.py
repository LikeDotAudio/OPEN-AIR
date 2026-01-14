# builder_audio/dynamic_gui_create_knob.py
#
# A Tkinter Canvas-based Rotary Knob that respects the global theme.
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

class CustomKnobFrame(ttk.Frame):
    def __init__(
        self,
        parent,
        variable,
        min_val,
        max_val,
        reff_point,
        path,
        state_mirror_engine,
        command,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.variable = variable
        self.min_val = min_val
        self.max_val = max_val
        self.reff_point = reff_point
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
        except ValueError:
            pass
        self._destroy_manual_entry(event)

    def _destroy_manual_entry(self, event):
        if self.temp_entry and self.temp_entry.winfo_exists():
            self.temp_entry.destroy()
            self.temp_entry = None


class KnobCreatorMixin:
    def _create_knob(self, parent_widget, config_data, **kwargs):
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
        indicator_color = config.get("indicator_color", accent_color)

        min_val = float(config.get("min", 0.0))
        max_val = float(config.get("max", 100.0))
        reff_point = float(config.get("reff_point", (min_val + max_val) / 2.0))
        value_default = float(config.get("value_default", 0.0))
        infinity = config.get("infinity", False)
        fine_pitch = config.get("fine_pitch", False)

        knob_value_var = tk.DoubleVar(value=value_default)
        drag_state = {"start_y": None, "start_value": None}

        def on_knob_press(event):
            drag_state["start_y"] = event.y
            drag_state["start_value"] = knob_value_var.get()

        def on_knob_drag(event):
            if drag_state["start_y"] is None: return
            dy = drag_state["start_y"] - event.y
            
            # Sensitivity Logic
            # Standard: Full range in ~200 pixels
            base_sensitivity = (max_val - min_val) / 200.0
            if fine_pitch:
                base_sensitivity /= 10.0
            
            # Ctrl(4) + Alt(8) = 12
            if (event.state & 0x000C) == 0x000C: 
                base_sensitivity /= 2.0

            delta = dy * base_sensitivity
            raw_new_val = drag_state["start_value"] + delta

            if infinity:
                 range_span = max_val - min_val
                 new_val = min_val + ((raw_new_val - min_val) % range_span)
            else:
                new_val = max(min_val, min(max_val, raw_new_val))

            if knob_value_var.get() != new_val:
                knob_value_var.set(new_val)
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        def on_knob_release(event):
            drag_state["start_y"] = None
            drag_state["start_value"] = None

        frame = CustomKnobFrame(
            parent_widget,
            variable=knob_value_var,
            min_val=min_val,
            max_val=max_val,
            reff_point=reff_point,
            path=path,
            state_mirror_engine=self.state_mirror_engine,
            command=None,
        )

        # Text Position Logic (label_Text_position)
        text_pos = config.get("label_Text_position", "top").lower()
        if label and config.get("show_label", True):
            lbl = ttk.Label(frame, text=label)
            if text_pos == "top":
                lbl.pack(side=tk.TOP, pady=(0, 5))
            elif text_pos == "bottom":
                lbl.pack(side=tk.BOTTOM, pady=(5, 0))
            elif text_pos == "left":
                lbl.pack(side=tk.LEFT, padx=(0, 5))
            elif text_pos == "right":
                lbl.pack(side=tk.RIGHT, padx=(5, 0))
            else:
                lbl.pack(side=tk.TOP, pady=(0, 5))

        try:
            width, height = config.get("width", 50), config.get("height", 50)
            canvas = tk.Canvas(frame, width=width, height=height, bg=bg_color, highlightthickness=0)
            
            if text_pos in ["left", "right"]:
                canvas.pack(side=tk.LEFT if text_pos == "right" else tk.RIGHT, expand=True)
            else:
                canvas.pack(expand=True)

            value_label = ttk.Label(frame, text=f"{int(knob_value_var.get())}", font=("Helvetica", 8))
            value_label.pack(side=tk.BOTTOM, after=canvas)

            visual_props = {"secondary": secondary_color}
            hover_color = "#999999"

            # Clean Parameter Extraction
            text_inside = config.get("text_inside", False)
            no_center = config.get("no_center", False)
            show_ticks = config.get("show_ticks", False)
            tick_length = int(config.get("tick_length", 10))
            arc_width = int(config.get("arc_width", 5))
            
            # Pointer configuration
            # Default to full radius line if not specified
            pointer_length = config.get("pointer_length", None) # If None, calculate dynamic full length
            pointer_offset = int(config.get("pointer_offset", 0)) # Distance from center start

            def update_knob_visuals(*args):
                self._draw_knob(
                    canvas, width, height, knob_value_var.get(), frame.min_val, frame.max_val, 
                    value_label, fg_color, accent_color, indicator_color, visual_props["secondary"],
                    text_inside=text_inside,
                    no_center=no_center,
                    show_ticks=show_ticks,
                    tick_length=tick_length,
                    arc_width=arc_width,
                    pointer_length=pointer_length,
                    pointer_offset=pointer_offset
                )

            knob_value_var.trace_add("write", update_knob_visuals)
            update_knob_visuals()

            def on_mousewheel(event):
                current_val = knob_value_var.get()
                val_range = frame.max_val - frame.min_val
                step = val_range * 0.05
                delta = 0
                if sys.platform == "linux":
                    if event.num == 4: delta = 1
                    elif event.num == 5: delta = -1
                else:
                    delta = 1 if event.delta > 0 else -1
                new_val = max(frame.min_val, min(frame.max_val, current_val + (delta * step)))
                knob_value_var.set(new_val)
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)

            def _bind_mousewheel(event):
                canvas.bind_all("<MouseWheel>", on_mousewheel)
                canvas.bind_all("<Button-4>", on_mousewheel)
                canvas.bind_all("<Button-5>", on_mousewheel)
                visual_props["secondary"] = hover_color
                update_knob_visuals()

            def _unbind_mousewheel(event):
                canvas.unbind_all("<MouseWheel>")
                canvas.unbind_all("<Button-4>")
                canvas.unbind_all("<Button-5>")
                visual_props["secondary"] = secondary_color
                update_knob_visuals()

            canvas.bind("<Enter>", _bind_mousewheel)
            canvas.bind("<Leave>", _unbind_mousewheel)
            canvas.bind("<Button-1>", on_knob_press)
            canvas.bind("<B1-Motion>", on_knob_drag)
            canvas.bind("<ButtonRelease-1>", on_knob_release)
            canvas.bind("<Button-2>", frame._jump_to_reff_point)
            canvas.bind("<Control-Button-1>", frame._jump_to_reff_point)
            canvas.bind("<Alt-Button-1>", frame._open_manual_entry)

            if path:
                state_mirror_engine.register_widget(path, knob_value_var, base_mqtt_topic_from_path, config)
                topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, path)
                self.subscriber_router.subscribe_to_topic(topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui)
                state_mirror_engine.initialize_widget_state(path)

            return frame
        except Exception as e:
            debug_logger(message=f"❌ The knob '{label}' shattered! Error: {e}")
            return None

    def _draw_knob(self, canvas, width, height, value, min_val, max_val, value_label, neutral_color, accent_for_arc, indicator_color, secondary, text_inside=False, no_center=False, show_ticks=False, tick_length=10, arc_width=5, pointer_length=None, pointer_offset=0):
        canvas.delete("all")
        cx, cy = width / 2, height / 2
        
        # Calculate max radius that fits
        # We need padding for the stroke width (arc_width) and potentially ticks
        padding = arc_width / 2 + 2
        if show_ticks:
            padding += tick_length + 2
            
        radius = min(width, height) / 2 - padding
        
        # Draw Background Arc
        canvas.create_arc(cx - radius, cy - radius, cx + radius, cy + radius, start=240, extent=-300, style=tk.ARC, outline=secondary, width=arc_width)
        
        norm_val_0_1 = (value - min_val) / (max_val - min_val) if max_val > min_val else 0
        norm_val = (norm_val_0_1 * 2) - 1 if (min_val < 0 and max_val >= 0) else norm_val_0_1
        
        # Color & Active Arc
        active_color = indicator_color
        val_extent = -300 * norm_val_0_1
        
        canvas.create_arc(cx - radius, cy - radius, cx + radius, cy + radius, start=240, extent=val_extent, style=tk.ARC, outline=active_color, width=arc_width)
        
        # Pointer Logic
        angle_rad = math.radians(240 + val_extent)
        
        p_start_dist = pointer_offset
        if pointer_length is None:
            # Default: from offset to just inside the arc
            p_end_dist = radius - (arc_width/2)
        else:
            p_end_dist = p_start_dist + float(pointer_length)
            
        sx = cx + p_start_dist * math.cos(angle_rad)
        sy = cy - p_start_dist * math.sin(angle_rad)
        ex = cx + p_end_dist * math.cos(angle_rad)
        ey = cy - p_end_dist * math.sin(angle_rad)
        
        canvas.create_line(sx, sy, ex, ey, fill=active_color, width=2, capstyle=tk.ROUND)
        
        # Center Dot
        if not no_center:
            canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=active_color, outline=active_color)
            
        # Text Inside
        if text_inside:
            # Hide the external label if it exists
            # (In this simple implementation, we just draw over center)
            # We might want to clear the 'value_label' text if it's being used for outside text, 
            # but value_label is passed in.
            value_label.place_forget() # Hide external
            value_label.pack_forget()
            canvas.create_text(cx, cy + (10 if not no_center else 0), text=f"{int(value)}", fill=active_color, font=("Helvetica", 8, "bold"))
        else:
             # Ensure external label is visible if not inside
             # Note: positioning is handled in _create_knob pack/grid logic which we didn't fully rewrite here, 
             # but we can at least set the text.
             value_label.config(text=f"{int(value)}")

        # Draw Ticks
        if show_ticks:
            start_angle = 240
            end_angle = 240 - 300
            step = 30 # degrees between ticks
            
            curr = start_angle
            while curr >= end_angle:
                rad = math.radians(curr)
                # Start just outside the arc
                ts_dist = radius + (arc_width/2) + 2
                te_dist = ts_dist + tick_length
                
                ts_x = cx + ts_dist * math.cos(rad)
                ts_y = cy - ts_dist * math.sin(rad)
                te_x = cx + te_dist * math.cos(rad)
                te_y = cy - te_dist * math.sin(rad)
                
                canvas.create_line(ts_x, ts_y, te_x, te_y, fill=secondary, width=1)
                curr -= step