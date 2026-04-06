# button_wink/button_wink.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from tkinter import ttk

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaGuiFramework.Methods.i18n_utils import get_text
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

# Core Modules
from .Core.wink_config import extract_wink_config
from .Core.wink_state import create_wink_state
from .Core.wink_physics import update_physics, blink_loop
from .Core.wink_renderer import draw_wink_visuals
from .Core.wink_events import bind_wink_events

@WidgetRegistry.register("_WinkButton")
class BuilderButtonWinkCreator(TransparencyMixin):
    """
    A mixin to create 'Wink' style buttons/switches.
    Mimics a mechanical shutter revealing a bright background.
    Refactored into modules for better maintainability.
    """

    def make_button_wink(self, parent_widget, config_data, context=None, **kwargs):
        """Creates a Wink Button widget."""
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️🔘 [BUILDER] Entering make_button_wink", level="TRACE")
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📜📑💻 [CONFIG] Raw config received: {config_data}", level="DEBUG")

        # 1. Extract Config
        config = extract_wink_config(config_data)
        path = config_data.get("path")
        label = get_text(config_data.get('label_active'))
        
        # ⚡ HARDENED INTERFACE: Extract from context if available
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...", level="TRACE")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            app_instance = context.app_instance
            builder_instance = context.builder_instance or app_instance
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.", level="DEBUG")
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self
            app_instance = kwargs.get("app_instance")
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "⚠️🔔🖱️ [CONTEXT] Context missing; fell back to self/kwargs.", level="DEBUG")

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬⚡️🔳 [BUILDER] Spawning wink button for '{label}' at path '{path}'.", level="DEBUG")

        # 2. Variable Management
        value_var = kwargs.get("variable")
        if value_var is None:
            initial_state = bool(config.get("value_default", False))
            value_var = tk.BooleanVar(master=parent_widget, value=initial_state)
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔋🔘✨ [STATE] Initial state for '{label}': {value_var.get()}", level="DEBUG")

        # 3. Create State
        state = create_wink_state(config, value_var.get())

        # 4. Container Frame
        # ⚡ HIGH-FIDELITY: Use tk.Canvas for container to ensure no grey corners
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🏗️🪟🖼️ [CONSTRUCT] Creating canvas container for wink '{label}'", level="TRACE")
        frame = tk.Canvas(parent_widget, bd=0, highlightthickness=0, relief="flat", width=config["width"], height=config["height"])
        frame.is_locked = False # ⚡ INTERACTION LOCK
        
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
        
        # Apply Industrial Transparency to both container and inner canvas
        if hasattr(builder_instance, '_apply_transparency'):
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"👻🌀🪟 [ALPHA] Applying industrial transparency to wink '{label}'", level="TRACE")
            # 1. Slices the patina onto the inner drawing canvas
            builder_instance._apply_transparency(frame, canvas, config_data, builder_instance)
            # 2. Also slices onto the outer container frame to handle padding/margins
            builder_instance._apply_transparency(frame, frame, config_data, builder_instance)
        
        def draw_visuals_callback():
            # ⚡ VISIBILITY GUARD: Stop rendering and physics if tab is hidden.
            # This significantly reduces CPU overhead for background animations.
            if hasattr(builder_instance, "is_visible") and not builder_instance.is_visible:
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🙈🚫🎨 [REDRAW] Redraw ABORTED for hidden wink '{label}'", level="TRACE")
                return

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔄✨🎨 [REDRAW] Rendering wink visuals for '{label}' (Open: {state.get('current_open'):.2f})", level="TRACE")
            draw_wink_visuals(canvas, state, config, label)
            
        def sync_bg():
            draw_visuals_callback()
        
        frame._draw = sync_bg
        
        # 8. MQTT and State Mirroring
        def broadcast_locked(is_locked):
            if state_mirror_engine and path:
                 matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"⚡🔴📡 [MQTT] Broadcasting wink lock state change for '{label}': {is_locked}", level="DEBUG")
                 extra = {"LOCKED": is_locked}
                 state_mirror_engine.broadcast_gui_change_to_mqtt(path, extra_payload=extra)

        state["_last_value"] = value_var.get()

        def on_value_change(*args):
            new_val = value_var.get()
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"⚡🔄✨ [EVENT] Wink value change detected for '{label}': {new_val}", level="INFO")
            
            # Purity check: only act if state actually changed or we need to stop an animation
            if new_val == state["_last_value"] and not state["animating"]:
                return
            state["_last_value"] = new_val

            if config["blink_interval"] > 0 and new_val:
                if not state.get("is_blinking_active"):
                    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🌀⏳✨ [ANIM] Starting blink loop for '{label}'", level="DEBUG")
                    state["is_blinking_active"] = True
                    state["blink_open"] = True
                    state["target_open"] = 1.0
                    blink_loop(canvas, state, config, value_var, draw_visuals_callback)
            else:
                # ⚡ SILENCE RUNAWAY: Explicitly stop blinking
                state["is_blinking_active"] = False
                state["target_open"] = 1.0 if new_val else 0.0
            
            if config["is_latching"] and not state["is_pressed"]:
                state["is_latched"] = new_val

            if not state.get("animating"):
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🌀⏳🌀 [ANIM] Starting physics update for '{label}'", level="TRACE")
                state["animating"] = True
                update_physics(canvas, state, config, draw_visuals_callback)

            if state_mirror_engine and path:
                 matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"⚡🔴📡 [MQTT] Broadcasting wink value change for '{label}' to '{path}'", level="DEBUG")
                 extra = {"LOCKED": state["is_locked"]}
                 state_mirror_engine.broadcast_gui_change_to_mqtt(path, extra_payload=extra)

        value_var.trace_add("write", on_value_change)
        
        # ⚡ INITIALIZATION: Only start blink if interval > 0 AND state is ON
        if value_var.get() and config["blink_interval"] > 0:
             if not state.get("is_blinking_active"):
                 state["is_blinking_active"] = True
                 blink_loop(canvas, state, config, value_var, draw_visuals_callback)

        def _update_from_mqtt(data):
            if "LOCKED" in data:
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📥📶🔄 [MQTT] Incoming lock state for '{label}': {data['LOCKED']}", level="DEBUG")
                state["is_locked"] = data["LOCKED"]
                draw_visuals_callback()

        if path and state_mirror_engine:
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📡📶🔗 [MQTT] Registering wink at path '{path}'", level="TRACE")
            topic = state_mirror_engine.register_widget(
                path, value_var, base_mqtt_topic_from_path, config_data, update_callback=_update_from_mqtt, instance=frame
            )
            if subscriber_router and topic:
                matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📥📶🔄 [MQTT] Subscribing to topic: {topic}", level="DEBUG")
                subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
            
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔄⏳🔋 [STATE] Initializing widget state from cache/broker for '{path}'", level="TRACE")
            state_mirror_engine.initialize_widget_state(path)

        # 9. Events
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🖱️👆🕹️ [EVENTS] Binding input protocols for wink '{label}'", level="TRACE")
        bind_wink_events(canvas, state, config, value_var, draw_visuals_callback, broadcast_locked)
        
        # Initial Draw
        draw_visuals_callback()

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"✅🆗🔳 [SUCCESS] The wink button '{label}' has materialized!", level="SUCCESS")
        return frame

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderButtonWinkCreator()
        return creator.make_button_wink(parent_widget, config_data, context, **kwargs)
