# button_trapezoid/button_trapezoid.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized dynamic, theme-aware trapezoidal button.

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from loguru import logger

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import builder_logger
from oaConfigurationManager.FileReaders.config_reader import Config
app_constants = Config.get_instance()

from oaStyle.Core.style import THEMES, DEFAULT_THEME
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaGui.Methods.i18n_utils import get_text
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

# --- EXTRACTED CORE MODULES ---
from ..trapezoid_renderer_mixin import TrapezoidRendererMixin
from ..trapezoid_interaction_mixin import TrapezoidInteractionMixin

from oaGuiBuilder.Core.base_widget_creator import BaseWidgetCreator

class TrapezoidButton(tk.Canvas, TrapezoidRendererMixin, TrapezoidInteractionMixin):
    """
    A self-contained Trapezoid Button widget that manages its own state and interaction.
    Refactored to eliminate redundant parameter passing (Data Trampolining).
    """
    def __init__(self, parent, variable, config, label, path, state_mirror_engine, 
                 base_mqtt_topic_from_path, subscriber_router, **kwargs):
        self.config_data = config
        self.variable = variable
        self.label = label
        self.path = path
        self.state_mirror_engine = state_mirror_engine
        self.base_mqtt_topic_from_path = base_mqtt_topic_from_path
        self.subscriber_router = subscriber_router
        self.is_latching = config.get("latching", False)
        self._is_pressed = False
        
        # Extract dimensions
        width = config.get("width", 80)
        height = config.get("height", 50)
        full_height = height + (25 if label else 0)
        
        # Background handling
        p_bg = kwargs.pop("bg", None)
        if p_bg is None:
            try: p_bg = parent.cget("bg")
            except: p_bg = "#2b2b2b"
        if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"

        super().__init__(parent, bd=0, highlightthickness=0, relief="flat", 
                         width=width, height=full_height, bg=p_bg, **kwargs)
        
        # Bindings
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", lambda e: self.render(), add="+")

        # State Sync
        self.variable.trace_add("write", lambda *a: self.render_and_broadcast())
        
        if self.path and self.state_mirror_engine:
            topic = self.state_mirror_engine.register_widget(
                self.path, self.variable, self.base_mqtt_topic_from_path, self.config_data)
            if self.subscriber_router and topic:
                self.subscriber_router.subscribe_to_topic(topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui)
            self.state_mirror_engine.initialize_widget_state(self.path)

        # Rendering API
        self._draw = self.render
        self.render()

    def render(self):
        """Orchestrates the drawing process."""
        self._trigger_redraw()

    def render_and_broadcast(self):
        """Redraws the button and announces the change to MQTT."""
        self.render()
        if self.state_mirror_engine:
            self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _trigger_redraw(self):
        """Prepares state and calls the renderer mixin."""
        current_face = self.config_data.get("color", "#8B0000")
        
        # Attempt to sample parent background for transparency-like feel
        try:
            p_bg = self.master.cget("bg")
            sampled_bg = self.cget("bg")
            if current_face == p_bg and sampled_bg.startswith("#"):
                current_face = sampled_bg
        except: pass

        current_state = {
            "pressed": self._is_pressed,
            "lit": self.variable.get(),
            "base_color": current_face,
            "led_color": self.config_data.get("led_color", self.config_data.get("indicator_color", "#FF0000")),
            "label": self.label
        }
        self.render_trapezoid_button(self, self.config_data, current_state)

@WidgetRegistry.register("_TrapezoidButton")
class BuilderButtonTrapezoidCreator(BaseWidgetCreator, TransparencyMixin):
    """Factory for creating TrapezoidButton instances."""

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Implementation of the Template Method for Trapezoid Button assembly."""
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️🔘 [BUILDER] Entering _assemble_ui", level="TRACE")
        
        label = get_text(get_text(config_data.get('label_active')), get_text(config_data.get('label'), ""))
        button_text = config_data.get("button_text", "")
        if button_text: config_data["button_text"] = button_text[:3]
        
        path = config_data.get("path")

        # Context Extraction
        ctx = context if context else type('obj', (object,), kwargs)()
        state_mirror_engine = getattr(ctx, 'state_mirror_engine', None) or kwargs.get('state_mirror_engine')
        subscriber_router = getattr(ctx, 'subscriber_router', None) or kwargs.get('subscriber_router')
        base_mqtt_topic_from_path = getattr(ctx, 'base_mqtt_topic_from_path', None) or kwargs.get('base_mqtt_topic_from_path')
        builder_instance = getattr(ctx, 'builder_instance', None) or getattr(ctx, 'app_instance', None) or kwargs.get('builder_instance')

        initial_state = bool(config_data.get("value_default", False))
        state_var = kwargs.get("variable") or tk.BooleanVar(master=parent_widget, value=initial_state)

        # Instantiate the specialized widget class
        button = TrapezoidButton(
            parent_widget, state_var, config_data, label, path, 
            state_mirror_engine, base_mqtt_topic_from_path, subscriber_router
        )

        return button, button

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        return BuilderButtonTrapezoidCreator.build(parent_widget, config_data, context, **kwargs)

    def make_button_trapezoid(self, parent_widget, config_data, context=None, **kwargs):
        """Legacy compatibility wrapper."""
        return self.build(parent_widget, config_data, context, **kwargs)
