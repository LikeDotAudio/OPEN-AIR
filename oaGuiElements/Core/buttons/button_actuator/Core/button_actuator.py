# button_actuator/button_actuator.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized dynamic Momentary Actuator Button.

import inspect

# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

from oaGui.Methods.i18n_utils import get_text
from oaGuiBuilder.Core.base_widget_creator import BaseWidgetCreator
from oaGuiManager.Core.factory.button_canvas_base import CanvasButton
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

# --- EXTRACTED CORE MODULES ---
from .actuator_interaction_mixin import ActuatorInteractionMixin
from .actuator_state_mixin import ActuatorStateMixin


class ActuatorButton(CanvasButton, ActuatorInteractionMixin, ActuatorStateMixin):
    """
    A self-contained, stateful Momentary Actuator Button.
    Inherits from CanvasButton and adds interaction/state mixins.
    """
    def __init__(self, parent, config, path, state_mirror_engine, base_mqtt_topic, subscriber_router, builder_instance, **kwargs):
        self.label = get_text(config.get("label"), "Actuator")
        self.text_active = get_text(config.get("label_active"), self.label)
        self.text_inactive = get_text(config.get("label_inactive"), self.label)
        self.path = path
        self.config_data = config
        self.state_mirror_engine = state_mirror_engine
        self.base_mqtt_topic = base_mqtt_topic
        self.subscriber_router = subscriber_router

        # Super initialization (CanvasButton)
        super().__init__(
            parent, text=self.text_inactive, command=None,
            width=config.get("layout", {}).get("width", 100),
            height=config.get("layout", {}).get("height", 50),
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
class BuilderButtonActuatorCreator(BaseWidgetCreator, TransparencyMixin):
    """Factory for creating Actuator Buttons."""

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔬🏗️🔘 [BUILDER] Entering _assemble_ui", level="TRACE")

        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = getattr(ctx, 'builder_instance', None) or getattr(ctx, 'app_instance', None) or kwargs.get('builder_instance')

        label, path = get_text(config_data.get("label")), config_data.get("path")
        b_topic = getattr(ctx, 'base_mqtt_topic_from_path', None) or kwargs.get('base_mqtt_topic_from_path')

        button = ActuatorButton(
            parent_widget, config_data, path,
            getattr(ctx, 'state_mirror_engine', None) or kwargs.get('state_mirror_engine'),
            b_topic,
            getattr(ctx, 'subscriber_router', None) or kwargs.get('subscriber_router'),
            b_inst
        )

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"✅🆗🔘 [SUCCESS] The actuator '{get_text(config_data.get('label'), 'Unknown')}' has materialized!", level="SUCCESS")
        return button, button

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        return BuilderButtonActuatorCreator.build(parent_widget, config_data, context, **kwargs)

    def make_button_actuator(self, parent_widget, config_data, context=None, **kwargs):
        """Legacy compatibility wrapper."""
        return self.build(parent_widget, config_data, context, **kwargs)
