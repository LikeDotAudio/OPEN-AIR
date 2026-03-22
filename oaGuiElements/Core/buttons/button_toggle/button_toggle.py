# button_toggle/button_toggle.py
# Author: Anthony Peter Kuzub
# Version: 20260217.1
#
# Description: This file provides the BuilderButtonToggleCreator class for creating photorealistic

import os
import tkinter as tk
from tkinter import ttk
import inspect

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaGuiManager.Core.factory.button_canvas_base import CanvasButton
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaOchestration.Methods.widget_event_binder import bind_variable_trace
from oaComMQTT.Methods.mqtt_topic_utils import get_topic
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

@WidgetRegistry.register("_GuiButtonToggle", "_SmartToggle", "_ButtonToggle")
class BuilderButtonToggleCreator(TransparencyMixin):
    """
    A mixin class that provides the functionality for creating photorealistic
    toggle button widgets that flip between two boolean states.
    """
    def __init__(self):
        super().__init__() # Call parent __init__ if it exists (TransparencyMixin has none)
        self.topic_widgets = {} # Initialize topic_widgets attribute

    def make_button_toggle(self, parent_widget, config_data, context=None, **kwargs):
        if LOCAL_DEBUG: logger.trace(f"🔬 Entering make_button_toggle with config: {config_data}")  
        """Creates a photorealistic CanvasButton that acts as a binary toggle."""
        current_function_name = inspect.currentframe().f_code.co_name
        label = config_data.get("label_active") or config_data.get("label", "")
        
        config = config_data
        path = config_data.get("path")

        # ⚡ HARDENED INTERFACE: Extract from context if available
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            app_instance = context.app_instance
            builder_instance = context.builder_instance or app_instance
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self
            app_instance = kwargs.get("app_instance")

        try:
            # Parse Options for Text
            options_map = config.get("options", {})
            on_config = options_map.get("ON", {})
            off_config = options_map.get("OFF", {})
            on_text = on_config.get("label_active", label if label else "ON")
            off_text = off_config.get("label_inactive", label if label else "OFF")

            # State Variable
            is_on_init = options_map.get("ON", {}).get("selected", False)
            state_var = kwargs.get("variable") or tk.BooleanVar(master=parent_widget, value=is_on_init)

            # Layout Configuration
            layout = config.get("layout", {})
            btn_h = config.get("height", layout.get("height", 50))
            btn_w = config.get("width", layout.get("width", 100))
            font_size = layout.get("font", 10)
            corner_r = layout.get("corner_radius", 6)
            alpha = float(config.get("alpha", layout.get("alpha", 1.0)))

            # Colors
            c_act = config.get("active_color", "#FF9900")
            
            # ⚡ DETERMINISTIC: Default to a fixed dark grey for the inactive state
            c_inact = config.get("bg_color", "#1a1a1a")
            c_act_bg = config.get("active_bg_color", "#000000")
            t_act = config.get("active_text_color", "#1a1a1a")
            t_inact = config.get("text_color", "#888888")
            
            glow_int = config.get("glow_intensity", 1.0)
            f_on_style = config.get("active_font_style", "bold")
            f_on_size = config.get("active_font_size")
            f_off_style = config.get("inactive_font_style", "normal")
            f_off_size = config.get("inactive_font_size")

            # Main Canvas Container (if label exists)
            if label:
                container = tk.Canvas(
                    parent_widget,
                    bd=0,
                    highlightthickness=0,
                    relief="flat",
                    width=btn_w + 10,
                    height=btn_h + 25
                )
                if hasattr(builder_instance, '_apply_transparency'):
                    builder_instance._apply_transparency(container, container, config, builder_instance)
                
                container._last_redraw_size = (0, 0)
                def redraw_labels(*args):
                    if not container.winfo_exists(): return
                    w = container.winfo_width()
                    h = container.winfo_height()
                    if (w, h) == container._last_redraw_size:
                        return
                    if w <= 1: return
                    container._last_redraw_size = (w, h)
                    
                    container.delete("industrial_text")
                    container.create_text(
                        (btn_w + 10)/2, 12, text=label, anchor="center",
                        fill="white", font=("TkDefaultFont", 10, "bold"),
                        tags="industrial_text"
                    )
                
                container.bind("<Configure>", lambda e: redraw_labels(), add="+")
                redraw_labels()
                parent_for_button = container
            else:
                container = None
                parent_for_button = parent_widget

            # Create the CanvasButton
            button = CanvasButton(
                parent_for_button, text=off_text, command=None,
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

            if container:
                button.place(x=5, y=25)
                def sync_bg():
                    redraw_labels()
                    if hasattr(button, "_draw"): button._draw()
                container._draw = sync_bg
                container.render = sync_bg
                return_widget = container
            else:
                return_widget = button

            def update_visual_state(*args):
                """Syncs button appearance with the boolean state_var."""
                is_on = state_var.get()
                button.set_active(is_on)
                button.set_text(on_text if is_on else off_text)

            def on_click(event):
                """Toggle the state on click."""
                state_var.set(not state_var.get())

            button.bind("<Button-1>", on_click, add="+")
            state_var.trace_add("write", update_visual_state)
            
            # Initial Sync
            update_visual_state()

            if path:
                self.topic_widgets[path] = (state_var, update_visual_state)
                # ⚡ LOCK REGISTRATION: Pass 'button' as instance
                topic = state_mirror_engine.register_widget(path, state_var, base_mqtt_topic_from_path, config, instance=button)
                bind_variable_trace(state_var, lambda: state_mirror_engine.broadcast_gui_change_to_mqtt(path))
                
                if subscriber_router and topic:
                    subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
                state_mirror_engine.initialize_widget_state(path)

            if LOCAL_DEBUG: logger.success(f"✅ SUCCESS! The toggle button '{label}' has materialized!")
            return return_widget

        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("❌ Error creating toggle button '{label}'")
            return None

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderButtonToggleCreator()
        return creator.make_button_toggle(parent_widget, config_data, context, **kwargs)
