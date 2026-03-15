# button_trapezoid/button_trapezoid.py
#
# A mixin to create a dynamic, theme-aware trapezoidal button.
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

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from workers.styling.style import THEMES, DEFAULT_THEME
from managers.Display.transparency.transparency_mixin import TransparencyMixin
import os


class BuilderButtonTrapezoidCreator(TransparencyMixin):
    """A mixin to create a dynamic, theme-aware trapezoidal button."""

    # Creates a custom trapezoidal button widget.
    # This method sets up a Canvas-based button to ensure true transparency.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): The configuration for the button.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     tk.Canvas: The created button canvas.
    def make_button_trapezoid(
        self, parent_widget, config_data, context=None, **kwargs
    ):
        """Creates a trapezoidal button widget."""
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🔳 [BUILDER] Entering make_button_trapezoid")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        current_function_name = "make_button_trapezoid"

        # Extract only widget-specific config from config_data
        label = config_data.get("label_active") or config_data.get("label", "")
        button_text = config_data.get("button_text", "")
        if button_text:
            button_text = button_text[:3]
            config_data["button_text"] = button_text

        config = config_data  # config_data is the config
        path = config_data.get("path")

        # ⚡ HARDENED INTERFACE: Extract from context if available
        if BUILDER_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
            if BUILDER_DEBUG: builder_logger.debug("✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.")
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self
            if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to self/kwargs.")

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️🔳 [BUILDER] Spawning trapezoid button for '{label}' at path '{path}'.")

        # --- Configuration ---
        width = config.get("width", 80)
        height = config.get("height", 50)
        if BUILDER_DEBUG: builder_logger.debug(f"📐📏🔳 [DIM] Trapezoid Dimensions: {width}x{height}")
        
        # Robust Background Inheritance
        try:
            p_bg = parent_widget.cget("bg")
            if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
        except:
            p_bg = "#2b2b2b"

        base_color = config.get("color", "#8B0000")
        indicator_color = config.get("indicator_color", "#FF0000")
        led_color = config.get("led_color", indicator_color)
        is_latching = config.get("latching", False)
        initial_state = config.get("value_default", False)
        if BUILDER_DEBUG: builder_logger.debug(f"🎨🖌️🌈 [STYLE] Color: {base_color}, LED: {led_color}, Latching: {is_latching}")

        # Check if we were passed a canvas to use (e.g. from toggler)
        canvas = kwargs.get("canvas")
        if canvas is None:
            # Use tk.Canvas for transparency support
            if BUILDER_DEBUG: builder_logger.trace(f"🏗️🪟🖼️ [CONSTRUCT] Creating canvas for trapezoid '{label}'")
            canvas = tk.Canvas(
                parent_widget,
                bd=0,
                highlightthickness=0,
                relief="flat",
                width=width,
                height=height + (25 if label else 0),
                bg=p_bg
            )
            # Apply Industrial Transparency only if we created the canvas
            if hasattr(self, '_apply_transparency'):
                if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to trapezoid '{label}'")
                self._apply_transparency(canvas, canvas, config, builder_instance)

        # --- State Management ---
        state_var = kwargs.get("variable") or tk.BooleanVar(value=initial_state)
        self._is_pressed = False
        if BUILDER_DEBUG: builder_logger.debug(f"🔋🔘✨ [STATE] Initial state for '{label}': {initial_state}")

        def redraw_button(*args):
            """Central function to redraw the button based on current state."""
            # ⚡ SYNC: If we have a sampled patina color, use it as the face base color
            # if the config didn't specify a custom one.
            current_face = base_color
            sampled_bg = canvas.cget("bg")
            if base_color == p_bg and sampled_bg.startswith("#"):
                current_face = sampled_bg

            if BUILDER_DEBUG: builder_logger.trace(f"🔄✨🎨 [REDRAW] Redrawing trapezoid '{label}' (Lit: {state_var.get()}, Pressed: {self._is_pressed})")
            current_state = {
                "pressed": self._is_pressed,
                "lit": state_var.get(),
                "base_color": current_face,
                "led_color": led_color,
                "label": label if kwargs.get("canvas") is None else None # Hide label if inside a toggler
            }
            self._draw_trapezoid_button(canvas, config, current_state)

        def on_press(event):
            if BUILDER_DEBUG: builder_logger.info(f"🖱️👆🔳 [INPUT] Press detected on trapezoid '{label}'")
            self._is_pressed = True
            if not is_latching:
                state_var.set(True)
            redraw_button()

        def on_release(event):
            if BUILDER_DEBUG: builder_logger.info(f"🖱️🔙🔳 [INPUT] Release detected on trapezoid '{label}'")
            self._is_pressed = False
            if is_latching:
                state_var.set(not state_var.get())
            else:
                state_var.set(False)
            redraw_button()

        if BUILDER_DEBUG: builder_logger.trace(f"🖱️👆🔗 [EVENTS] Binding input protocols for trapezoid '{label}'")
        canvas.bind("<Button-1>", on_press)
        canvas.bind("<ButtonRelease-1>", on_release)
        canvas.bind("<Configure>", redraw_button, add="+")

        # --- MQTT and State Mirroring ---
        def on_state_change(*args):
            if BUILDER_DEBUG: builder_logger.debug(f"⚡🔴📡 [EVENT] State change for '{label}'. Syncing visuals and broadcasting.")
            redraw_button()
            if state_mirror_engine:
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        state_var.trace_add("write", on_state_change)

        if path and state_mirror_engine:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering trapezoid at path '{path}'")
            widget_id = path
            topic = state_mirror_engine.register_widget(
                widget_id, state_var, base_mqtt_topic_from_path, config
            )

            if subscriber_router and topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing to topic: {topic}")
                subscriber_router.subscribe_to_topic(
                    topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                )

            if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing widget state from cache/broker for '{path}'")
            state_mirror_engine.initialize_widget_state(path)

        # Add redraw hook for transparency reslicing
        canvas._draw = redraw_button
        canvas.render = redraw_button

        redraw_button()

        if BUILDER_DEBUG: builder_logger.success(f"✅🆗🔳 [SUCCESS] The trapezoid button '{label}' has materialized!")
        return canvas

    def _draw_trapezoid_button(self, canvas, config, state):
        """Draws the button in its current state."""
        # ⚡ INDUSTRIAL TRANSPARENCY: Don't delete everything, preserve the patina slice
        for item in canvas.find_all():
            tags = canvas.gettags(item)
            if "panel_bg_slice" not in tags:
                canvas.delete(item)

        # 0. Background Slice (Fallback if slice doesn't exist)
        if hasattr(canvas, 'panel_bg_image') and not canvas.find_withtag("panel_bg_slice"):
            canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")

        width = config.get("width", 80)
        button_h = config.get("height", 50)
        canvas_h = canvas.winfo_height()
        if canvas_h <= 1: canvas_h = button_h + (25 if state.get("label") else 0)

        label = state.get("label")
        top_reserve = 25 if label else 0
        
        # 0.1 Widget Label (Floating)
        if label:
            canvas.create_text(
                width/2, 10, text=label, fill="white",
                font=("Helvetica", 9, "bold"), anchor="n", tags="industrial_text"
            )

        base_color = state["base_color"]
        pressed = state["pressed"]
        lit = state["lit"]
        led_color = state["led_color"]

        # --- Dynamic Colors ---
        top_color = self._adjust_color(base_color, 1.5)
        bottom_color = self._adjust_color(base_color, 0.6)
        face_color = base_color

        # --- Geometry (Narrow Top, Wide Bottom) ---
        slant = config.get("slant", 10)
        depth = 5 if not pressed else 2
        
        y_off = top_reserve

        # Main face points
        p1 = (slant, y_off + depth)
        p2 = (width - slant, y_off + depth)
        p3 = (width, y_off + button_h - depth)
        p4 = (0, y_off + button_h - depth)

        # Top bevel points
        t1 = (slant, y_off + depth)
        t2 = (width - slant, y_off + depth)
        t3 = (width - slant, y_off)
        t4 = (slant, y_off)

        # Bottom bevel points
        b1 = (0, y_off + button_h - depth)
        b2 = (width, y_off + button_h - depth)
        b3 = (width, y_off + button_h)
        b4 = (0, y_off + button_h)

        # Draw bevels first
        canvas.create_polygon(b1, b2, b3, b4, fill=bottom_color, outline=bottom_color, tags="vu_element")
        canvas.create_polygon(t1, t2, t3, t4, fill=top_color, outline=top_color, tags="vu_element")

        # Draw main face
        canvas.create_polygon(p1, p2, p3, p4, fill=face_color, outline=face_color, tags="vu_element")

        # --- Indicator Light ---
        if lit:
            light_radius = config.get("light_radius", 5) * 1.2  # 20% larger
            light_x = width / 2
            light_y = y_off + depth + light_radius + 5

            # Glow effect
            canvas.create_oval(
                light_x - light_radius * 1.5,
                light_y - light_radius * 1.5,
                light_x + light_radius * 1.5,
                light_y + light_radius * 1.5,
                fill=led_color,
                outline="",
                tags="vu_element"
            )
            # Inner light
            canvas.create_oval(
                light_x - light_radius,
                light_y - light_radius,
                light_x + light_radius,
                light_y + light_radius,
                fill=self._adjust_color(led_color, 1.5),
                outline=self._adjust_color(led_color, 2.0),
                tags="vu_element"
            )

        # --- Button Text ---
        button_text = config.get("button_text", "")
        if button_text:
            text_x = width / 2
            # Calculate position based on light position or default
            light_radius = config.get("light_radius", 5) * 1.2
            light_y = y_off + depth + light_radius + 5
            text_y = light_y + light_radius + 8  # Position below light

            canvas.create_text(
                text_x,
                text_y,
                text=button_text,
                fill="white",  # Force white for better contrast on patina
                font=("Arial", 9, "bold"),
                anchor="center",
                tags="industrial_text"
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

