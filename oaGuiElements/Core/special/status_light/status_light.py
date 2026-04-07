# status_light/status_light.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.4
#
# Description: Adds a status indicator circle to the GUI.

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from tkinter import ttk
import orjson

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaComProtocols.oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaComProtocols.oaComMQTT.Core.mqtt_message import MqttMessage

class StatusLightWidget(tk.Frame):
    """
    A standalone status light widget that manages its own UI and MQTT subscription.
    """
    def __init__(self, parent, config, state_mirror_engine, subscriber_router, base_topic_path):
        # Use theme-compatible background
        super().__init__(parent, bd=0, highlightthickness=0, relief="flat")
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️🔴 [BUILDER] Initializing StatusLightWidget", level="TRACE")
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📜📑💻 [CONFIG] Raw config received: {config}", level="DEBUG")

        self.widget_config = config
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = subscriber_router
        self.base_topic_path = base_topic_path
        
        # 1. Orientation Logic
        self.orientation = config.get("Orientation", "horizontal").lower()
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📐📏🔳 [LAYOUT] Orientation: {self.orientation}", level="DEBUG")
        
        # 3. Canvas for the Label and Dot
        # Increase size to fit label if needed
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🏗️🪟🎨 [CONSTRUCT] Creating status light canvas.", level="TRACE")
        self.status_canvas = tk.Canvas(
            self, width=120, height=30, highlightthickness=0, bd=0, relief="flat"
        )
        self.status_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Draw the initial circle (Gray or Red)
        # Coordinates will be updated in _draw
        self.status_light_id = self.status_canvas.create_oval(
            0, 0, 1, 1, fill="red", outline="white"
        )

        # 4. Subscribe to MQTT
        if self.state_mirror_engine and self.subscriber_router:
            # Global topic
            global_topic = "OPEN-AIR/GUI/Global/Header/StatusLight"
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📡📶🔄 [MQTT] Subscribing to GLOBAL status topic: {global_topic}", level="TRACE")
            self.subscriber_router.subscribe_to_topic(
                global_topic, self._update_status_light
            )
            
            # Instance-specific topic if path is provided
            widget_path = config.get("path")
            if widget_path:
                topic = self.state_mirror_engine.calculate_topic(widget_path, self.base_topic_path)
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📡📶🔄 [MQTT] Subscribing to INSTANCE status topic: {topic}", level="TRACE")
                self.subscriber_router.subscribe_to_topic(topic, self._update_status_light)

    def _update_status_light(self, msg: MqttMessage):
        """Callback function to update the status light's color based on MQTT messages."""
        try:
            topic = msg.topic
            payload = msg.payload
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📥📶🔄 [MQTT] Incoming status light update on: {topic}", level="TRACE")

            if isinstance(payload, bytes):
                data = orjson.loads(payload)
            elif isinstance(payload, str):
                data = orjson.loads(payload)
            else:
                data = payload

            # Support both 'color' and 'val' keys for status
            color_val = data.get("color", data.get("val", "red"))
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔋🔄✨ [STATE] Status light color command: {color_val}", level="DEBUG")

            # Determine final hex color
            if color_val in ["green", True, 1, "1", "online"]:
                fill_color = "#00ff00"
            elif color_val in ["yellow", "warning"]:
                fill_color = "#ffff00"
            else:
                fill_color = "#ff0000"

            # Schedule the GUI update on the main Tkinter thread
            def update_gui():
                if self.status_canvas.winfo_exists():
                    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"✨🔄🎨 [SYNC] Updating status light dot to color: {fill_color}", level="TRACE")
                    self.status_canvas.itemconfig(self.status_light_id, fill=fill_color)

            if self.state_mirror_engine and self.state_mirror_engine.root:
                self.state_mirror_engine.root.after(0, update_gui)
            else:
                update_gui()

        except Exception as e:
            builder_logger.exception(f"❌🚫🛑 [ERROR] failure updating status light for topic '{topic}'")
            pass

    def _draw(self):
        """Transparency hook."""
        if not self.status_canvas.winfo_exists(): return
        
        w = self.status_canvas.winfo_width()
        h = self.status_canvas.winfo_height()
        if w <= 1: return

        self.status_canvas.delete("bg")
        if hasattr(self.status_canvas, 'panel_bg_image') and self.status_canvas.panel_bg_image:
            self.status_canvas.create_image(0, 0, image=self.status_canvas.panel_bg_image, anchor="nw", tags="bg")
            self.status_canvas.tag_lower("bg")
        
        self.status_canvas.delete("industrial_text")
        
        label_text = self.widget_get_text(config.get("label_active"), "Fleet Status:")
        
        dot_size = 16
        if self.orientation == "vertical":
            # Label on top, dot below
            if label_text:
                self.status_canvas.create_text(
                    w/2, 5, text=label_text, fill="white", font=("Helvetica", 9, "bold"),
                    anchor="n", tags="industrial_text"
                )
            # Center dot below text
            cx, cy = w/2, h - dot_size/2 - 5
            self.status_canvas.coords(self.status_light_id, cx - dot_size/2, cy - dot_size/2, cx + dot_size/2, cy + dot_size/2)
        else:
            # Dot on left, label on right (Horizontal)
            if label_text:
                self.status_canvas.create_text(
                    30, h/2, text=label_text, fill="white", font=("Helvetica", 9),
                    anchor="w", tags="industrial_text"
                )
            # Dot on far left
            cx, cy = 15, h/2
            self.status_canvas.coords(self.status_light_id, cx - dot_size/2, cy - dot_size/2, cx + dot_size/2, cy + dot_size/2)


class HeaderStatusLightMixin(TransparencyMixin):
    """
    Adds a status indicator circle to the GUI.
    """

    def _build_header_status_light(self, parent_widget, config_data, context=None):
        # Create the Status Light Widget
        status_widget = StatusLightWidget(
            parent_widget, 
            config_data, 
            self.state_mirror_engine, 
            self.subscriber_router,
            self.base_mqtt_topic_from_path
        )
        
        # Register for transparency slicing
        if hasattr(self, '_apply_transparency'):
             self._apply_transparency(status_widget, status_widget.status_canvas, config_data, self)

        return status_widget