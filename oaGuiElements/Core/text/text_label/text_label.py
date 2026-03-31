# text_label/text_label.py
# Author: Anthony Peter Kuzub
# Version: 20260221.Standardized.1
#
# Description: A mixin class for the DynamicGuiBuilder that handles the creation of a label widget.

import os
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import tkinter as tk
from tkinter import ttk
import inspect

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaOchestration.Methods.widget_event_binder import bind_variable_trace
from oaGuiManager.Core.context.widget_context import WidgetContext
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

@WidgetRegistry.register("_Label", "_SmartLabel", "_GuiLabel")
class BuilderTextLabelCreator(TransparencyMixin):
    """
    A mixin class that provides the functionality for creating a label widget.
    """

    def make_text_label(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬 Entering make_text_label with config: {config_data}", level="TRACE")
        """Creates a Tkinter label widget."""
        # ⚡ HARDENED INTERFACE: Standardize extraction
        config = config_data
        label = config.get("label_active", config.get("label", "Label"))
        value = config.get("value", "")
        units = config.get("units", config.get("unit_text", ""))
        path = config.get("path")

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

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬⚡️ Creating new label: '{label}' at {path}.", level="DEBUG")
        try:
            # Robust Background Inheritance
            try:
                p_bg = parent_widget.cget("bg")
                if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
            except:
                p_bg = "#2b2b2b"

            # Use tk.Canvas for sub_frame to support background slicing
            sub_frame = tk.Canvas(
                parent_widget,
                bd=0,
                highlightthickness=0,
                relief="flat",
                height=25, # Default height for label
                bg=p_bg
            )

            layout_config = config.get("layout", {})
            font_size = layout_config.get("font", 10)
            custom_font = ("Helvetica", font_size)
            custom_colour = layout_config.get("colour", None)

            label_text = f"{label}: {value}" if value else label
            if units:
                label_text += f" {units}"

            label_var = kwargs.get("variable") or tk.StringVar(master=parent_widget, value=label_text)
            
            # Apply Industrial Transparency with canvas support
            if hasattr(self, '_apply_transparency'):
                self._apply_transparency(sub_frame, sub_frame, config, builder_instance)

            def redraw_canvas_text(*args):
                if not sub_frame.winfo_exists(): return
                sub_frame.delete("industrial_text")
                w = sub_frame.winfo_width()
                h = sub_frame.winfo_height()
                if w <= 1: return
                
                txt = label_var.get()
                sub_frame.create_text(
                    5, h/2, text=txt, anchor="w",
                    fill=custom_colour or "white", font=custom_font,
                    tags="industrial_text"
                )

            # Sync background hook
            def sync_bg():
                redraw_canvas_text()
            
            sub_frame._draw = sync_bg
            sub_frame.render = sync_bg
            
            label_var.trace_add("write", redraw_canvas_text)
            sub_frame.bind("<Configure>", redraw_canvas_text, add="+")

            if path:
                if hasattr(self, 'topic_widgets'):
                    self.topic_widgets[path] = sub_frame

                # --- MQTT Wiring ---
                if state_mirror_engine and subscriber_router:
                    widget_id = path

                    # 1. Register widget
                    topic = state_mirror_engine.register_widget(
                        widget_id, label_var, base_mqtt_topic_from_path, config
                    )

                    # 2. Subscribe to topic for incoming messages
                    if topic:
                        subscriber_router.subscribe_to_topic(
                            topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                        )

                    # 3. Bind variable trace for outgoing messages
                    callback = lambda *args: state_mirror_engine.broadcast_gui_change_to_mqtt(widget_id)
                    bind_variable_trace(label_var, callback)

                    # 4. Initialize state from cache or broadcast
                    state_mirror_engine.initialize_widget_state(widget_id)

            return sub_frame

        except Exception as e:
            logger.exception("💥 Label creation for '{label}' has exploded! Error")
            return None

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderTextLabelCreator()
        return creator.make_text_label(parent_widget, config_data, context, **kwargs)
