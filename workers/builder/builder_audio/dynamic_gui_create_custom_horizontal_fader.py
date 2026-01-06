# workers/builder/builder_audio/dynamic_gui_create_custom_horizontal_fader.py
#
# A horizontal fader widget that adapts to the system theme.

import tkinter as tk
from tkinter import ttk
import math
from managers.configini.config_reader import Config

app_constants = Config.get_instance()
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.styling.style import THEMES, DEFAULT_THEME
import os
from workers.mqtt.mqtt_topic_utils import get_topic


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
        # Extract parameters from config and provide defaults
        # Theme Resolution
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        self.bg_color = colors.get("bg", "#2b2b2b")
        self.accent_color = colors.get("accent", "#33A1FD")
        self.neutral_color = colors.get("neutral", "#dcdcdc")
        self.track_col = colors.get("secondary", "#444444")
        self.handle_col = colors.get("fg", "#dcdcdc")

        # Widget-specific config values
        self.min_val = float(config.get("value_min", 0.0))
        self.max_val = float(config.get("value_max", 100.0))
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
        self.outline_col = "black"  # Not configurable at the moment
        self.outline_width = 1  # Not configurable at the moment
        self.ticks = config.get("ticks", None)
        self.tick_interval = tick_interval  # Store the passed tick_interval

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
        self.command = (
            command  # The function to call when value changes (e.g., on_drag_or_click)
        )
        self.temp_entry = None  # Initialize temp_entry

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
    def _create_custom_horizontal_fader(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        """Creates a custom horizontal fader widget."""
        current_function_name = "_create_custom_horizontal_fader"

        # Extract only widget-specific config from config_data
        label = config_data.get("label_active")
        config = config_data  # config_data is the config
        path = config_data.get("path")
        tick_interval = config_data.get(
            "tick_interval"
        )  # Extract tick_interval from config_data

        # Access global context directly from self
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

            # Apply logarithmic scaling if needed
            log_norm_pos = norm_x**frame.log_exponent
            current_value = frame.min_val + log_norm_pos * (
                frame.max_val - frame.min_val
            )
            frame.variable.set(current_value)

            # Broadcast the change from the user interaction
            if state_mirror_engine:
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        frame = CustomHorizontalFaderFrame(
            parent_widget,  # Use parent_widget here
            variable=fader_value_var,
            config=config,
            path=path,
            state_mirror_engine=self.state_mirror_engine,
            command=on_drag_or_click_callback,
            tick_interval=tick_interval,  # Pass the tick_interval
        )
        if label:
            ttk.Label(frame, text=label).pack(side=tk.TOP, pady=(0, 5))

        width = config.get("layout", {}).get("width", 200)
        height = config.get("layout", {}).get("height", 60)

        canvas = tk.Canvas(
            frame, width=width, height=height, bg=bg_color, highlightthickness=0
        )
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.update_idletasks()

        value_label = ttk.Label(
            frame, text=f"{int(fader_value_var.get())}", font=("Helvetica", 8)
        )
        value_label.pack(side=tk.BOTTOM)

        def on_fader_value_change(*args):
            current_fader_val = fader_value_var.get()
            self._draw_horizontal_fader(
                frame,
                canvas,
                canvas.winfo_width(),
                canvas.winfo_height(),
                current_fader_val,
            )
            value_label.config(text=f"{int(current_fader_val)}")

        fader_value_var.trace_add("write", on_fader_value_change)
        on_fader_value_change()

        canvas.bind("<B1-Motion>", frame.command)
        canvas.bind("<Button-1>", frame.command)
        canvas.bind("<Control-Button-1>", frame._jump_to_reff_point)
        canvas.bind("<Alt-Button-1>", frame._open_manual_entry)
        canvas.bind("<Configure>", lambda e: on_fader_value_change())

        if path:
            widget_id = path
            self.state_mirror_engine.register_widget(
                widget_id, fader_value_var, base_mqtt_topic_from_path, config
            )

            # Subscribe to the topic for incoming messages
            topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, widget_id)
            self.subscriber_router.subscribe_to_topic(
                topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui
            )
            state_mirror_engine.initialize_widget_state(path)

        return frame

    def _draw_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius,
            y1,
            x1 + radius,
            y1,
            x2 - radius,
            y1,
            x2 - radius,
            y1,
            x2,
            y1,
            x2,
            y1 + radius,
            x2,
            y1 + radius,
            x2,
            y2 - radius,
            x2,
            y2 - radius,
            x2,
            y2,
            x2 - radius,
            y2,
            x2 - radius,
            y2,
            x1 + radius,
            y2,
            x1 + radius,
            y2,
            x1,
            y2,
            x1,
            y2 - radius,
            x1,
            y2 - radius,
            x1,
            y1 + radius,
            x1,
            y1 + radius,
            x1,
            y1,
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

        # Draw Ticks
        tick_color = "light grey"
        tick_length_half = height * 0.1

        tick_values_to_draw = []
        if frame_instance.ticks is not None:
            # Use custom ticks if provided in config
            tick_values_to_draw = frame_instance.ticks
        elif (
            frame_instance.tick_interval is not None
            and frame_instance.tick_interval > 0
        ):
            # Use the passed tick_interval
            current_tick = (
                math.ceil(frame_instance.min_val / frame_instance.tick_interval)
                * frame_instance.tick_interval
            )
            while current_tick <= frame_instance.max_val:
                tick_values_to_draw.append(current_tick)
                current_tick += frame_instance.tick_interval
        else:
            # Fallback to internal dynamic tick generation if no tick_interval is provided
            value_range = frame_instance.max_val - frame_instance.min_val
            if value_range <= 10:
                tick_interval = 2
            elif value_range <= 50:
                tick_interval = 5
            elif value_range <= 100:
                tick_interval = 10
            elif value_range <= 1000:
                tick_interval = 50
            else:  # value_range > 1000
                tick_interval = 100

            # Generate ticks
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
                display_tick_norm = linear_tick_norm ** (
                    1.0 / frame_instance.log_exponent
                )
                tick_x_pos = (width - 20) * display_tick_norm + 10
                canvas.create_line(
                    tick_x_pos,
                    cy - tick_length_half,
                    tick_x_pos,
                    cy + tick_length_half,
                    fill=tick_color,
                    width=1,
                )
                if i % 2 == 0:
                    canvas.create_text(
                        tick_x_pos,
                        cy + 15,
                        text=str(int(tick_value)),
                        fill=tick_color,
                        anchor="n",
                    )

        # Handle
        cap_width = 30
        cap_height = height * 0.7
        self._draw_rounded_rectangle(
            canvas,
            handle_x - cap_width / 2,
            cy - cap_height / 2,
            handle_x + cap_width / 2,
            cy + cap_height / 2,
            radius=10,
            fill=frame_instance.handle_col,
            outline=frame_instance.track_col,
        )

        # Center line
        center_line_length = cap_height * 0.9
        canvas.create_line(
            handle_x,
            cy - center_line_length / 2,
            handle_x,
            cy + center_line_length / 2,
            fill=frame_instance.track_col,
            width=2,
        )

        # 60% lines at 25% and 75% of width
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
