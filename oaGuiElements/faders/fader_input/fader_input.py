# fader_input/fader_input.py
#
# A simple entry field that syncs with a DoubleVar (used by faders/knobs for numerical display).
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20250821.200641.1

import tkinter as tk
from tkinter import ttk

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfiguration.config_reader import Config

app_constants = Config.get_instance()

from oaComMQTT.mqtt_topic_utils import get_topic
from oaOchestration.widget_event_binder import bind_variable_trace
from oaGuiManager.transparency.transparency_mixin import TransparencyMixin


class BuilderFaderInputCreator(TransparencyMixin):
    """Mixin for creating a simple entry field synced with a DoubleVar."""

    def make_fader_input(self, parent_widget, config_data, context=None, **kwargs):
        """Creates a simple text entry widget synced with a DoubleVar."""
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️📝 [BUILDER] Entering make_fader_input")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        label = config_data.get("label_active")
        path = config_data.get("path")
        variable = kwargs.get("variable")
        
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

        if not variable:
            if BUILDER_DEBUG: builder_logger.trace("🔋🔢✨ [STATE] No variable provided, creating new DoubleVar.")
            variable = tk.DoubleVar()

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️📝 [BUILDER] Spawning fader input field for '{label}' at path '{path}'.")

        frame = tk.Frame(parent_widget)

        if hasattr(self, '_apply_transparency'):
            if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to input frame '{label}'")
            self._apply_transparency(frame, None, config_data, builder_instance)

        if label:
            tk.Label(frame, text=label, fg="#dcdcdc", font=("Helvetica", 10)).pack(side=tk.TOP)

        entry = tk.Entry(frame, textvariable=variable, width=10, justify="center", bg="#1a1a1a", fg="#ffffff", insertbackground="white", bd=0, highlightthickness=1, highlightbackground="#444444")
        entry.pack(side=tk.TOP, pady=5)

        if path:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering fader input at path '{path}'")
            topic = state_mirror_engine.register_widget(path, variable, base_mqtt_topic_from_path, config_data)
            
            def on_gui_change():
                if BUILDER_DEBUG: builder_logger.debug(f"⚡🔴📡 [EVENT] Input change for '{label}'. Broadcasting to MQTT.")
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)
            
            bind_variable_trace(variable, on_gui_change)
            
            if subscriber_router and topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing to topic: {topic}")
                subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
            
            if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing state from cache/broker for '{path}'")
            state_mirror_engine.initialize_widget_state(path)

        if BUILDER_DEBUG: builder_logger.success(f"✅🆗📝 [SUCCESS] The fader input '{label}' has materialized!")
        return frame
