# fader_linear_travelling_potentiometer/fader_linear_travelling_potentiometer.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized Linear Travelling Potentiometer (LTP).

import tkinter as tk

# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaGuiBuilder.Core.base_widget_creator import BaseWidgetCreator
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry
from oaGuiManager.Core.transparency.transparency import TransparencyManager
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaStyle.Core.style import DEFAULT_THEME, THEMES

from .ltp_interaction_mixin import LTPInteractionMixin

# --- EXTRACTED CORE MODULES ---
from .ltp_renderer_mixin import LTPRendererMixin

DEFAULT_LTP_WIDTH = 100
DEFAULT_MIN_VAL = 0.0
DEFAULT_MAX_VAL = 100.0
DEFAULT_LOG_EXPONENT = 1.0
ROTATION_MIN = -100.0
ROTATION_MAX = 100.0

class CustomLTPFrame(tk.Frame, LTPRendererMixin, LTPInteractionMixin):
    def __init__(self, master, config, path, state_mirror_engine, subscriber_router, base_mqtt_topic, **kwargs):
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
        self.arc_width = int(s_cfg.get("arc_width", 5))
        self.pointer_length = s_cfg.get("pointer_length", None)
        self.pointer_offset = int(s_cfg.get("pointer_offset", 0))
        self.no_center = s_cfg.get("no_center", False)

        self.tick_size, self.tick_color, self.track_hover_color = float(s_cfg.get("tick_size", 0.35)), s_cfg.get("tick_color", "light grey"), s_cfg.get("track_hover_color", "#444")
        self.tick_thickness = int(s_cfg.get("tick_thickness", 1))
        self.tick_font = ("Arial", 7)
        self.tick_label_position = s_cfg.get("tick_label_position", "both")
        self.custom_ticks = s_cfg.get("custom_ticks", None)
        self.tick_interval = s_cfg.get("tick_interval", None)
        self.tick_color = s_cfg.get("tick_color", "light grey")
        self.accent_color, self.value_color = colors.get("accent"), colors.get("accent")

        # 3. State
        self.linear_var = kwargs.get("linear_variable") or tk.DoubleVar(master=master, value=float(f_cfg.get("value_default", 0.0)))
        self.rotation_var = kwargs.get("rotation_variable") or tk.DoubleVar(master=master, value=float(k_cfg.get("rotation_default", 0.0)))
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

@WidgetRegistry.register("_CustomLTP")
class BuilderFaderLinearTravellingPotentiometerCreator(BaseWidgetCreator, TransparencyMixin):

    is_composite = True

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Assembles the LTP UI."""
        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = getattr(ctx, 'builder_instance', None) or getattr(ctx, 'app_instance', None) or kwargs.get('builder_instance')

        path = config_data.get("path")
        s_engine = getattr(ctx, 'state_mirror_engine', None) or kwargs.get('state_mirror_engine')
        b_topic = getattr(ctx, 'base_mqtt_topic_from_path', None) or kwargs.get('base_mqtt_topic_from_path', "")
        s_router = getattr(ctx, 'subscriber_router', None) or kwargs.get('subscriber_router')

        frame = CustomLTPFrame(
            parent_widget, config_data, path, s_engine, s_router, b_topic, **kwargs
        )

        if hasattr(b_inst, '_apply_transparency'):
            TransparencyManager.apply_transparency(frame, frame.canvas, config_data, b_inst)

        if path and s_engine:
            lin_cfg = {**config_data, **config_data.get("fader_config", {})}
            s_engine.register_widget(path, frame.linear_var, b_topic, lin_cfg)

            rot_path = f"{path}.rotation"
            rot_cfg = {
                **config_data,
                **config_data.get("knob_config", {}),
                "path": rot_path,
                "value_min": frame.rotation_min,
                "value_max": frame.rotation_max
            }
            s_engine.register_widget(rot_path, frame.rotation_var, b_topic, rot_cfg)

            s_engine.initialize_widget_state(path)
            s_engine.initialize_widget_state(rot_path)

        return frame, frame.canvas

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        return BuilderFaderLinearTravellingPotentiometerCreator.build(parent_widget, config_data, context, **kwargs)

    def make_fader_linear_travelling_potentiometer(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderFaderLinearTravellingPotentiometerCreator.build(parent_widget, config_data, context, **kwargs)
