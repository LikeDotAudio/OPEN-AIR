# meter_needle/meter_needle.py
# Modularized Needle VU Meter.
# Version 20260315.Modular.1

import time
import tkinter as tk
from loguru import logger

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True
from workers.logger.logger import builder_logger
from managers.configini.config_reader import Config
app_constants = Config.get_instance()

# --- Specialized Modules ---
from .config.meter_config import MeterConfig
from .ui.frame_factory import FrameFactory
from .animation.animator import MeterAnimator
from .integration.state_linker import StateLinker
from .core.rendering_engine import MeterRenderingEngine
from .core.visual_helpers import MeterVisualHelpers
from managers.Display.transparency.transparency_mixin import TransparencyMixin
from managers.Display.transparency.transparency import TransparencyManager
from managers.Display.factory.widget_registry import WidgetRegistry

class BuilderMeterNeedleCreator(TransparencyMixin):
    """Orchestrates the creation of a needle-style VU meter."""

    def make_meter_needle(self, parent_widget, config_data, context=None, **kwargs):
        if BUILDER_DEBUG: builder_logger.trace(f"🔬🏗️📶 [BUILDER] Creating MeterNeedle.")
        
        # 1. Config & Context
        config = MeterConfig(config_data)
        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = ctx.builder_instance if hasattr(ctx, 'builder_instance') else ctx.app_instance
        
        try:
            # 2. UI Setup
            frame = FrameFactory.create_frame(parent_widget, config)
            w, h, ox, oy = FrameFactory.calculate_dimensions(config)
            frame.pivot_offset_x, frame.pivot_offset_y = ox, oy
            canvas = FrameFactory.create_canvas(frame, w, h, config.canvas_bg)

            if hasattr(b_inst, '_apply_transparency'):
                TransparencyManager.apply_transparency(frame, frame, config_data, b_inst)
                TransparencyManager.apply_transparency(frame, canvas, config_data, b_inst)
                if hasattr(frame, 'lbl'): TransparencyManager.apply_transparency(frame.lbl, None, config_data, b_inst)

            # 3. Animation Logic
            def render_cb(full_redraw=False):
                now = time.time() * 1000; v1, v2 = frame.anim_current_value, (frame.anim_current_value_2 if config.meter_mode == "stereo" else None)
                if v1 >= config.red_zone_start or (v2 is not None and v2 >= config.red_zone_start):
                    frame.anim_peak_on, frame.anim_peak_expiry = True, now + config.peak_hold_ms
                elif now > frame.anim_peak_expiry: frame.anim_peak_on = False
                
                MeterRenderingEngine.render(canvas, config, v1, v2, frame.anim_peak_on, ox, oy, full_redraw=full_redraw)
            
            frame.render = lambda: render_cb(full_redraw=True)
            animator = MeterAnimator(frame, config, canvas, render_cb)
            canvas.tag_bind("peak_dot", "<Button-1>", animator.reset_peak)

            # 4. State Integration
            linker = StateLinker(ctx.state_mirror_engine, ctx.subscriber_router, config, base_topic_path=ctx.base_mqtt_topic_from_path)
            linker.setup_links(animator); frame.vu_value_var, frame.vu_value_var_2 = linker.vu_value_var, linker.vu_value_var_2

            render_cb(full_redraw=True)
            return frame

        except Exception as e:
            if BUILDER_DEBUG: builder_logger.exception(f"❌ Critical failure creating VU meter '{config.label}': {e}")
            return None

    def _draw_needle_vu_meter(self, *args, **kwargs): pass # Deprecated shim
