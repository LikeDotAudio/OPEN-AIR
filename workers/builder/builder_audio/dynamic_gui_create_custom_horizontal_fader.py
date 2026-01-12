# builder_audio/dynamic_gui_create_custom_horizontal_fader.py
#
# A horizontal fader widget that adapts to the system theme.
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
from managers.configini.config_reader import Config

app_constants = Config.get_instance()

# --- Default Fader Configuration Constants ---
DEFAULT_FADER_HEIGHT = 80 # Default height for the fader canvas
DEFAULT_MIN_VAL = 0.0
DEFAULT_MAX_VAL = 100.0
DEFAULT_LOG_EXPONENT = 1.0
DEFAULT_REFF_POINT_RATIO = 0.5 # Percentage of range for default reff point
DEFAULT_BORDER_WIDTH = 0
DEFAULT_BORDER_COLOR = "black"
DEFAULT_SHOW_VALUE = True
DEFAULT_SHOW_UNITS = False
DEFAULT_LABEL_COLOR = "white"
DEFAULT_VALUE_COLOR = "white"
DEFAULT_OUTLINE_COLOR = "black"
DEFAULT_OUTLINE_WIDTH = 1
DEFAULT_TICK_SIZE_RATIO = 0.2 # Relative to height
DEFAULT_TICK_FONT_FAMILY = "Helvetica"
DEFAULT_TICK_FONT_SIZE = 10
DEFAULT_TICK_COLOR = "light grey"
DEFAULT_VALUE_FOLLOW = True
DEFAULT_VALUE_HIGHLIGHT_COLOR = "#f4902c"
DEFAULT_CAP_WIDTH = 30
DEFAULT_CAP_HEIGHT_RATIO = 0.5
DEFAULT_CAP_RADIUS = 10
DEFAULT_CAP_OUTLINE_COLOR = "black" # Using track_col by default
# ---------------------------------------------

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.styling.style import THEMES, DEFAULT_THEME
import os
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.handlers.widget_event_binder import bind_variable_trace


class CustomHorizontalFaderFrame(tk.Frame):
    def __init__(
        self,
        master,
        variable,
        config,
        path,
        state_mirror_engine,
        command,
        tick_interval=None,
    ):
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        fader_style = colors.get("fader_style", {})

        self.bg_color = colors.get("bg", "#2b2b2b")
        self.accent_color = colors.get("accent", "#33A1FD")
        self.neutral_color = colors.get("neutral", "#dcdcdc")
        self.track_col = colors.get("secondary", "#444444")
        self.handle_col = colors.get("fg", "#dcdcdc")

        self.min_val = float(config.get("value_min", DEFAULT_MIN_VAL))
        self.max_val = float(config.get("value_max", DEFAULT_MAX_VAL))
        self.log_exponent = float(config.get("log_exponent", DEFAULT_LOG_EXPONENT))
        self.reff_point = float(
            config.get("reff_point", (self.min_val + self.max_val) / 2.0)
        )
        self.border_width = int(config.get("border_width", DEFAULT_BORDER_WIDTH))
        self.border_color = config.get("border_color", DEFAULT_BORDER_COLOR)
        self.show_value = config.get("show_value", DEFAULT_SHOW_VALUE)
        self.show_units = config.get("show_units", DEFAULT_SHOW_UNITS)
        self.label_color = config.get("label_color", DEFAULT_LABEL_COLOR)
        self.value_color = config.get("value_color", DEFAULT_VALUE_COLOR)
        self.label_text = config.get("label_active", "")
        self.outline_col = DEFAULT_OUTLINE_COLOR
        self.outline_width = DEFAULT_OUTLINE_WIDTH
        self.ticks = config.get("ticks", None)
        self.tick_interval = tick_interval

        # Fader Cap Styling
        self.cap_width = int(config.get("cap_width", DEFAULT_CAP_WIDTH))
        self.cap_height_ratio = float(config.get("cap_height_ratio", DEFAULT_CAP_HEIGHT_RATIO))
        self.cap_radius = int(config.get("cap_radius", DEFAULT_CAP_RADIUS))
        self.cap_color = config.get("cap_color", self.handle_col) # Defaults to handle_col from theme
        self.cap_outline_color = config.get("cap_outline_color", self.track_col) # Defaults to track_col from theme


        # Custom styling
        self.tick_size = config.get("tick_size", fader_style.get("tick_size", DEFAULT_TICK_SIZE_RATIO))
        tick_font_family = config.get("tick_font_family", fader_style.get("tick_font_family", DEFAULT_TICK_FONT_FAMILY))
        tick_font_size = config.get("tick_font_size", fader_style.get("tick_font_size", DEFAULT_TICK_FONT_SIZE))
        self.tick_font = (tick_font_family, tick_font_size)
        self.tick_color = config.get("tick_color", fader_style.get("tick_color", DEFAULT_TICK_COLOR))
        self.value_follow = config.get("value_follow", fader_style.get("value_follow", DEFAULT_VALUE_FOLLOW))
        self.value_highlight_color = config.get("value_highlight_color", fader_style.get("value_highlight_color", DEFAULT_VALUE_HIGHLIGHT_COLOR))


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


class CustomHorizontalFaderCreatorMixin:

    def _create_custom_horizontal_fader(self, parent_widget, config_data, **kwargs):
        label = config_data.get("label_active")
        config = config_data
        path = config_data.get("path")
        tick_interval = config_data.get("tick_interval")

        layout_config = config.get("layout", {})
        font_size = layout_config.get("font", 10)
        custom_font = ("Helvetica", font_size)
        custom_colour = layout_config.get("colour", None)

        state_mirror_engine = self.state_mirror_engine
        subscriber_router = self.subscriber_router
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg_color = colors.get("bg", "#2b2b2b")

        min_val = float(config.get("value_min", 0.0))
        max_val = float(config.get("value_max", 100.0))
        value_default = float(config.get("value_default", 50.0))

        fader_value_var = tk.DoubleVar(value=value_default)

        def on_drag_or_click_callback(event):
            canvas = event.widget
            width = canvas.winfo_width()
            norm_x = (event.x - 10) / (width - 20)
            norm_x = max(0.0, min(1.0, norm_x))

            log_norm_pos = norm_x**frame.log_exponent
            current_value = frame.min_val + log_norm_pos * (
                frame.max_val - frame.min_val
            )
            frame.variable.set(current_value)

            if state_mirror_engine:
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        frame = CustomHorizontalFaderFrame(
            parent_widget,
            variable=fader_value_var,
            config=config,
            path=path,
            state_mirror_engine=self.state_mirror_engine,
            command=on_drag_or_click_callback,
            tick_interval=tick_interval,
        )
        if label:
            lbl = tk.Label(frame, text=label, font=custom_font, background=bg_color, foreground=colors.get("fg", "#dcdcdc"))
            if custom_colour:
                lbl.configure(foreground=custom_colour)
            lbl.pack(side=tk.TOP, pady=(0, 5))

        width = layout_config.get("width", 200)
        height = layout_config.get("height", DEFAULT_FADER_HEIGHT)

        canvas = tk.Canvas(
            frame, width=width, height=height, bg=bg_color, highlightthickness=0
        )
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.update_idletasks()

        def on_fader_value_change(*args):
            current_fader_val = fader_value_var.get()
            
            # Use winfo or fall back to config dimensions if not yet mapped
            current_w = canvas.winfo_width()
            current_h = canvas.winfo_height()
            if current_w <= 1: current_w = width
            if current_h <= 1: current_h = height

            self._draw_horizontal_fader(
                frame,
                canvas,
                current_w,
                current_h,
                current_fader_val,
            )

        fader_value_var.trace_add("write", on_fader_value_change)
        on_fader_value_change()

        canvas.bind("<B1-Motion>", frame.command)
        canvas.bind("<Button-1>", frame.command)
        canvas.bind("<Control-Button-1>", frame._jump_to_reff_point)
        canvas.bind("<Alt-Button-1>", frame._open_manual_entry)
        canvas.bind("<Configure>", lambda e: on_fader_value_change())

        if path:
            widget_id = path
            state_mirror_engine.register_widget(widget_id, fader_value_var, base_mqtt_topic_from_path, config_data)
            callback = lambda: state_mirror_engine.broadcast_gui_change_to_mqtt(widget_id)
            bind_variable_trace(fader_value_var, callback)
            topic = state_mirror_engine.get_widget_topic(widget_id)
            if topic:
                subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
            state_mirror_engine.initialize_widget_state(widget_id)
        return frame

    def _draw_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1, x1 + radius, y1, x2 - radius, y1, x2 - radius, y1,
            x2, y1, x2, y1 + radius, x2, y1 + radius, x2, y2 - radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x2 - radius, y2,
            x1 + radius, y2, x1 + radius, y2, x1, y2, x1, y2 - radius,
            x1, y2 - radius, x1, y1 + radius, x1, y1 + radius, x1, y1,
        ]
        return canvas.create_polygon(points, **kwargs, smooth=True)

    def _draw_horizontal_fader(self, frame_instance, canvas, width, height, value):
        canvas.delete("all")
        cy = height / 2
        canvas.create_line(
            10,
            cy,
            width - 10,
            cy,
            fill=frame_instance.track_col,
            width=4,
            capstyle=tk.ROUND,
        )

        norm_value = (
            (value - frame_instance.min_val)
            / (frame_instance.max_val - frame_instance.min_val)
            if (frame_instance.max_val - frame_instance.min_val) != 0
            else 0
        )
        norm_value = max(0.0, min(1.0, norm_value))

        display_norm_pos = norm_value ** (1.0 / frame_instance.log_exponent)
        handle_x = (width - 20) * display_norm_pos + 10

        # Draw the fill line
        canvas.create_line(
            10,
            cy - 2.5,  # Adjust to be centered above cy with width 5
            handle_x,
            cy - 2.5,  # Same y-coordinate for a straight line
            fill=frame_instance.value_highlight_color,
            width=5,
            capstyle=tk.ROUND,
        )

        tick_length_half = height * frame_instance.tick_size

        tick_values_to_draw = []
        if frame_instance.ticks is not None:
            tick_values_to_draw = frame_instance.ticks
        else:
            value_range = frame_instance.max_val - frame_instance.min_val
            if value_range <= 10:
                tick_interval = 2
            elif value_range <= 50:
                tick_interval = 5
            elif value_range <= 100:
                tick_interval = 10
            elif value_range <= 1000:
                tick_interval = 50
            elif value_range <= 5000:
                tick_interval = 250
            else: 
                tick_interval = 500

            if tick_interval > 0:
                current_tick = (
                    math.ceil(frame_instance.min_val / tick_interval) * tick_interval
                )
                while current_tick <= frame_instance.max_val:
                    tick_values_to_draw.append(current_tick)
                    current_tick += tick_interval

        for i, tick_value in enumerate(tick_values_to_draw):
            linear_tick_norm = (
                (tick_value - frame_instance.min_val)
                / (frame_instance.max_val - frame_instance.min_val)
                if (frame_instance.max_val - frame_instance.min_val) != 0
                else 0
            )
            if 0.0 <= linear_tick_norm <= 1.0:
                display_tick_norm = linear_tick_norm
                tick_x_pos = (width - 20) * display_tick_norm + 10
                canvas.create_line(
                    tick_x_pos,
                    cy - tick_length_half,
                    tick_x_pos,
                    cy + tick_length_half,
                    fill=frame_instance.tick_color,
                    width=1,
                )
                if i % 2 == 0:
                    canvas.create_text(
                        tick_x_pos,
                        cy + 25,
                        text=str(int(tick_value)),
                        fill=frame_instance.tick_color,
                        font=frame_instance.tick_font,
                        anchor="n",
                    )

        cap_width = frame_instance.cap_width
        cap_height = height * frame_instance.cap_height_ratio
        self._draw_rounded_rectangle(
            canvas,
            handle_x - cap_width / 2,
            cy - cap_height / 2,
            handle_x + cap_width / 2,
            cy + cap_height / 2,
            radius=frame_instance.cap_radius,
            fill=frame_instance.cap_color,
            outline=frame_instance.cap_outline_color,
        )

        if frame_instance.value_follow:
            canvas.create_text(
                handle_x,
                cy - cap_height / 2 - 5,
                text=f"{value:.2f}",
                fill=frame_instance.value_color,
                anchor="s"
            )

        center_line_length = cap_height * 0.9
        canvas.create_line(
            handle_x,
            cy - center_line_length / 2,
            handle_x,
            cy + center_line_length / 2,
            fill=frame_instance.track_col,
            width=2,
        )

        side_line_length = cap_height * 0.6
        x_offset = cap_width * 0.25
        canvas.create_line(
            handle_x - x_offset,
            cy - side_line_length / 2,
            handle_x - x_offset,
            cy + side_line_length / 2,
            fill=frame_instance.track_col,
            width=1,
        )
        canvas.create_line(
            handle_x + x_offset,
            cy - side_line_length / 2,
            handle_x + x_offset,
            cy + side_line_length / 2,
            fill=frame_instance.track_col,
            width=1,
        )
