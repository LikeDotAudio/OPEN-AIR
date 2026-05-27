# fader_linear_travelling_potentiometer/fader_linear_travelling_potentiometer.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized Linear Travelling Potentiometer (LTP).

import tkinter as tk

# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaGui.Core.factory.base_widget_creator import BaseWidgetCreator
from oaGui.Hooks.registry.registry_widget_store import RegistryWidgetStore
from oaGui.Workers.compositing.engine_visual_effects import EngineVisualEffects
from oaGui.Workers.compositing.sync_behavior import SyncBehavior
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

        # 2. Parameters — pillar reads, matching frontEnd/libControl/faders/LTPFader/LTPFader.jsx.
        #   domain.{min,max}, value.default_value, readout.{show_value,show_units},
        #   cosmetics.colors.highlight all live INSIDE fader_config (not at top level).
        #   Note: the JsonSchemaNormalizer's LEXICON renames "value" -> "value_default"
        #   recursively, so the value pillar may show up under either key.
        fc_domain = f_cfg.get("domain") if isinstance(f_cfg.get("domain"), dict) else {}
        fc_readout = f_cfg.get("readout") if isinstance(f_cfg.get("readout"), dict) else {}
        fc_cosmetics = f_cfg.get("cosmetics") if isinstance(f_cfg.get("cosmetics"), dict) else {}
        fc_colors = fc_cosmetics.get("colors") if isinstance(fc_cosmetics.get("colors"), dict) else {}

        self.min_val = float(fc_domain.get("min", f_cfg.get("value_min", config.get("min", DEFAULT_MIN_VAL))))
        self.max_val = float(fc_domain.get("max", f_cfg.get("value_max", config.get("max", DEFAULT_MAX_VAL))))
        self.log_exponent = float(f_cfg.get("log_exponent", DEFAULT_LOG_EXPONENT))
        rail_highlight = fc_colors.get("highlight")
        self.value_highlight_color = f_cfg.get("value_highlight_color", rail_highlight or colors.get("accent"))
        self.show_value = bool(fc_readout.get("show_value", f_cfg.get("show_value", True)))
        self.show_units = bool(fc_readout.get("show_units", f_cfg.get("show_units", False)))
        self.unit_text = f_cfg.get("unit_text", "")

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

        # 3. State — linear default mirrors LTPFader.jsx:
        #   defaultVal = fc.value.default_value ?? (min + max) / 2
        # The value pillar may be a dict (`{default_value: -10.0}`) or a scalar
        # shorthand (`-10.0`). Accept both, and resolve under either key name
        # since LEXICON renames "value" -> "value_default".
        val_pillar = f_cfg.get("value", f_cfg.get("value_default"))
        if isinstance(val_pillar, dict):
            linear_default = float(val_pillar.get("default_value", val_pillar.get("default", (self.min_val + self.max_val) / 2)))
        elif isinstance(val_pillar, (int, float)):
            linear_default = float(val_pillar)
        else:
            linear_default = (self.min_val + self.max_val) / 2
        self.linear_var = kwargs.get("linear_variable") or tk.DoubleVar(master=master, value=linear_default)
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

@RegistryWidgetStore.register("_CustomLTP")
class BuilderFaderLinearTravellingPotentiometerCreator(BaseWidgetCreator, SyncBehavior):

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
            EngineVisualEffects.apply_transparency(frame, frame.canvas, config_data, b_inst)

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
