# knob/dynamic_guimake_knob.py
import tkinter as tk

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from workers.Command_Router.mqtt.mqtt_topic_utils import get_topic
from managers.Display.transparency.transparency_manager import TransparencyManager
from managers.Display.factory.widget_registry import WidgetRegistry

# Core Modules
from .core.knob_config import extract_knob_config
from .core.knob_state import create_knob_state
from .core.knob_renderer import draw_knob_visuals
from .core.knob_events import bind_knob_events

class CustomKnobFrame(tk.Canvas):
    def __init__(self, parent, variable, min_val, max_val, reff_point, path, state_mirror_engine, command, *args, **kwargs):
        # ⚡ OPTIMIZATION: Ensure frame respects its requested dimensions to prevent clipping
        if "width" in kwargs: kwargs["width"] = max(kwargs["width"], 10)
        if "height" in kwargs: kwargs["height"] = max(kwargs["height"], 10)
        
        # Robust Background Inheritance
        p_bg = kwargs.pop("bg", None)
        if p_bg is None:
            try:
                p_bg = parent.cget("bg")
                if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
            except:
                p_bg = "#2b2b2b"

        # Pop other explicit arguments to prevent 'multiple values' errors
        kwargs.pop("bd", None)
        kwargs.pop("highlightthickness", None)
        kwargs.pop("relief", None)

        super().__init__(parent, bd=0, highlightthickness=0, relief="flat", bg=p_bg, *args, **kwargs)
        self.pack_propagate(False)
        self.grid_propagate(False)
        self.variable, self.min_val, self.max_val, self.reff_point = variable, min_val, max_val, reff_point
        self.path, self.state_mirror_engine, self.command = path, state_mirror_engine, command
        self.is_locked = False # ⚡ INTERACTION LOCK
        self.temp_entry = None

    def _jump_to_reff_point(self, event):
        if LOCAL_DEBUG: logger.debug(f"⚡ User invoked Quantum Jump! Resetting to {self.reff_point}")
        self.variable.set(self.reff_point)
        if self.state_mirror_engine: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _open_manual_entry(self, event):
        if self.temp_entry and self.temp_entry.winfo_exists(): return
        self.temp_entry = tk.Entry(self, width=8, justify="center")
        self.temp_entry.place(x=event.x - 20, y=event.y - 10)
        self.temp_entry.insert(0, str(self.variable.get()))
        self.temp_entry.select_range(0, tk.END)
        self.temp_entry.focus_set()
        for b in ["<Return>", "<FocusOut>"]: self.temp_entry.bind(b, self._submit_manual_entry)
        self.temp_entry.bind("<Escape>", self._destroy_manual_entry)

    def _submit_manual_entry(self, event):
        try:
            val = float(self.temp_entry.get())
            if self.min_val <= val <= self.max_val:
                self.variable.set(val)
                if self.state_mirror_engine: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)
        except ValueError: pass
        self._destroy_manual_entry(event)

    def _destroy_manual_entry(self, event):
        if self.temp_entry and self.temp_entry.winfo_exists():
            self.temp_entry.destroy(); self.temp_entry = None

@WidgetRegistry.register("_Knob", "_SmartKnob")
class BuilderKnobCreator:
    
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """
        Static factory method for creating a Knob widget.
        Replaces the old instance-based make_knob.
        """
        if LOCAL_DEBUG: logger.opt(raw=True).trace(f"🔬 Entering BuilderKnobCreator.make with config: {config_data}")
        config = extract_knob_config(config_data)
        path, label = config_data.get("path"), config_data.get("label_active")
        
        # ⚡ HARDENED INTERFACE: Extract from context if available
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            app_instance = context.app_instance
            builder_instance = context.builder_instance or app_instance # Fallback for safety
        else:
            # Fallback for legacy calls (should be phased out)
            state_mirror_engine = kwargs.get("state_mirror_engine")
            subscriber_router = kwargs.get("subscriber_router")
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance")
            app_instance = kwargs.get("app_instance")

        knob_value_var = kwargs.get("variable") or tk.DoubleVar(value=config["value_default"])
        state = create_knob_state(config)

        # Container frame
        frame = CustomKnobFrame(
            parent_widget, knob_value_var, config["min"], config["max"], config["reff_point"], 
            path, state_mirror_engine, None,
            width=config["width"], height=config["height"]
        )
        frame.pack_propagate(False) # Prevent frame from shrinking to canvas if it's smaller

        try:
            # Robust Background Inheritance for factory
            try:
                p_bg = parent_widget.cget("bg")
                if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
            except:
                p_bg = "#2b2b2b"

            canvas = tk.Canvas(frame, width=config["width"], height=config["height"], highlightthickness=0, bd=0, relief="flat", bg=p_bg)
            canvas.pack(expand=True, fill=tk.BOTH)

            # Apply Transparency via Manager
            TransparencyManager.apply_transparency(frame, canvas, config_data, builder_instance)
            # ⚡ MANDATORY: Slices the patina onto the outer container frame too
            TransparencyManager.apply_transparency(frame, frame, config_data, builder_instance)

            def sync_bg():
                draw_cb()

            def draw_cb(): 
                draw_knob_visuals(canvas, state, config, knob_value_var.get(), label)
            
            knob_value_var.trace_add("write", lambda *a: draw_cb())
            frame._draw = sync_bg
            frame.render = sync_bg
            
            # Initial sync
            sync_bg()

            def broadcast_cb():
                if state_mirror_engine: state_mirror_engine.broadcast_gui_change_to_mqtt(path)

            bind_knob_events(canvas, frame, state, config, knob_value_var, draw_cb, broadcast_cb)

            if path and state_mirror_engine:
                topic = state_mirror_engine.register_widget(path, knob_value_var, base_mqtt_topic_from_path, config_data, instance=frame)
                if subscriber_router and topic:
                    subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
                state_mirror_engine.initialize_widget_state(path)

            draw_cb()
            if LOCAL_DEBUG: logger.success(f"✅ SUCCESS! The knob '{label}' has materialized!")
            return frame
        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("🔘❌ Error creating knob '{label}'")
            return None

    # Maintain backward compatibility for mixin usage until full transition
    def make_knob(self, parent_widget, config_data, context=None, **kwargs):
        # In mixin mode, 'self' is the builder instance, so pass it as app_instance if needed
        # But wait, self IS the builder instance. 
        # The new static 'make' expects 'context' to contain 'app_instance'.
        # If calling from legacy mixin, we need to ensure transparency works.
        if context and not context.app_instance:
             # Create a patched context? No, Context is frozen.
             # We assume if make_knob is called on the builder, 'self' is the builder.
             pass
        
        # Call static implementation
        # If context is missing app_instance (because it's the old style context), pass self as builder_instance in kwargs
        # ⚡ ROBUSTNESS: Ensure we don't pass multiple values for builder_instance
        b_inst = kwargs.pop('builder_instance', self)
        return BuilderKnobCreator.make(parent_widget, config_data, context, builder_instance=b_inst, **kwargs)
