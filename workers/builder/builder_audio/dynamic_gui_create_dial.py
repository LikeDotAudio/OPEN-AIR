# builder_audio/dynamic_gui_create_dial.py
#
# A Tkinter Canvas-based 360-degree Dial that respects the global theme.
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

class CustomDialFrame(ttk.Frame):
    def __init__(
        self,
        parent,
        variable,
        reff_point,
        path,
        state_mirror_engine,
        command,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.variable = variable
        self.min_val = 0
        self.max_val = 999
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


class DialCreatorMixin:
    def _create_dial(self, parent_widget, config_data, **kwargs):
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

        min_val, max_val = 0, 999
        reff_point = float(config.get("reff_point", (min_val + max_val) / 2.0))
        value_default = float(config.get("value_default", 0.0))

        dial_value_var = tk.DoubleVar(value=value_default)
        drag_state = {"start_y": None, "start_value": None}

        def on_dial_press(event):
            drag_state["start_y"] = event.y
            drag_state["start_value"] = dial_value_var.get()

        def on_dial_drag(event):
            if drag_state["start_y"] is None: return
            dy = drag_state["start_y"] - event.y
            sensitivity = (max_val - min_val) / 100.0
            new_val = max(min_val, min(max_val, drag_state["start_value"] + (dy * sensitivity)))
            if dial_value_var.get() != new_val:
                dial_value_var.set(new_val)
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        def on_dial_release(event):
            drag_state["start_y"] = None
            drag_state["start_value"] = None

        frame = CustomDialFrame(
            parent_widget,
            variable=dial_value_var,
            reff_point=reff_point,
            path=path,
            state_mirror_engine=self.state_mirror_engine,
            command=None,
        )

        if label and config.get("show_label", True):
            ttk.Label(frame, text=label).pack(side=tk.TOP, pady=(0, 5))

        try:
            width, height = config.get("width", 50), config.get("height", 50)
            piechart, pointer = config.get("piechart", True), config.get("pointer", True)
            canvas = tk.Canvas(frame, width=width, height=height, bg=bg_color, highlightthickness=0)
            canvas.pack(expand=True)

            visual_props = {"secondary": secondary_color}
            hover_color = "#999999"

            def update_dial_visuals(*args):
                self._draw_dial(canvas, width, height, dial_value_var.get(), frame.min_val, frame.max_val, fg_color, accent_color, indicator_color, visual_props["secondary"], piechart=piechart, pointer=pointer)

            dial_value_var.trace_add("write", update_dial_visuals)
            update_dial_visuals()

            def on_mousewheel(event):
                current_val = dial_value_var.get()
                val_range = frame.max_val - frame.min_val
                step = val_range * 0.05
                delta = 0
                if sys.platform == "linux":
                    if event.num == 4: delta = 1
                    elif event.num == 5: delta = -1
                else:
                    delta = 1 if event.delta > 0 else -1
                new_val = max(frame.min_val, min(frame.max_val, current_val + (delta * step)))
                dial_value_var.set(new_val)

            def _bind_mousewheel(event):
                canvas.bind_all("<MouseWheel>", on_mousewheel)
                canvas.bind_all("<Button-4>", on_mousewheel)
                canvas.bind_all("<Button-5>", on_mousewheel)
                visual_props["secondary"] = hover_color
                update_dial_visuals()

            def _unbind_mousewheel(event):
                canvas.unbind_all("<MouseWheel>")
                canvas.unbind_all("<Button-4>")
                canvas.unbind_all("<Button-5>")
                visual_props["secondary"] = secondary_color
                update_dial_visuals()

            canvas.bind("<Enter>", _bind_mousewheel)
            canvas.bind("<Leave>", _unbind_mousewheel)
            canvas.bind("<Button-1>", on_dial_press)
            canvas.bind("<B1-Motion>", on_dial_drag)
            canvas.bind("<ButtonRelease-1>", on_dial_release)
            canvas.bind("<Button-2>", frame._jump_to_reff_point)
            canvas.bind("<Control-Button-1>", frame._jump_to_reff_point)
            canvas.bind("<Alt-Button-1>", frame._open_manual_entry)

            if path:
                state_mirror_engine.register_widget(path, dial_value_var, base_mqtt_topic_from_path, config)
                callback = lambda: state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                bind_variable_trace(dial_value_var, callback)
                topic = state_mirror_engine.get_widget_topic(path)
                if topic:
                    subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
                state_mirror_engine.initialize_widget_state(path)

            return frame
        except Exception as e:
            debug_logger(message=f"❌ The dial '{label}' shattered! Error: {e}")
            return None

    def _draw_dial(self, canvas, width, height, value, min_val, max_val, neutral_color, accent_for_arc, indicator_color, secondary, piechart=True, pointer=True):
        canvas.delete("all")
        cx, cy = width / 2, height / 2
        radius = min(width, height) / 2 - 5
        canvas.create_arc(5, 5, width - 5, height - 5, start=0, extent=359.9, style=tk.ARC, outline=secondary, width=4)
        norm_val = (value - min_val) / (max_val - min_val) if max_val > min_val else 0
        start_angle, val_extent = 90, -360 * norm_val
        if abs(val_extent) >= 360: val_extent = -359.9
        if piechart:
            canvas.create_arc(5, 5, width - 5, height - 5, start=start_angle, extent=val_extent, style=tk.PIESLICE, fill=indicator_color, outline=indicator_color, width=1)
        if pointer:
            angle_rad = math.radians(start_angle + val_extent)
            px, py = cx + radius * math.cos(angle_rad), cy - radius * math.sin(angle_rad)
            canvas.create_line(cx, cy, px, py, fill=indicator_color, width=3, capstyle=tk.ROUND)
        text_bg_radius = radius * 0.5
        canvas.create_oval(cx - text_bg_radius, cy - text_bg_radius, cx + text_bg_radius, cy + text_bg_radius, fill="#2b2b2b", outline=secondary, width=1)
        canvas.create_text(cx, cy, text=f"{int(value)}", fill=neutral_color, font=("Helvetica", 8, "bold"))