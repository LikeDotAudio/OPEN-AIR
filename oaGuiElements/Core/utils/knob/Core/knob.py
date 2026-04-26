# knob/knob.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized Rotary Knob Widget.

import tkinter as tk

# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaGui.Methods.i18n_utils import get_text
from oaGui.Methods.safe_after_mixin import SafeAfterMixin
from oaGui.Core.base_widget_creator import BaseWidgetCreator
from oaGui.Core.factory.widget_registry import WidgetRegistry
from oaGui.Core.transparency.transparency import TransparencyManager
from oaGui.Core.transparency.transparency_mixin import TransparencyMixin

# Core Modules
from .knob_config import extract_knob_config
from .knob_interaction_mixin import KnobInteractionMixin
from .knob_renderer_mixin import KnobRendererMixin
from .knob_state import create_knob_state


class CustomKnobFrame(tk.Canvas, KnobInteractionMixin, KnobRendererMixin, SafeAfterMixin):
    """
    A self-contained, stateful Rotary Knob widget.
    Follows SRP: Handles its own interactions, state, and rendering via mixins.
    """
    def __init__(self, parent, variable, config, state, path, state_mirror_engine, label_text, **kwargs):
        self._init_safe_after()
        # 1. Geometry Normalization
        if "width" in kwargs: kwargs["width"] = max(kwargs["width"], 10)
        if "height" in kwargs: kwargs["height"] = max(kwargs["height"], 10)

        # 2. Background Inheritance
        p_bg = kwargs.pop("bg", None)
        if p_bg is None:
            try: p_bg = parent.cget("bg")
            except: p_bg = "#2b2b2b"
        if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"

        kwargs.pop("bd", None); kwargs.pop("highlightthickness", None); kwargs.pop("relief", None)
        super().__init__(parent, bd=0, highlightthickness=0, relief="flat", bg=p_bg, **kwargs)

        # 3. State Anchoring (Directly on self as per Architect directive)
        self.variable = variable
        self.config = config
        self.state = state
        self.path = path
        self.state_mirror_engine = state_mirror_engine
        self.label_text = label_text

        self.min_val, self.max_val = config["min"], config["max"]
        self.reff_point = config["reff_point"]
        self.is_locked = False
        self.temp_entry = None

        # 4. Lifecycle Bindings
        self._bind_knob_events()
        self.variable.trace_add("write", lambda *a: self._draw_visuals())

        # Initial Render
        self.safe_after(50, self._draw_visuals)

    def _broadcast_cb(self):
        """Helper for mixin to trigger MQTT updates."""
        if self.state_mirror_engine and self.path:
            self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _draw_cb(self):
        """Helper for mixin to trigger re-draws."""
        self._draw_visuals()

    def render(self): self._draw_visuals()
    def _draw(self): self._draw_visuals()

    def _jump_to_reff_point(self, event):
        self.variable.set(self.reff_point)
        self._broadcast_cb()

    def _open_manual_entry(self, event):
        if self.temp_entry and self.temp_entry.winfo_exists(): return
        self.temp_entry = tk.Entry(self, width=8, justify="center")
        self.temp_entry.place(x=event.x - 20, y=event.y - 10)
        self.temp_entry.insert(0, str(self.variable.get()))
        self.temp_entry.select_range(0, tk.END)
        self.temp_entry.focus_set()
        for b in ["<Return>", "<FocusOut>"]: self.temp_entry.bind(b, self._submit_manual_entry)
        self.temp_entry.bind("<Escape>", lambda e: self._destroy_manual_entry(None))

    def _submit_manual_entry(self, event):
        try:
            value = float(self.temp_entry.get())
            if self.min_val <= value <= self.max_val:
                self.variable.set(value); self._broadcast_cb()
        except ValueError: pass
        self._destroy_manual_entry(None)

    def _destroy_manual_entry(self, event):
        if self.temp_entry and self.temp_entry.winfo_exists():
            self.temp_entry.destroy(); self.temp_entry = None

@WidgetRegistry.register("_Knob", "_SmartKnob")
class BuilderKnobCreator(BaseWidgetCreator, TransparencyMixin):

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Assembles the Knob UI elements."""
        config = extract_knob_config(config_data)
        label = get_text(get_text(config_data.get('label_active'))) or get_text(get_text(config_data.get('label')), "Unknown")
        path = config_data.get("path")

        knob_var = kwargs.get("variable") or tk.DoubleVar(master=parent_widget, value=config["value_default"])
        state = create_knob_state(config)

        s_engine = getattr(context, 'state_mirror_engine', None) or kwargs.get('state_mirror_engine')
        s_router = getattr(context, 'subscriber_router', None) or kwargs.get('subscriber_router')
        b_topic = getattr(context, 'base_mqtt_topic_from_path', None) or kwargs.get('base_mqtt_topic_from_path', "")
        b_inst = getattr(context, 'builder_instance', None) or kwargs.get('builder_instance') or self

        frame = CustomKnobFrame(parent_widget, knob_var, config, state, path, s_engine, label, width=config["width"], height=config["height"])

        if hasattr(b_inst, '_apply_transparency'):
            TransparencyManager.apply_transparency(frame, frame, config_data, b_inst)

        if path and s_engine:
            topic = s_engine.register_widget(path, knob_var, b_topic, config_data, instance=frame)
            if s_router and topic: s_router.subscribe_to_topic(topic, s_engine.sync_incoming_mqtt_to_gui)
            s_engine.initialize_widget_state(path)

        return frame, frame

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        return BuilderKnobCreator.build(parent_widget, config_data, context, **kwargs)

    def make_knob(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderKnobCreator.build(parent_widget, config_data, context, **kwargs)
