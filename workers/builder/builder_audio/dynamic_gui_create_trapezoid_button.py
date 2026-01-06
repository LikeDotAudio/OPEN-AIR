# workers/builder/builder_audio/dynamic_gui_create_trapezoid_button.py

import tkinter as tk
from tkinter import ttk
import math
from managers.configini.config_reader import Config

app_constants = Config.get_instance()
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.styling.style import THEMES, DEFAULT_THEME
import os


class TrapezoidButtonCreatorMixin:
    """A mixin to create a dynamic, theme-aware trapezoidal button."""

    def _create_trapezoid_button(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        """Creates a trapezoidal button widget."""
        current_function_name = "_create_trapezoid_button"

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
                message=f"Creating trapezoid button: {label}", **_get_log_args()
            )

        frame = ttk.Frame(parent_widget)  # Use parent_widget here

        if label:
            ttk.Label(frame, text=label).pack(side=tk.TOP, pady=(0, 5))

        # --- Configuration ---
        width = config.get("width", 80)
        height = config.get("height", 50)
        base_color = config.get("color", "#8B0000")
        indicator_color = config.get("indicator_color", "#FF0000")  # Legacy/fallback
        led_color = config.get(
            "led_color", indicator_color
        )  # Use specific led_color, fallback to general indicator_color
        is_latching = config.get("latching", False)
        initial_state = config.get("value_default", False)

        # Theme Resolution
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        bg_color = colors.get("bg", "#2b2b2b")

        canvas = tk.Canvas(
            frame, width=width, height=height, bg=bg_color, highlightthickness=0
        )
        canvas.pack()

        # --- State Management ---
        state_var = tk.BooleanVar(value=initial_state)
        self._is_pressed = False

        def redraw_button():
            """Central function to redraw the button based on current state."""
            current_state = {
                "pressed": self._is_pressed,
                "lit": state_var.get(),
                "base_color": base_color,
                "led_color": led_color,
            }
            self._draw_trapezoid_button(canvas, config, current_state)

        def on_press(event):
            self._is_pressed = True
            if not is_latching:
                state_var.set(True)
            redraw_button()

        def on_release(event):
            self._is_pressed = False
            if is_latching:
                state_var.set(not state_var.get())
            else:
                state_var.set(False)
            redraw_button()

        canvas.bind("<Button-1>", on_press)
        canvas.bind("<ButtonRelease-1>", on_release)

        # --- MQTT and State Mirroring ---
        def on_state_change(*args):
            redraw_button()
            if self.state_mirror_engine:
                self.state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        state_var.trace_add("write", on_state_change)

        if path and self.state_mirror_engine:
            widget_id = path
            self.state_mirror_engine.register_widget(
                widget_id, state_var, base_mqtt_topic_from_path, config
            )

            # Subscribe to the topic for incoming messages
            from workers.mqtt.mqtt_topic_utils import get_topic

            topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, widget_id)
            self.subscriber_router.subscribe_to_topic(
                topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui
            )

            state_mirror_engine.initialize_widget_state(path)

        redraw_button()

        return frame

    def _draw_trapezoid_button(self, canvas, config, state):
        """Draws the button in its current state."""
        canvas.delete("all")

        width = config.get("width", 80)
        height = config.get("height", 50)

        base_color = state["base_color"]
        pressed = state["pressed"]
        lit = state["lit"]
        led_color = state["led_color"]

        # --- Dynamic Colors ---
        top_color = self._adjust_color(base_color, 1.5)
        side_color = self._adjust_color(base_color, 1.2)
        bottom_color = self._adjust_color(base_color, 0.6)
        face_color = base_color

        # --- Geometry (Narrow Top, Wide Bottom) ---
        slant = config.get("slant", 10)
        depth = 5 if not pressed else 2

        # Main face points
        p1 = (slant, depth)
        p2 = (width - slant, depth)
        p3 = (width, height - depth)
        p4 = (0, height - depth)

        # Top bevel points
        t1 = (slant, depth)
        t2 = (width - slant, depth)
        t3 = (width - slant, 0)
        t4 = (slant, 0)

        # Bottom bevel points
        b1 = (0, height - depth)
        b2 = (width, height - depth)
        b3 = (width, height)
        b4 = (0, height)

        # Draw bevels first
        canvas.create_polygon(b1, b2, b3, b4, fill=bottom_color, outline=bottom_color)
        canvas.create_polygon(t1, t2, t3, t4, fill=top_color, outline=top_color)

        # Draw main face
        canvas.create_polygon(p1, p2, p3, p4, fill=face_color, outline=face_color)

        # --- Indicator Light ---
        if lit:
            light_radius = config.get("light_radius", 5) * 1.2  # 20% larger
            light_x = width / 2
            light_y = depth + light_radius + 5

            # Glow effect
            canvas.create_oval(
                light_x - light_radius * 1.5,
                light_y - light_radius * 1.5,
                light_x + light_radius * 1.5,
                light_y + light_radius * 1.5,
                fill=led_color,
                outline="",
            )
            # Inner light
            canvas.create_oval(
                light_x - light_radius,
                light_y - light_radius,
                light_x + light_radius,
                light_y + light_radius,
                fill=self._adjust_color(led_color, 1.5),
                outline=self._adjust_color(led_color, 2.0),
            )

    def _adjust_color(self, hex_color, factor):
        """Lightens or darkens a hex color by a factor."""
        if not hex_color or len(hex_color) != 7:
            return "#000000"
        try:
            r, g, b = (
                int(hex_color[1:3], 16),
                int(hex_color[3:5], 16),
                int(hex_color[5:7], 16),
            )
            r = int(min(255, r * factor))
            g = int(min(255, g * factor))
            b = int(min(255, b * factor))
            return f"#{r:02x}{g:02x}{b:02x}"
        except (ValueError, TypeError):
            return "#000000"
