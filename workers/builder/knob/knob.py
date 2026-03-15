# knob/knob.py
import tkinter as tk
from loguru import logger
from managers.configini.config_reader import Config
from managers.Display.factory.widget_registry import WidgetRegistry
from workers.builder.core.base_widget_creator import BaseWidgetCreator

# Core Modules
from .core.knob_config import extract_knob_config
from .core.knob_state import create_knob_state
from .core.knob_renderer import draw_knob_visuals
from .core.knob_interaction_mixin import KnobInteractionMixin

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True

class CustomKnobFrame(tk.Canvas, KnobInteractionMixin):
    def __init__(self, parent, variable, config, state, path, state_mirror_engine, 
                 draw_cb, broadcast_cb, **kwargs):
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

        super().__init__(parent, bd=0, highlightthickness=0, relief="flat", bg=p_bg, **kwargs)
        self.pack_propagate(False)
        self.grid_propagate(False)
        
        self.variable = variable
        self.config = config
        self.state = state
        self.min_val, self.max_val = config["min"], config["max"]
        self.reff_point = config["reff_point"]
        self.path = path
        self.state_mirror_engine = state_mirror_engine
        self._draw_cb = draw_cb
        self._broadcast_cb = broadcast_cb
        
        self.is_locked = False # ⚡ INTERACTION LOCK
        self.temp_entry = None
        
        self._bind_knob_events()

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
class BuilderKnobCreator(BaseWidgetCreator):
    
    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Assembles the Knob UI elements."""
        config = extract_knob_config(config_data)
        label = config_data.get("label_active") or config_data.get("label", "Unknown")
        path = config_data.get("path")
        
        knob_value_var = kwargs.get("variable") or tk.DoubleVar(value=config["value_default"])
        state = create_knob_state(config)

        def broadcast_cb():
            state_mirror_engine = getattr(context, 'state_mirror_engine', None) or kwargs.get('state_mirror_engine')
            if state_mirror_engine and path: 
                state_mirror_engine.broadcast_gui_change_to_mqtt(path)

        # Container frame/canvas
        frame = CustomKnobFrame(
            parent_widget, knob_value_var, config, state, 
            path, 
            getattr(context, 'state_mirror_engine', None) or kwargs.get('state_mirror_engine'), 
            None, # draw_cb placeholder
            broadcast_cb,
            width=config["width"], height=config["height"]
        )
        
        frame.variable = knob_value_var # Ensure variable is accessible for registration

        def draw_cb(): 
            draw_knob_visuals(frame, state, config, knob_value_var.get(), label)
        
        frame._draw_cb = draw_cb # Inject actual draw callback
        knob_value_var.trace_add("write", lambda *a: draw_cb())
        frame._draw = draw_cb
        frame.render = draw_cb
        
        draw_cb()
        return frame, frame

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """Legacy compatibility layer."""
        return BuilderKnobCreator.build(parent_widget, config_data, context, **kwargs)

    # Maintain backward compatibility for mixin usage
    def make_knob(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderKnobCreator.build(parent_widget, config_data, context, **kwargs)
