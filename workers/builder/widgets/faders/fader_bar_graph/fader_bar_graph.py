# fader_bar_graph/fader_bar_graph.py
# Modularized Fader with Dual Bar Graphs.
# Version 20260315.Modular.1

import tkinter as tk
from loguru import logger

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True
from workers.logger.logger import builder_logger
from managers.configini.config_reader import Config
app_constants = Config.get_instance()

from workers.styling.style import THEMES, DEFAULT_THEME
from managers.Display.transparency.transparency_mixin import TransparencyMixin
from managers.Display.transparency.transparency import TransparencyManager
from managers.Display.factory.widget_registry import WidgetRegistry

# --- EXTRACTED CORE MODULES ---
from .core.fader_bar_renderer_mixin import FaderBarRendererMixin
from .core.fader_bar_interaction_mixin import FaderBarInteractionMixin
from .core.fader_bar_state_mixin import FaderBarStateMixin
from workers.builder.core.ui_geometry_math import UIGeometryMath

class FaderWithBarGraphFrame(
    tk.Frame,
    TransparencyMixin,
    FaderBarRendererMixin,
    FaderBarInteractionMixin,
    FaderBarStateMixin
):
    def __init__(self, master, config, path, state_mirror_engine, subscriber_router, base_mqtt_topic, builder_instance=None):
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        super().__init__(master, bd=0, highlightthickness=0)
        
        self.widget_config, self.path, self.instance = config, path, builder_instance
        self.state_mirror_engine, self.subscriber_router, self.base_mqtt_topic = state_mirror_engine, subscriber_router, base_mqtt_topic
        
        # 1. Config
        self.min_val, self.max_val = float(config.get("value_min", -100.0)), float(config.get("value_max", 0.0))
        self.log_exponent = float(config.get("log_exponent", 1.0))
        self.bar_padding, self.meter_width = int(config.get("bar_padding", 0)), int(config.get("meter_width", 15))
        self.enable_meters = config.get("bar_enable", True); self.cap_height = int(config.get("cap_height", 40))
        self.show_ticks, self.tick_steps = config.get("show_ticks", True), int(config.get("tick_steps", 10))
        
        layout = config.get("layout", {}); self.width, self.height = int(layout.get("width", 100)), int(layout.get("height", 300))
        self.left_style, self.right_style = config.get("left_meter_style", {}), config.get("right_meter_style", {})
        self.fader_track_color = config.get("fader_track_color", colors.get("secondary", "#444"))
        self.fader_grip_color = config.get("cap_colour", colors.get("fg", "#dcdcdc"))
        
        # 2. State
        self.fader_var = tk.DoubleVar(value=float(config.get("value_default", self.min_val)))
        self.left_var, self.right_var = tk.DoubleVar(value=self.min_val), tk.DoubleVar(value=self.min_val)
        self._register_vars()

        # 3. UI
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, highlightthickness=0); self.canvas.pack(fill=tk.BOTH, expand=True)
        if builder_instance and hasattr(builder_instance, '_apply_transparency'):
            TransparencyManager.apply_transparency(self, self.canvas, config, builder_instance)

        self.fader_var.trace_add("write", lambda *a: self._update_fader_pos())
        self.left_var.trace_add("write", lambda *a: self._update_meter("left"))
        self.right_var.trace_add("write", lambda *a: self._update_meter("right"))
        
        self.canvas.bind("<Button-1>", self._on_press); self.canvas.bind("<B1-Motion>", self._on_drag); self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.after(10, self._draw_static); self.canvas.after(20, self._draw_dynamic)

    def render(self): self._draw_static(); self._draw_dynamic()
    def _update_fader_pos(self):
        if not hasattr(self, 'draw_h'): return
        y = self.top_m + UIGeometryMath.value_to_pixel(self.fader_var.get(), self.min_val, self.max_val, self.draw_h, reverse=True)
        self.canvas.coords("cap", self.cx, y); self.canvas.coords("cap_text", self.cx, y)
        self.canvas.itemconfig("cap_text", text=f"{self.fader_var.get():.1f}")

@WidgetRegistry.register("_FaderWithBarGraph")
class BuilderFaderBarGraphCreator(TransparencyMixin):
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        if context: s_engine, s_router, b_topic, b_inst = context.state_mirror_engine, context.subscriber_router, context.base_mqtt_topic_from_path, context.builder_instance
        else: s_engine, s_router, b_topic, b_inst = kwargs.get("state_mirror_engine"), kwargs.get("subscriber_router"), kwargs.get("base_mqtt_topic_from_path"), kwargs.get("builder_instance")
        
        return FaderWithBarGraphFrame(parent_widget, config_data, config_data.get("path"), s_engine, s_router, b_topic, b_inst)

    def make_fader_bar_graph(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderFaderBarGraphCreator.make(parent_widget, config_data, context, **kwargs)
