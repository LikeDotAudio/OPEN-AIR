# button_actuator/button_actuator.py
#
# This file provides the BuilderButtonActuatorCreator class for creating photorealistic
# actuator buttons in the GUI using the shared CanvasButton base.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260208.2345

import os
import tkinter as tk
from tkinter import ttk
import inspect
import orjson
import time
from workers.Command_Router.mqtt.mqtt_message import MqttMessage

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from workers.Command_Router.mqtt.mqtt_publisher_service import publish_payload
from managers.Display.factory.button_canvas_base import CanvasButton
from managers.Display.transparency.transparency_mixin import TransparencyMixin
from workers.Command_Router.mqtt.mqtt_topic_utils import get_topic

# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2
TOPIC_DELIMITER = "/"

class BuilderButtonActuatorCreator(TransparencyMixin):
    """
    A mixin class that provides the functionality for creating photorealistic
    actuator buttons that trigger actions via MQTT.
    """

    def make_button_actuator(self, parent_widget, config_data, context=None, **kwargs):
        """Creates a photorealistic CanvasButton that acts as a momentary actuator."""
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🔘 [BUILDER] Entering make_button_actuator")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        current_function_name = inspect.currentframe().f_code.co_name

        label = config_data.get("label", "Actuator")
        text_active = config_data.get("label_active", label)
        text_inactive = config_data.get("label_inactive", label)
        
        config = config_data
        path = config_data.get("path")

        # ⚡ HARDENED INTERFACE: Extract from context if available
        if BUILDER_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            app_instance = context.app_instance
            builder_instance = context.builder_instance or app_instance
            if BUILDER_DEBUG: builder_logger.debug("✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.")
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self
            app_instance = kwargs.get("app_instance")
            if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to self/kwargs.")

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️🔘 [BUILDER] Spawning button actuator for '{label}' at path '{path}'.")

        try:
            # Layout configuration
            if BUILDER_DEBUG: builder_logger.trace("📐📏🔳 [LAYOUT] Calculating dimensions and geometry...")
            layout = config.get("layout", {})
            btn_h = config.get("height", layout.get("height", 50))
            btn_w = config.get("width", layout.get("width", 100))
            font_size = layout.get("font", 10)
            corner_r = layout.get("corner_radius", 6)
            alpha = float(config.get("alpha", layout.get("alpha", 1.0)))
            if BUILDER_DEBUG: builder_logger.debug(f"📏📐🔲 [DIM] Dimensions: {btn_w}x{btn_h}, Radius: {corner_r}, Alpha: {alpha}")

            # Colors
            if BUILDER_DEBUG: builder_logger.trace("🎨🖌️🌈 [COLOR] Resolving industrial color palette...")
            c_act = config.get("active_color", "#FF9900")
            c_inact = config.get("bg_color", "#1a1a1a")
            c_act_bg = config.get("active_bg_color", "#000000")
            t_act = config.get("active_text_color", "#1a1a1a")
            t_inact = config.get("text_color", "#888888")
            
            glow_int = config.get("glow_intensity", 1.0)
            f_on_style = config.get("active_font_style", "bold")
            f_on_size = config.get("active_font_size")
            f_off_style = config.get("inactive_font_style", "normal")
            f_off_size = config.get("inactive_font_size")
            if BUILDER_DEBUG: 
                builder_logger.debug(f"🌈🎨✨ [COLOR] Active: {c_act}, Inactive: {c_inact}, Glow: {glow_int}")
                builder_logger.debug(f"🖋️🔤🔡 [FONT] ON: {f_on_style}/{f_on_size}, OFF: {f_off_style}/{f_off_size}")

            # Create the CanvasButton
            if BUILDER_DEBUG: builder_logger.trace("🏗️🔳🔘 [CONSTRUCT] Instantiating CanvasButton core...")
            button = CanvasButton(
                parent_widget, text=text_inactive, command=None, # Handling clicks manually for momentary action
                width=btn_w, height=btn_h, corner_radius=corner_r,
                bg_color=c_inact, active_color=c_act, active_bg_color=c_act_bg,
                text_color=t_inact, active_text_color=t_act,
                glow_intensity=glow_int,
                active_font_style=f_on_style, active_font_size=f_on_size,
                inactive_font_style=f_off_style if f_off_style else "normal",
                inactive_font_size=f_off_size,
                alpha=alpha, font=("TkDefaultFont", font_size),
                transparency_applicator=builder_instance._apply_transparency if hasattr(builder_instance, '_apply_transparency') else None,
                config=config, builder=builder_instance
            )
            
            # --- Layout Application (Grid) ---
            if "row" in layout and "column" in layout:
                if BUILDER_DEBUG: builder_logger.debug(f"📐🔳🔗 [LAYOUT] Applying grid coordinates: R{layout['row']} C{layout['column']}")
                button.grid(
                    row=layout["row"], 
                    column=layout["column"], 
                    columnspan=layout.get("col_span", 1),
                    rowspan=layout.get("row_span", 1),
                    padx=layout.get("padx", DEFAULT_PAD_X),
                    pady=layout.get("pady", DEFAULT_PAD_Y),
                    sticky=layout.get("sticky", "")
                )

            # Store states for dynamic text updates
            button._text_active = text_active
            button._text_inactive = text_inactive

            def on_press(event):
                if BUILDER_DEBUG: builder_logger.info(f"🖱️👆🔘 [INPUT] Press detected on actuator '{label}'")
                # 1. Local Feedback
                button.set_active(True)
                button.set_text(button._text_active)
                
                # Maintenance Command Handling
                scpi_msg = str(config.get("message", config.get("value", config.get("domain", {}).get("value", ""))))
                is_maint = (
                    scpi_msg.startswith("*") or 
                    "SYSTem" in scpi_msg.upper() or 
                    scpi_msg.startswith("sudo ") or 
                    scpi_msg.startswith("pkill ")
                )
                
                if is_maint:
                    if BUILDER_DEBUG: builder_logger.debug(f"📋⌨️✨ [MAINT] Maintenance command detected. Copying to clipboard: {scpi_msg}")
                    try:
                        parent_widget.clipboard_clear()
                        parent_widget.clipboard_append(scpi_msg)
                        button.set_text("PASTE copied text into terminal")
                        parent_widget.after(3000, lambda: button.set_text(button._text_inactive))
                    except Exception as e:
                        builder_logger.error(f"❌ Clipboard error: {e}")
                    return 
                
                # 2. Network Action
                if state_mirror_engine:
                    topic = state_mirror_engine.calculate_topic(f"{path}/trigger", base_mqtt_topic_from_path)
                    payload = orjson.dumps({"val": True, "ts": time.time()})
                    if BUILDER_DEBUG: builder_logger.trace(f"📡🔴📡 [MQTT] Publishing momentary ON trigger to: {topic}")
                    state_mirror_engine.publish_command(topic, payload)

            def on_release(event):
                if BUILDER_DEBUG: builder_logger.info(f"🖱️🔙🔘 [INPUT] Release detected on actuator '{label}'")
                # 1. Local Feedback
                button.set_active(False)
                if button.text != "PASTE copied text into terminal":
                    button.set_text(button._text_inactive)

                # Skip release MQTT for maintenance
                scpi_msg = str(config.get("message", config.get("value", config.get("domain", {}).get("value", ""))))
                if (
                    scpi_msg.startswith("*") or 
                    "SYSTem" in scpi_msg.upper() or
                    scpi_msg.startswith("sudo ") or 
                    scpi_msg.startswith("pkill ")
                ):
                    return

                # 2. Network Action
                if state_mirror_engine:
                    topic = state_mirror_engine.calculate_topic(f"{path}/trigger", base_mqtt_topic_from_path)
                    payload = orjson.dumps({"val": False, "ts": time.time()})
                    if BUILDER_DEBUG: builder_logger.trace(f"📡🔴📡 [MQTT] Publishing momentary OFF trigger to: {topic}")
                    state_mirror_engine.publish_command(topic, payload)

            if BUILDER_DEBUG: builder_logger.trace(f"🖱️👆🔗 [EVENTS] Binding input protocols for actuator '{label}'")
            button.bind("<ButtonPress-1>", on_press, add="+")
            button.bind("<ButtonRelease-1>", on_release, add="+")

            if path:
                if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering actuator at path '{path}'")
                self.topic_widgets[path] = button
                
                if state_mirror_engine:
                    status_topic = state_mirror_engine.calculate_topic(f"{path}/active", base_mqtt_topic_from_path)
                    if subscriber_router:
                        if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing to feedback topic: {status_topic}")
                        subscriber_router.subscribe_to_topic(status_topic, self._on_actuator_state_update)

                    def _cleanup(event):
                        if event.widget == str(button):
                            if BUILDER_DEBUG: builder_logger.trace(f"❌🧹📡 [CLEANUP] Unsubscribing and removing actuator '{label}'")
                            if subscriber_router:
                                subscriber_router.unsubscribe_from_topic(status_topic, self._on_actuator_state_update)
                            if path in self.topic_widgets: del self.topic_widgets[path]

                    button.bind("<Destroy>", _cleanup, add="+")

            if BUILDER_DEBUG: builder_logger.success(f"✅🆗🔘 [SUCCESS] The actuator button '{label}' has materialized!")
            return button

        except Exception as e:
            if BUILDER_DEBUG:
                builder_logger.exception(f"❌🚫🛑 [ERROR] Critical failure creating button actuator '{label}'")
            return None

    def _on_actuator_state_update(self, msg: MqttMessage):
        """Syncs the button's visual state with remote MQTT triggers."""
        try:
            topic = msg.topic
            payload = msg.payload
            
            if BUILDER_DEBUG: builder_logger.trace(f"📥📶🔄 [MQTT] Incoming actuator state update on topic: {topic}")

            if isinstance(payload, (bytes, str)):
                data = orjson.loads(payload)
            else:
                data = payload
                
            is_active = data.get("val")
            if BUILDER_DEBUG: builder_logger.debug(f"🔋🔄✨ [STATE] Actuator state update parsed: {is_active}")

            # Match widget in registry
            # We need to find the widget instance by its path
            # Since we don't have a direct map from topic to widget here, 
            # we'll look at all topic_widgets
            for p, button in self.topic_widgets.items():
                # Reconstruct expected status topic for this path
                # Use engine if available
                if hasattr(self, "state_mirror_engine") and self.state_mirror_engine:
                    expected_topic = self.state_mirror_engine.calculate_topic(f"{p}/active", self.base_mqtt_topic_from_path)
                    if expected_topic == topic:
                        if BUILDER_DEBUG: builder_logger.trace(f"✨🔄🎨 [SYNC] Updating actuator '{p}' visual state to: {is_active}")
                        button.set_active(is_active)
                        button.set_text(button._text_active if is_active else button._text_inactive)
                        break
        except Exception as e:
            if BUILDER_DEBUG:
                builder_logger.exception(f"❌🚫🛑 [ERROR] Critical failure in actuator MQTT update for topic '{topic}'")
