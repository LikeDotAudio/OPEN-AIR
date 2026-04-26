# fader_horizontal/fader_horizontal.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Modularized Horizontal Fader.

import tkinter as tk

# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaGuiBuilder.Core.base_widget_creator import BaseWidgetCreator

# --- EXTRACTED CORE MODULES ---
from oaGuiElements.Core.faders.fader_horizontal.Core.horizontal_fader_renderer_mixin import HorizontalFaderRendererMixin
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry
from oaGuiManager.Core.transparency.transparency import TransparencyManager
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

from .horizontal_fader_interaction_mixin import HorizontalFaderInteractionMixin


class CustomHorizontalFaderFrame(
    tk.Frame,
    HorizontalFaderRendererMixin,
    HorizontalFaderInteractionMixin
):
    def __init__(self, master, variable, config, path, state_mirror_engine):
        super().__init__(master, bd=0, highlightthickness=0)

        self.variable, self.path, self.config_data, self.state_mirror_engine = variable, path, config, state_mirror_engine

        # 1. Config
        self.min_val = float(config.get("min", config.get("value_min", 0.0)))
        self.max_val = float(config.get("max", config.get("value_max", 100.0)))
        self.log_exponent = float(config.get("log_exponent", 1.0))
        self.reff_point = float(config.get("reff_point", (self.min_val + self.max_val) / 2.0))

        self.width = float(config.get("width", config.get("layout", {}).get("width", 200)))
        self.height = float(config.get("height", config.get("layout", {}).get("height", 100)))
        self.track_hover_color = "#444444"

        # 2. State
        self.is_sliding = self.is_locked = self.is_hovered = False
        self._resize_timer = self.temp_entry = None

        # 3. Canvas
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=self.cget("bg"), width=int(self.width), height=int(self.height))
        self.canvas.pack(fill="both", expand=True)

        # 4. Bindings
        self.variable.trace_add("write", self._update_positions)
        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Button-1>", self._start_sliding)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._stop_sliding)
        self.canvas.bind("<Button-2>", self._jump_to_reff_point)
        self.canvas.bind("<Alt-Button-1>", self._open_manual_entry)
        self.canvas.bind("<Enter>", lambda e: self._update_hover_state(True))
        self.canvas.bind("<Leave>", lambda e: self._update_hover_state(False))
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

        self.after(50, self.render)

    def _on_configure(self, event):
        if self._resize_timer: self.after_cancel(self._resize_timer)
        if event.width > 1: self._resize_timer = self.after(100, self.render)

    def _update_hover_state(self, h):
        self.is_hovered = h
        if self.canvas.find_withtag("track_slot"): self.canvas.itemconfig("track_slot", fill=self.track_hover_color if h else "#050505")

    def _draw(self): self.render()

@WidgetRegistry.register("_CustomHorizontalFader")
class BuilderFaderHorizontalCreator(BaseWidgetCreator, TransparencyMixin):

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Assembles the Horizontal Fader UI."""
        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = getattr(ctx, 'builder_instance', None) or getattr(ctx, 'app_instance', None) or kwargs.get('builder_instance')

        val_var = tk.DoubleVar(master=parent_widget, value=float(config_data.get("value_default", config_data.get("value", 50.0))))
        frame = CustomHorizontalFaderFrame(parent_widget, val_var, config_data, config_data.get("path"), getattr(ctx, 'state_mirror_engine', None) or kwargs.get('state_mirror_engine'))

        if hasattr(b_inst, '_apply_transparency'):
            TransparencyManager.apply_transparency(frame, frame.canvas, config_data, b_inst)
            TransparencyManager.apply_transparency(frame, frame, config_data, b_inst)

        path = config_data.get("path")
        s_engine = getattr(ctx, 'state_mirror_engine', None) or kwargs.get('state_mirror_engine')
        if path and s_engine:
            b_topic = getattr(ctx, 'base_mqtt_topic_from_path', None) or kwargs.get('base_mqtt_topic_from_path', "")
            topic = s_engine.register_widget(path, val_var, b_topic, config_data, instance=frame)
            if getattr(ctx, 'subscriber_router', None) and topic:
                ctx.subscriber_router.subscribe_to_topic(topic, s_engine.sync_incoming_mqtt_to_gui)
            s_engine.initialize_widget_state(path)

        return frame, frame.canvas

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        return BuilderFaderHorizontalCreator.build(parent_widget, config_data, context, **kwargs)

    def make_fader_horizontal(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderFaderHorizontalCreator.build(parent_widget, config_data, context, **kwargs)
