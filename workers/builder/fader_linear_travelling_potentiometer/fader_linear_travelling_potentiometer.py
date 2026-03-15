# fader_linear_travelling_potentiometer/fader_linear_travelling_potentiometer.py
# Modularized Linear Travelling Potentiometer (LTP).
# Version 20260315.Modular.1

import tkinter as tk
from tkinter import ttk
from loguru import logger

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True
from workers.logger.logger import builder_logger
from managers.configini.config_reader import Config
app_constants = Config.get_instance()

from workers.styling.style import THEMES, DEFAULT_THEME
from managers.Display.transparency.transparency_mixin import TransparencyMixin
from managers.Display.transparency.transparency_manager import TransparencyManager
from managers.Display.factory.widget_registry import WidgetRegistry

# --- EXTRACTED CORE MODULES ---
from .core.ltp_renderer_mixin import LTPRendererMixin
from .core.ltp_interaction_mixin import LTPInteractionMixin

DEFAULT_LTP_WIDTH = 100
DEFAULT_MIN_VAL = 0.0
DEFAULT_MAX_VAL = 100.0
DEFAULT_LOG_EXPONENT = 1.0
ROTATION_MIN = -100.0
ROTATION_MAX = 100.0

class CustomLTPFrame(tk.Frame, LTPRendererMixin, LTPInteractionMixin):
    def __init__(self, master, config, path, state_mirror_engine, subscriber_router, base_mqtt_topic):
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        f_cfg, k_cfg, s_cfg = config.get("fader_config", config), config.get("knob_config", config), config.get("style", config)
        
        # 1. Initialization
        super().__init__(master, bd=int(s_cfg.get("border_width", 0)), relief="solid", highlightthickness=int(s_cfg.get("border_width", 0)))
        
        self.path, self.state_mirror_engine, self.base_mqtt_topic = path, state_mirror_engine, base_mqtt_topic
        self.widget_config, self.orientation = config, "vertical"
        
        # 2. Parameters
        self.min_val = float(f_cfg.get("value_min", DEFAULT_MIN_VAL))
        self.max_val = float(f_cfg.get("value_max", DEFAULT_MAX_VAL))
        self.log_exponent = float(f_cfg.get("log_exponent", DEFAULT_LOG_EXPONENT))
        self.value_highlight_color = f_cfg.get("value_highlight_color", colors.get("accent"))
        self.show_value, self.show_units, self.unit_text = bool(f_cfg.get("show_value", True)), bool(f_cfg.get("show_units", False)), f_cfg.get("unit_text", "")
        
        self.rotation_min = float(k_cfg.get("rotation_min", ROTATION_MIN))
        self.rotation_max = float(k_cfg.get("rotation_max", ROTATION_MAX))
        self.cap_radius, self.cap_color, self.cap_outline_color = int(k_cfg.get("cap_radius", 18)), k_cfg.get("cap_color", "#dcdcdc"), k_cfg.get("cap_outline_color", "#444444")
        self.freestyle = k_cfg.get("freestyle", False)
        
        self.knob_shape, self.knob_teeth, self.pointer_style = s_cfg.get("knob_shape", "circle"), int(s_cfg.get("knob_teeth", 12)), s_cfg.get("pointer_style", "line")
        self.tick_size, self.tick_color, self.track_hover_color = float(s_cfg.get("tick_size", 0.35)), s_cfg.get("tick_color", "light grey"), s_cfg.get("track_hover_color", "#444")
        self.accent_color, self.value_color = colors.get("accent"), colors.get("accent")

        # 3. State
        self.linear_var = tk.DoubleVar(value=float(f_cfg.get("value_default", 0.0)))
        self.rotation_var = tk.DoubleVar(value=float(k_cfg.get("rotation_default", 0.0)))
        self.is_sliding, self.is_hovered = False, False
        self._setup_drag_state()

        # 4. Canvas & Bindings
        self.canvas = tk.Canvas(self, bg=colors.get("bg"), highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<Button-1>", lambda e: self.on_press(e, self.canvas))
        self.canvas.bind("<B1-Motion>", lambda e: self.on_drag(e, self.canvas))
        self.canvas.bind("<ButtonRelease-1>", lambda e: setattr(self, 'is_sliding', False))
        self.canvas.bind("<Configure>", lambda e: self.redraw(self.canvas))
        
        self.linear_var.trace_add("write", lambda *a: self.redraw(self.canvas))
        self.rotation_var.trace_add("write", lambda *a: self.redraw(self.canvas))

    def _draw(self): self.redraw(self.canvas) # External sync entry

@WidgetRegistry.register("_CustomLTP")
class BuilderFaderLinearTravellingPotentiometerCreator(TransparencyMixin):
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        ctx = context if context else type('obj', (object,), kwargs)()
        frame = CustomLTPFrame(parent_widget, config_data, config_data.get("path"), ctx.state_mirror_engine, None, ctx.subscriber_router)
        
        if hasattr(ctx.builder_instance, '_apply_transparency'):
            TransparencyManager.apply_transparency(frame, frame.canvas, config_data, ctx.builder_instance)
        
        if frame.path and ctx.state_mirror_engine:
            lin_cfg = {**config_data, **config_data.get("fader_config", {})}
            ctx.state_mirror_engine.register_widget(frame.path, frame.linear_var, ctx.base_mqtt_topic_from_path, lin_cfg)
            
            rot_path = f"{frame.path}.rotation"
            rot_cfg = {**config_data, **config_data.get("knob_config", {}), "path": rot_path, "value_min": frame.rotation_min, "value_max": frame.rotation_max}
            ctx.state_mirror_engine.register_widget(rot_path, frame.rotation_var, ctx.base_mqtt_topic_from_path, rot_cfg)
            
            ctx.state_mirror_engine.initialize_widget_state(frame.path)
            ctx.state_mirror_engine.initialize_widget_state(rot_path)

        return frame

    def make_fader_linear_travelling_potentiometer(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderFaderLinearTravellingPotentiometerCreator.make(parent_widget, config_data, context, builder_instance=self, **kwargs)
