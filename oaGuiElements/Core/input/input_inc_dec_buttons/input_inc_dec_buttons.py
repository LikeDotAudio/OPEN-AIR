# input_inc_dec_buttons/input_inc_dec_buttons.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: input_inc_dec_buttons/dynamic_guimake_input_inc_dec_buttons.py

import tkinter as tk
from tkinter import ttk

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = False    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin


class BuilderInputIncDecButtonsCreator(TransparencyMixin):
    # Creates a set of increment and decrement buttons along with a display for their current value.
    # This method sets up two buttons (up/down arrows) that, when pressed, modify a numerical
    # value. The current value is displayed, and the entire widget is synchronized via MQTT.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the increment/decrement buttons.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     tk.Frame: The created frame containing the increment/decrement buttons and value display.
        def make_input_inc_dec_buttons(
            self, parent_widget, config_data, context=None, **kwargs
        ):  # Updated signature
            """Creates increment/decrement buttons."""
            if BUILDER_DEBUG: 
                builder_logger.trace(f"🔬🏗️🕹️ [BUILDER] Entering make_input_inc_dec_buttons")
                builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")
    
            current_function_name = "make_input_inc_dec_buttons"
    
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
    
            if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️🕹️ [BUILDER] Forging inc/dec buttons for '{label}' at path '{path}'.")
    
            frame = tk.Frame(parent_widget)  # Use parent_widget here
            
            # Apply Industrial Transparency
            if hasattr(self, '_apply_transparency'):
                if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to inc/dec frame.")
                self._apply_transparency(frame, None, config_data, builder_instance)
    
            if label:
                tk.Label(frame, text=label, fg="white").pack(side=tk.LEFT, padx=(0, 10))
    
            # Initial value and range (optional, can be used for boundary checks)
            value_default = config.get("value_default", 0)
            increment_amount = config.get("increment", 1)
            if BUILDER_DEBUG: builder_logger.debug(f"📐📏✨ [STATE] Default value: {value_default}, Step: {increment_amount}")
    
            current_value = tk.IntVar(value=value_default)
    
            value_display = tk.Label(frame, textvariable=current_value, fg="white")
            value_display.pack(side=tk.RIGHT, padx=(10, 0))
            
            def sync_bg():
                if BUILDER_DEBUG: builder_logger.trace(f"🔄👻🎨 [SYNC] Syncing labels to background for inc/dec frame.")
                bg = frame.cget("bg")
                for child in frame.winfo_children():
                    if isinstance(child, tk.Label):
                        child.config(bg=bg)
            
            frame._draw = sync_bg
    
            def _increment():
                new_val = current_value.get() + increment_amount
                if BUILDER_DEBUG: builder_logger.info(f"🖱️👆🆙 [INPUT] Increment clicked for '{label}'. New: {new_val}")
                current_value.set(new_val)
    
            def _decrement():
                new_val = current_value.get() - increment_amount
                if BUILDER_DEBUG: builder_logger.info(f"🖱️👆⬇️ [INPUT] Decrement clicked for '{label}'. New: {new_val}")
                current_value.set(new_val)
    
            if BUILDER_DEBUG: builder_logger.trace(f"🏗️🔳🕹️ [CONSTRUCT] Instantiating inc/dec ttk.Buttons.")
            dec_button = ttk.Button(frame, text="⬇", command=_decrement)
            dec_button.pack(side=tk.RIGHT)
    
            inc_button = ttk.Button(frame, text="⬆", command=_increment)
            inc_button.pack(side=tk.RIGHT, padx=(5, 0))
    
            # --- New MQTT Wiring for Inc/Dec Buttons ---
            if path:  # state_mirror_engine and subscriber_router are now explicitly passed
                if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering inc/dec buttons at path '{path}'")
                widget_id = path
    
                # 1. Register widget
                topic = state_mirror_engine.register_widget(
                    widget_id, current_value, base_mqtt_topic_from_path, config
                )
    
                # 2. Subscribe to this widget's topic to receive updates
                if subscriber_router and topic:
                    if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing to topic: {topic}")
                    subscriber_router.subscribe_to_topic(
                        topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                    )
    
                # 3. Bind variable trace for outgoing messages
                # Use a lambda that calls broadcast_gui_change_to_mqtt
                def on_gui_change(*args):
                    if BUILDER_DEBUG: builder_logger.debug(f"⚡🔴📡 [EVENT] Value change for inc/dec '{label}'. Broadcasting.")
                    state_mirror_engine.broadcast_gui_change_to_mqtt(widget_id)
                
                current_value.trace_add("write", on_gui_change)
    
                # 4. Initialize state from cache or broadcast
                if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing state from cache/broker.")
                state_mirror_engine.initialize_widget_state(widget_id)
    
            if BUILDER_DEBUG: builder_logger.success(f"✅🆗🕹️ [SUCCESS] The increment/decrement buttons for '{label}' has materialized!")
            return frame
    
