# fader/fader.py
# Modularized Vertical Fader Widget.
# Version 20260315.Modular.1

import tkinter as tk
from tkinter import ttk
import sys
import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from workers.logger.logger import builder_logger
from loguru import logger
from managers.configini.config_reader import Config
app_constants = Config.get_instance()

from workers.styling.style import THEMES, DEFAULT_THEME
from managers.Display.transparency.transparency_mixin import TransparencyMixin
from managers.Display.transparency.transparency_manager import TransparencyManager
from managers.Display.factory.widget_registry import WidgetRegistry

# --- EXTRACTED CORE MODULES ---
from .core.fader_interaction_mixin import FaderInteractionMixin
from .core.fader_renderer_mixin import FaderRendererMixin
from .core.fader_state_mixin import FaderStateMixin

class CustomFaderFrame(
    tk.Frame, 
    FaderInteractionMixin, 
    FaderRendererMixin, 
    FaderStateMixin
):
    """Refactored Fader frame inheriting interaction, rendering, and state logic via mixins."""
    
    def __init__(self, master, variable, config, path, state_mirror_engine, sync_callback):
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        f_style = colors.get("fader_style", {})
        
        self.bg_color = colors.get("bg", "#2b2b2b")
        self.accent_color = colors.get("accent", "#33A1FD")
        self.track_col = colors.get("secondary", "#444444")
        self.handle_col = colors.get("fg", "#dcdcdc")

        # 1. Config Parameters
        self.min_val = float(config.get("value_min", -100.0))
        self.max_val = float(config.get("value_max", 0.0))
        self.log_exponent = float(config.get("log_exponent", 1.0))
        self.reff_point = float(config.get("reff_point", (self.min_val + self.max_val) / 2.0))
        
        self.show_value = bool(config.get("show_value", True))
        self.show_units = bool(config.get("show_units", False))
        self.label_color = config.get("label_color", "white")
        self.label_text = config.get("label_active", "")
        self.unit_text, self.unit_position = config.get("unit_text", ""), config.get("unit_position", "right") 
        
        self.tick_size = float(config.get("tick_size", f_style.get("tick_size", 0.35)))
        self.fader_track_color = config.get("fader_track_color", config.get("fader_colour", self.track_col))
        self.track_hover_color = config.get("track_hover_color", "#444444") 
        self.cap_color = config.get("cap_color", config.get("cap", self.handle_col))
        self.cap_highlight_color = config.get("cap_highlight_color", config.get("cap_highlights", None))
        self.value_highlight_color = config.get("value_highlight_color", f_style.get("value_highlight_color", "#f4902c"))
        
        self.cap_width_override = config.get("cap_width")
        self.cap_height_override = config.get("cap_height")
        self.fader_cap_scale = float(config.get("fader_cap_scale", 1.0))

        # 2. State Setup
        self.is_sliding = self.is_locked = self.is_hovered = False
        self.temp_entry = None
        self.variable = variable
        self.path = path
        self.state_mirror_engine = state_mirror_engine
        self.sync_callback = sync_callback

        super().__init__(
            master, bd=int(config.get("border_width", 0)), relief="solid", 
            highlightbackground=config.get("border_color", "black"), 
            highlightthickness=int(config.get("border_width", 0)), bg=self.bg_color
        )

@WidgetRegistry.register("_Fader", "_SmartFader", "_CustomFader")
class BuilderFaderCreator(TransparencyMixin):
    
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        if LOCAL_DEBUG: logger.trace(f"🔬 BuilderFaderCreator.make: {config_data.get('path')}")
        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = ctx.builder_instance if hasattr(ctx, 'builder_instance') else ctx.app_instance
        
        path = config_data.get("path")
        val_var = tk.DoubleVar(value=float(config_data.get("value_default", 75.0)))

        frame = CustomFaderFrame(parent_widget, val_var, config_data, path, ctx.state_mirror_engine, None)

        try:
            l_cfg = config_data.get("layout", {})
            w, h = float(config_data.get("width", l_cfg.get("width", 100))), float(config_data.get("height", l_cfg.get("height", 250)))

            canvas = tk.Canvas(frame, width=int(w), height=int(h), highlightthickness=0, bd=0, relief="flat", bg=frame.bg_color)
            canvas.pack(fill=tk.BOTH, expand=True)
            frame.canvas = canvas # Inject canvas ref
            
            if hasattr(b_inst, '_apply_transparency'): TransparencyManager.apply_transparency(frame, canvas, config_data, b_inst)

            # 3. Dynamic Handlers
            def _sync_pos(*a):
                if not canvas.winfo_exists(): return
                cw, ch = float(canvas.winfo_width()), float(canvas.winfo_height())
                frame._sync_fader_cap_position(cw if cw>1 else w, ch if ch>1 else h, val_var.get())

            frame.sync_callback = _sync_pos

            def _schedule_redraw(e=None):
                if getattr(frame, "_resize_timer", None): canvas.after_cancel(frame._resize_timer)
                cw, ch = float(canvas.winfo_width()), float(canvas.winfo_height())
                frame._resize_timer = canvas.after(100, lambda: frame._draw_fader(cw if cw>1 else w, ch if ch>1 else h, val_var.get()))

            frame._draw = _schedule_redraw
            val_var.trace_add("write", _sync_pos)

            # 4. Canvas Bindings
            canvas.bind("<Enter>", lambda e: frame._update_hover_state(True))
            canvas.bind("<Leave>", lambda e: frame._update_hover_state(False))
            canvas.bind("<MouseWheel>", frame._on_mousewheel)
            canvas.bind("<Button-4>", frame._on_mousewheel)
            canvas.bind("<Button-5>", frame._on_mousewheel)

            canvas.bind("<Button-1>", frame._start_interaction)
            canvas.bind("<B1-Motion>", frame._on_drag)
            canvas.bind("<ButtonRelease-1>", frame._stop_interaction)
            canvas.bind("<Button-2>", frame._jump_to_reff_point)
            canvas.bind("<Alt-Button-1>", frame._open_manual_entry)
            canvas.bind("<Configure>", _schedule_redraw)

            # 5. State Setup
            if path and ctx.state_mirror_engine:
                rc = {**config_data, "value_min": frame.min_val, "value_max": frame.max_val}
                topic = ctx.state_mirror_engine.register_widget(path, val_var, ctx.base_mqtt_topic_from_path, rc, instance=frame)
                if ctx.subscriber_router and topic: ctx.subscriber_router.subscribe_to_topic(topic, ctx.state_mirror_engine.sync_incoming_mqtt_to_gui)
                ctx.state_mirror_engine.initialize_widget_state(path)

            canvas.after(50, lambda: frame._draw_fader(w, h, val_var.get()))
            return frame
        except Exception as e:
            logger.exception("🎚️❌ Error creating custom fader")
            return None

    def make_fader(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderFaderCreator.make(parent_widget, config_data, context, builder_instance=self, **kwargs)
