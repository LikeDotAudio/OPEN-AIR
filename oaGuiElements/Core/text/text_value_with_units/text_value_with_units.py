# text_value_with_units/text_value_with_units.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: text_value_with_units/dynamic_guimake_text_value_with_units.py

import tkinter as tk
from tkinter import ttk
import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from oaComMQTT.Methods.mqtt_topic_utils import get_topic  # Import get_topic
from oaStyle.Core.style import THEMES, DEFAULT_THEME
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin


class BuilderTextValueWithUnitsCreator(TransparencyMixin):
    # Creates a text input widget (Entry) that is synchronized via MQTT.
    # This method sets up a Tkinter Entry widget for text input, binds its value
    # to a StringVar, and integrates it with the state management engine.
    # Changes to the text input are broadcast via MQTT, and incoming MQTT messages
    # can update the text field.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the text input widget.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     tk.Canvas: The created canvas containing the text input widget, or None on failure.

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderTextValueWithUnitsCreator()
        return creator.make_text_value_with_units(parent_widget, config_data, context, **kwargs)

    def make_text_value_with_units(
        self, parent_widget, config_data, context=None, **kwargs
    ):  # Updated signature
        """Creates a text input widget."""
        current_function_name = "make_text_value_with_units"

        # Extract only widget-specific config from config_data
        label = config_data.get("label_active")
        config = config_data  # config_data is the config
        path = config_data.get("path")

        # ⚡ HARDENED INTERFACE: Extract from context if available
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self

        if LOCAL_DEBUG: logger.debug(f"🔬⚡️ Entering '{current_function_name}' to forge a text input field for '{label}'.")

        # Robust Background Inheritance
        try:
            p_bg = parent_widget.cget("bg")
            if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
        except:
            p_bg = "#2b2b2b"

        # Use tk.Canvas for transparency support
        canvas = tk.Canvas(
            parent_widget,
            bd=0,
            highlightthickness=0,
            relief="flat",
            height=30,
            bg=p_bg
        )
        
        # Apply Industrial Transparency
        if hasattr(self, '_apply_transparency'):
            self._apply_transparency(canvas, canvas, config, builder_instance)

        try:
            # Check both 'layout' and 'geometry' for configuration
            layout_config = config.get("layout", {})
            geom_config = config.get("geometry", {})
            
            font_size = layout_config.get("font", geom_config.get("font", 13))
            custom_font = ("Segoe UI", font_size)
            
            # Extract color with fallback to None if it's an empty string
            custom_colour = layout_config.get("colour", geom_config.get("colour", None))
            if custom_colour == "": custom_colour = None

            text_var = tk.StringVar()
            text_var.set(config.get("value_default", ""))

            # Create a style for the entry
            clean_path = path.replace('/', '_') if path else "default"
            style_name = f"TextValue.{clean_path}.TEntry"
            style = ttk.Style()
            
            # Default to black text, override if custom_colour is provided
            text_color = "black"
            if custom_colour:
                text_color = custom_colour
                
            style.configure(style_name, fieldbackground="#2b2b2b", foreground=text_color)

            entry = ttk.Entry(canvas, textvariable=text_var, font=custom_font, style=style_name)
            # Add left padding if there is a label to avoid overlap
            padx_left = 100 if label else 10
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(padx_left, 10))

            def redraw_input_labels(*args):
                if not canvas.winfo_exists(): return
                canvas.delete("industrial_text")
                w = canvas.winfo_width()
                h = canvas.winfo_height()
                if w <= 1: return
                
                # Draw Main Label (Left)
                if label:
                    canvas.create_text(
                        10, h/2, text=f"{label}:", anchor="w",
                        fill=custom_colour or "white", font=custom_font,
                        tags="industrial_text"
                    )

            def sync_bg():
                if not canvas.winfo_exists(): return
                bg = canvas.cget("bg")
                # ⚡ HIGH-FIDELITY: Update the style's fieldbackground to match the sampled patina
                style.configure(style_name, fieldbackground=bg)
                redraw_input_labels()
            
            canvas._draw = sync_bg
            canvas.render = sync_bg
            canvas.bind("<Configure>", redraw_input_labels, add="+")

            def _on_text_change(*args):
                try:
                    if LOCAL_DEBUG: logger.debug(f"Text changed for {label}: {text_var.get()}")
                    state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                except Exception as e:
                    if LOCAL_DEBUG:
                        logger.debug(f"🔴 ERROR in _on_text_change: {e}",
                            file=os.path.basename(__file__),
                        )

            text_var.trace_add(
                "write", _on_text_change
            )  # Use trace_add for consistency

            if path:
                widget_id = path
                topic = state_mirror_engine.register_widget(
                    widget_id, text_var, base_mqtt_topic_from_path, config
                )

                # Subscribe to this widget's topic to receive updates
                if subscriber_router and topic:
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )

                if LOCAL_DEBUG: logger.debug(f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine (StringVar: {text_var.get()}).")
                # Initialize state from cache or broadcast
                state_mirror_engine.initialize_widget_state(path)

            if LOCAL_DEBUG: logger.success(f"✅ SUCCESS! The text input '{label}' has been successfully forged!",
                file=os.path.basename(__file__),
                version=app_constants.CURRENT_VERSION,
                function=f"{self.__class__.__name__}.{current_function_name}",
            )
            return canvas
        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("❌ The text input '{label}' has disintegrated! Error",
                    file=os.path.basename(__file__),
                    version=app_constants.CURRENT_VERSION,
                    function=current_function_name,
                )
            return None

