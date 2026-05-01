# fader_dual/fader_dual.py

# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized High-performance Dual Fader Widget.
import tkinter as tk

from oaConfigurationManager.FileReaders.config_reader import Config
from oaGui.Methods.i18n_utils import get_text

# --- Standard Debug Logging Setup ---

app_constants = Config.get_instance()

from oaGui.Core.base_widget_creator import BaseWidgetCreator
from oaGui.Hooks.widget_registry import WidgetRegistry
from oaGui.Workers.transparency.transparency import TransparencyManager
from oaGui.Workers.transparency.transparency_mixin import TransparencyMixin
from oaStyle.Core.style import DEFAULT_THEME, THEMES

from .dual_fader_interaction_mixin import DualFaderInteractionMixin

# --- EXTRACTED CORE MODULES ---
from .dual_fader_renderer_mixin import DualFaderRendererMixin


class CustomDualFaderFrame(tk.Frame, DualFaderRendererMixin, DualFaderInteractionMixin):
    """A dual-handle slider with synchronized readout tags."""

    def __init__(self, master, config, path, state_mirror_engine, base_mqtt_topic, subscriber_router, orientation="horizontal"):
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        super().__init__(master, bd=0, highlightthickness=0, bg=colors.get("bg", "#2b2b2b"))

        self.orientation = str(orientation).lower()
        self.min_val, self.max_val = float(config.get("value_min", 0.0)), float(config.get("value_max", 100.0))
        self.log_exponent = float(config.get("log_exponent", 1.0))
        self.label_active = get_text(config.get("label_active"), "")
        self.value_highlight_color = colors.get("accent", "#f4902c")

        self.cap_width = int(float(config.get("cap_width", 30)))
        self.cap_height_ratio = float(config.get("cap_height_ratio", 0.6))
        self.cap_color = config.get("cap_color", colors.get("fg", "#dcdcdc"))

        self.path, self.state_mirror_engine, self.config_data = path, state_mirror_engine, config
        self.v1_var = tk.DoubleVar(value=float(config.get("value_default_v1", 50)))
        self.v2_var = tk.DoubleVar(value=float(config.get("value_default_v2", 50)))
        self.delta_var = tk.DoubleVar(value=0.0)

        l_cfg = config.get("layout", {})
        self.width = float(config.get("width", l_cfg.get("width", 100 if self.orientation == "vertical" else 250)))
        self.height = float(config.get("height", l_cfg.get("height", 250 if self.orientation == "vertical" else 100)))

        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=self.cget("bg"), width=int(self.width), height=int(self.height))
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.v1_var.trace_add("write", self._sync_positions)
        self.v2_var.trace_add("write", self._sync_positions)

        self._resize_timer, self.active_fader = None, None
        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", lambda e: setattr(self, 'active_fader', None))

        self.after(50, self.render)

    def _on_configure(self, event):
        if self._resize_timer: self.after_cancel(self._resize_timer)
        if self.canvas.winfo_width() > 1: self._resize_timer = self.after(100, self.render)

    def render(self): self._draw_fader()
    def _draw(self): self.render()

@WidgetRegistry.register("_CustomDualHorizontalFader", "_CustomDualVerticalFader")
class BuilderFaderDualCreator(BaseWidgetCreator, TransparencyMixin):

    is_composite = True

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Assembles the Dual Fader UI."""
        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = getattr(ctx, 'builder_instance', None) or getattr(ctx, 'app_instance', None) or kwargs.get('builder_instance')

        path = config_data.get("path")
        orientation = "vertical" if "_CustomDualVerticalFader" in config_data.get("type", "") else "horizontal"

        s_engine = getattr(ctx, 'state_mirror_engine', None) or kwargs.get('state_mirror_engine')
        b_topic = getattr(ctx, 'base_mqtt_topic_from_path', None) or kwargs.get('base_mqtt_topic_from_path', "")
        s_router = getattr(ctx, 'subscriber_router', None) or kwargs.get('subscriber_router')

        frame = CustomDualFaderFrame(parent_widget, config_data, path, s_engine, b_topic, s_router, orientation)

        if hasattr(b_inst, '_apply_transparency'):
            TransparencyManager.apply_transparency(frame, frame.canvas, config_data, b_inst)

        if path and s_engine:
            for v_id, var in [("V1", frame.v1_var), ("V2", frame.v2_var)]:
                v_path = f"{path}/{v_id}"
                topic = s_engine.register_widget(v_path, var, b_topic, config_data)
                if s_router and topic:
                    s_router.subscribe_to_topic(topic, s_engine.sync_incoming_mqtt_to_gui)
                s_engine.initialize_widget_state(v_path)

        return frame, frame.canvas

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        return BuilderFaderDualCreator.build(parent_widget, config_data, context, **kwargs)

    def make_fader_dual(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderFaderDualCreator.build(parent_widget, config_data, context, **kwargs)
