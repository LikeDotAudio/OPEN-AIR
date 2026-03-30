# button_actuator/button_actuator.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized dynamic Momentary Actuator Button.

import tkinter as tk
from loguru import logger

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = False
from oaLogging.Core.logger import builder_logger
from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()

from oaGuiManager.Core.factory.button_canvas_base import CanvasButton
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

# --- EXTRACTED CORE MODULES ---
from .Core.actuator_interaction_mixin import ActuatorInteractionMixin
from .Core.actuator_state_mixin import ActuatorStateMixin

class ActuatorButton(CanvasButton, ActuatorInteractionMixin, ActuatorStateMixin):
    """
    A self-contained, stateful Momentary Actuator Button.
    Inherits from CanvasButton and adds interaction/state mixins.
    """
    def __init__(self, parent, config, path, state_mirror_engine, base_mqtt_topic, subscriber_router, builder_instance, **kwargs):
        self.label = config.get("label", "Actuator")
        self.text_active = config.get("label_active", self.label)
        self.text_inactive = config.get("label_inactive", self.label)
        self.path = path
        self.config_data = config
        self.state_mirror_engine = state_mirror_engine
        self.base_mqtt_topic = base_mqtt_topic
        self.subscriber_router = subscriber_router
        
        # Super initialization (CanvasButton)
        super().__init__(
            parent, text=self.text_inactive, command=None,
            width=config.get("width", 100), height=config.get("height", 50),
            corner_radius=config.get("layout", {}).get("corner_radius", 6),
            bg_color=config.get("bg_color", "#1a1a1a"),
            active_color=config.get("active_color", "#FF9900"),
            active_bg_color=config.get("active_bg_color", "#000000"),
            text_color=config.get("text_color", "#888888"),
            active_text_color=config.get("active_text_color", "#1a1a1a"),
            glow_intensity=config.get("glow_intensity", 1.0),
            active_font_style=config.get("active_font_style", "bold"),
            active_font_size=config.get("active_font_size"),
            inactive_font_style=config.get("inactive_font_style", "normal"),
            inactive_font_size=config.get("inactive_font_size"),
            alpha=float(config.get("alpha", 1.0)),
            font=("TkDefaultFont", config.get("layout", {}).get("font", 10)),
            transparency_applicator=builder_instance._apply_transparency if hasattr(builder_instance, '_apply_transparency') else None,
            config=config, builder=builder_instance
        )

        # Lifecycle Bindings
        self.bind("<ButtonPress-1>", self._on_press, add="+")
        self.bind("<ButtonRelease-1>", self._on_release, add="+")
        
        if self.path and self.state_mirror_engine:
            self._status_topic = self.state_mirror_engine.topic_calculator.calculate(f"{self.path}/active", self.base_mqtt_topic)
            if self.subscriber_router:
                self.subscriber_router.subscribe_to_topic(self._status_topic, self._on_mqtt_state_update)
            self.bind("<Destroy>", self._cleanup, add="+")

    def _cleanup(self, event):
        if event.widget == str(self):
            if self.subscriber_router:
                self.subscriber_router.unsubscribe_from_topic(self._status_topic, self._on_mqtt_state_update)

@WidgetRegistry.register("_GuiActuator", "_SmartActuator", "_ButtonActuator", "_GuiButton")
class BuilderButtonActuatorCreator(TransparencyMixin):
    """Factory for creating Actuator Buttons."""

    def make_button_actuator(self, parent_widget, config_data, context=None, **kwargs):
        if BUILDER_DEBUG: builder_logger.trace(f"🔬🏗️🔘 [BUILDER] Creating ActuatorButton.")
        
        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = ctx.builder_instance if hasattr(ctx, 'builder_instance') else ctx.app_instance
        
        path, b_topic = config_data.get("path"), ctx.base_mqtt_topic_from_path
        
        button = ActuatorButton(
            parent_widget, config_data, path, 
            ctx.state_mirror_engine, b_topic, ctx.subscriber_router, b_inst
        )

        # Layout Application (Grid)
        lay = config_data.get("layout", {})
        if "row" in lay and "column" in lay:
            button.grid(
                row=lay["row"], column=lay["column"],
                columnspan=lay.get("col_span", 1), rowspan=lay.get("row_span", 1),
                padx=lay.get("padx", 5), pady=lay.get("pady", 2),
                sticky=lay.get("sticky", "")
            )

        if BUILDER_DEBUG: builder_logger.success(f"✅🆗🔘 [SUCCESS] The actuator '{config_data.get('label')}' has materialized!")
        return button

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderButtonActuatorCreator()
        return creator.make_button_actuator(parent_widget, config_data, context, **kwargs)
