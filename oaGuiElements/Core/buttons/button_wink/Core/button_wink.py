# button_wink/button_wink.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import inspect
import tkinter as tk

from oaConfigurationManager.FileReaders.config_reader import Config

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()

from oaGui.Core.factory.base_widget_creator import BaseWidgetCreator
from oaGui.Hooks.registry.registry_widget_store import RegistryWidgetStore
from oaGui.Methods.formatting.i18n_utils import get_text
from oaGui.Workers.compositing.sync_behavior import SyncBehavior

# Core Modules
from .wink_config import extract_wink_config
from .wink_events import bind_wink_events
from .wink_physics import blink_loop, update_physics
from .wink_renderer import draw_wink_visuals
from .wink_state import create_wink_state


@RegistryWidgetStore.register("_WinkButton")
class BuilderButtonWinkCreator(BaseWidgetCreator, SyncBehavior):
    """
    A mixin to create 'Wink' style buttons/switches.
    Mimics a mechanical shutter revealing a bright background.
    Refactored into modules for better maintainability.
    """

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Assembles the Wink Button UI elements."""
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔬🏗️🔘 [BUILDER] Entering _assemble_ui", level="TRACE")

        # 1. Extract Config
        config = extract_wink_config(config_data)
        path = config_data.get("path")
        label = get_text(config_data.get('label_active'))

        builder_instance = getattr(context, 'builder_instance', None) or kwargs.get('builder_instance') or self
        state_mirror_engine = getattr(context, 'state_mirror_engine', None) or kwargs.get('state_mirror_engine')
        subscriber_router = getattr(context, 'subscriber_router', None) or kwargs.get('subscriber_router')
        base_mqtt_topic = getattr(context, 'base_mqtt_topic_from_path', None) or kwargs.get('base_mqtt_topic_from_path')

        # 2. Variable Management
        value_var = kwargs.get("variable")
        if value_var is None:
            initial_state = bool(config.get("value_default", False))
            value_var = tk.BooleanVar(master=parent_widget, value=initial_state)

        # 3. Create State
        state = create_wink_state(config, value_var.get())

        # 4. Container Frame
        frame = tk.Canvas(parent_widget, bd=0, highlightthickness=0, relief="flat", width=config["width"], height=config["height"])
        frame.is_locked = False
        frame.variable = value_var # Attach variable for BaseWidgetCreator to find it

        # 6. Canvas (Inner drawing)
        canvas = tk.Canvas(
            frame,
            width=config["width"],
            height=config["height"],
            bg=config["bezel_color"],
            highlightthickness=0,
            bd=0,
            relief="flat"
        )
        canvas.place(x=0, y=0)

        # 7. Transparency
        if hasattr(builder_instance, '_apply_transparency'):
            builder_instance._apply_transparency(frame, canvas, config_data, builder_instance)
            builder_instance._apply_transparency(frame, frame, config_data, builder_instance)

        def draw_visuals_callback():
            if hasattr(builder_instance, "is_visible") and not builder_instance.is_visible:
                return
            draw_wink_visuals(canvas, state, config, label)

        def sync_bg():
            draw_visuals_callback()

        frame._draw = sync_bg

        # 8. Events and Physics
        state["_last_value"] = value_var.get()

        def on_value_change(*args):
            new_val = value_var.get()
            if new_val == state["_last_value"] and not state["animating"]:
                return
            state["_last_value"] = new_val

            if config["blink_interval"] > 0 and new_val:
                if not state.get("is_blinking_active"):
                    state["is_blinking_active"] = True
                    state["blink_open"] = True
                    state["target_open"] = 1.0
                    blink_loop(canvas, state, config, value_var, draw_visuals_callback)
            else:
                state["is_blinking_active"] = False
                state["target_open"] = 1.0 if new_val else 0.0

            if config["is_latching"] and not state["is_pressed"]:
                state["is_latched"] = new_val

            if not state.get("animating"):
                state["animating"] = True
                update_physics(canvas, state, config, draw_visuals_callback)

            if state_mirror_engine and path:
                 extra = {"LOCKED": state["is_locked"]}
                 state_mirror_engine.broadcast_gui_change_to_mqtt(path, extra_payload=extra)

        value_var.trace_add("write", on_value_change)

        # Initial Animation Setup
        if value_var.get() and config["blink_interval"] > 0:
             if not state.get("is_blinking_active"):
                 state["is_blinking_active"] = True
                 blink_loop(canvas, state, config, value_var, draw_visuals_callback)

        def _update_from_mqtt(data):
            if "LOCKED" in data:
                state["is_locked"] = data["LOCKED"]
                draw_visuals_callback()

        # Note: MQTT registration is now partially handled by BaseWidgetCreator,
        # but we keep custom callback logic here if needed.
        # Actually, BaseWidgetCreator doesn't support custom update_callback yet.
        # I'll let BaseWidgetCreator handle the basics and we can override if needed.

        def broadcast_locked(is_locked):
            if state_mirror_engine and path:
                 extra = {"LOCKED": is_locked}
                 state_mirror_engine.broadcast_gui_change_to_mqtt(path, extra_payload=extra)

        bind_wink_events(canvas, state, config, value_var, draw_visuals_callback, broadcast_locked)
        draw_visuals_callback()

        return frame, canvas

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        return BuilderButtonWinkCreator.build(parent_widget, config_data, context, **kwargs)

    def make_button_wink(self, parent_widget, config_data, context=None, **kwargs):
        """Legacy compatibility wrapper."""
        return self.build(parent_widget, config_data, context, **kwargs)
