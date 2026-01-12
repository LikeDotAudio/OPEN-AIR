# builder_text/dynamic_gui_create_text_input.py
#
# A mixin for creating a text input widget that is synchronized via MQTT.
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
from managers.configini.config_reader import Config
from workers.mqtt.mqtt_topic_utils import get_topic  # Import get_topic
from workers.styling.style import THEMES, DEFAULT_THEME

app_constants = Config.get_instance()  # Get the singleton instance
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
import os


class TextInputCreatorMixin:
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
    #     ttk.Frame: The created frame containing the text input widget, or None on failure.
    def _create_text_input(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        """Creates a text input widget."""
        current_function_name = "_create_text_input"

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
                message=f"🔬⚡️ Entering '{current_function_name}' to forge a text input field for '{label}'.",
                **_get_log_args(),
            )

        frame = ttk.Frame(parent_widget)  # Use parent_widget here

        try:
            layout_config = config.get("layout", {})
            font_size = layout_config.get("font", 13)
            custom_font = ("Segoe UI", font_size)
            custom_colour = layout_config.get("colour", None)

            if label:
                lbl = ttk.Label(frame, text=label, font=custom_font)
                if custom_colour:
                    lbl.configure(foreground=custom_colour)
                lbl.pack(side=tk.LEFT, padx=(0, 10))

            text_var = tk.StringVar()
            text_var.set(config.get("value_default", ""))

            # Create a style for the entry with light grey background and black text
            clean_path = path.replace('/', '_') if path else "default"
            style_name = f"LightGrey.{clean_path}.TEntry"
            style = ttk.Style()
            
            # Default to black text, override if custom_colour is provided
            text_color = "black"
            if custom_colour:
                text_color = custom_colour
                
            style.configure(style_name, fieldbackground="#bcbcbc", foreground=text_color)

            entry = ttk.Entry(frame, textvariable=text_var, font=custom_font, style=style_name)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            def _on_text_change(*args):
                try:
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"Text changed for {label}: {text_var.get()}",
                            file=os.path.basename(__file__),
                            function="_on_text_change",
                        )
                    state_mirror_engine.broadcast_gui_change_to_mqtt(path)
                except Exception as e:
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"🔴 ERROR in _on_text_change: {e}",
                            file=os.path.basename(__file__),
                            function="_on_text_change",
                        )

            text_var.trace_add(
                "write", _on_text_change
            )  # Use trace_add for consistency

            if path:
                widget_id = path
                state_mirror_engine.register_widget(
                    widget_id, text_var, base_mqtt_topic_from_path, config
                )

                # Subscribe to this widget's topic to receive updates
                topic = get_topic(
                    self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, widget_id
                )
                self.subscriber_router.subscribe_to_topic(
                    topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui
                )

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🔬 Widget '{label}' ({path}) registered with StateMirrorEngine (StringVar: {text_var.get()}).",
                        **_get_log_args(),
                    )
                # Initialize state from cache or broadcast
                state_mirror_engine.initialize_widget_state(path)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ SUCCESS! The text input '{label}' has been successfully forged!",
                    file=os.path.basename(__file__),
                    version=app_constants.CURRENT_VERSION,
                    function=f"{self.__class__.__name__}.{current_function_name}",
                )
            return frame
        except Exception as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌ The text input '{label}' has disintegrated! Error: {e}",
                    file=os.path.basename(__file__),
                    version=app_constants.CURRENT_VERSION,
                    function=current_function_name,
                )
            return None