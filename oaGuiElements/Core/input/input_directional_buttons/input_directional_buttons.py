# input_directional_buttons/dynamic_guimake_input_directional_buttons.py
#
# A mixin for creating a set of directional buttons (up, down, left, right) that publish MQTT commands.
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
import os
import orjson
import time

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin


class BuilderInputDirectionalButtonsCreator(TransparencyMixin):
    # Creates a set of directional buttons (up, down, left, right) and binds them to MQTT commands.
    # This method arranges four buttons in a cross pattern and configures each button
    # to publish a specific MQTT command when pressed, allowing for remote control of movement.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the directional buttons.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     tk.Frame: The created frame containing the directional buttons.
        def make_input_directional_buttons(
            self, parent_widget, config_data, context=None, **kwargs
        ):  # Updated signature
            """Creates a set of directional buttons (up, down, left, right)."""
            if BUILDER_DEBUG: 
                builder_logger.trace(f"🔬🏗️🕹️ [BUILDER] Entering make_input_directional_buttons")
                builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")
    
            current_function_name = "make_input_directional_buttons"
    
            # Extract only widget-specific config from config_data
            label = config_data.get("label_active")
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
    
            if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️🕹️ [BUILDER] Spawning directional buttons for '{label}' at path '{path}'.")
    
            frame = tk.Frame(parent_widget)  # Use parent_widget here
            
            # Apply Industrial Transparency
            if hasattr(self, '_apply_transparency'):
                if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to directional frame.")
                self._apply_transparency(frame, None, config_data, builder_instance)
    
            if label:
                tk.Label(frame, text=label, fg="white").grid(row=0, column=1, pady=(0, 5))
    
            def sync_bg():
                if BUILDER_DEBUG: builder_logger.trace(f"🔄👻🎨 [SYNC] Syncing labels to background for directional frame.")
                bg = frame.cget("bg")
                for child in frame.winfo_children():
                    if isinstance(child, tk.Label):
                        child.config(bg=bg)
            
            frame._draw = sync_bg
    
            # Create buttons
            if BUILDER_DEBUG: builder_logger.trace(f"🏗️🔳🕹️ [CONSTRUCT] Instantiating directional ttk.Buttons.")
            up_button = ttk.Button(frame, text="⬆")
            down_button = ttk.Button(frame, text="⬇")
            left_button = ttk.Button(frame, text="⬅")
            right_button = ttk.Button(frame, text="➡")
    
            up_button.grid(row=1, column=1)
            left_button.grid(row=2, column=0)
            right_button.grid(row=2, column=2)
            down_button.grid(row=3, column=1)
    
            # Commands (these would typically publish MQTT messages)
            def _publish_command(action):
                action_path = f"{path}/{action}"
                topic = get_topic(
                    self.state_mirror_engine.base_topic, base_mqtt_topic_from_path, action_path
                )
                payload_data = {
                    "val": True,
                    "src": "gui",
                    "ts": time.time(),
                    "GUID": self.state_mirror_engine.GUID,
                }
                if BUILDER_DEBUG: builder_logger.debug(f"📡🔴📡 [MQTT] Publishing directional command '{action}' to topic: {topic}")
                self.state_mirror_engine.publish_command(topic, orjson.dumps(payload_data).decode())
    
            def _move_up():
                if BUILDER_DEBUG: builder_logger.info(f"🖱️👆⬆️ [INPUT] User clicked UP for '{path}'")
                _publish_command("up")
    
            def _move_down():
                if BUILDER_DEBUG: builder_logger.info(f"🖱️👆⬇️ [INPUT] User clicked DOWN for '{path}'")
                _publish_command("down")
    
            def _move_left():
                if BUILDER_DEBUG: builder_logger.info(f"🖱️👆⬅️ [INPUT] User clicked LEFT for '{path}'")
                _publish_command("left")
    
            def _move_right():
                if BUILDER_DEBUG: builder_logger.info(f"🖱️👆➡ [INPUT] User clicked RIGHT for '{path}'")
                _publish_command("right")
    
            if BUILDER_DEBUG: builder_logger.trace("🖱️👆🔗 [EVENTS] Binding command logic to directional buttons.")
            up_button.config(command=_move_up)
            down_button.config(command=_move_down)
            left_button.config(command=_move_left)
            right_button.config(command=_move_right)
    
            if BUILDER_DEBUG: builder_logger.success(f"✅🆗🕹️ [SUCCESS] The directional buttons for '{label}' has materialized!")
            return frame
    