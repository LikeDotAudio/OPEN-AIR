# meter_needle/meter_needle.py
# Modularized Needle VU Meter.
# Version 20260315.Modular.1

import time
import tkinter as tk
from loguru import logger

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True
from oaLogging.Core.logger import builder_logger
from oaConfiguration.FileReaders.config_reader import Config
app_constants = Config.get_instance()

# --- Specialized Modules ---
from .config.meter_config import MeterConfig
from .ui.frame_factory import FrameFactory
from .animation.animator import MeterAnimator
from .integration.state_linker import StateLinker
from .Core.rendering_engine import MeterRenderingEngine
from .Core.visual_helpers import MeterVisualHelpers
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaGuiManager.Core.transparency.transparency import TransparencyManager
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

@WidgetRegistry.register("_NeedleVUMeter")
class BuilderMeterNeedleCreator(TransparencyMixin):
    """Orchestrates the creation of a needle-style VU meter."""

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """Static factory method for the registry."""
        return BuilderMeterNeedleCreator().make_meter_needle(
            parent_widget, config_data, context=context, **kwargs
        )

    def make_meter_needle(self, parent_widget, config_data, context=None, **kwargs):
        print("DEBUG: entering make_meter_needle")
        if BUILDER_DEBUG: builder_logger.trace(f"🔬🏗️📶 [BUILDER] Creating MeterNeedle.")
        
        # 1. Config & Context
        print("DEBUG: creating config")
        config = MeterConfig(config_data)
        ctx = context if context else type('obj', (object,), kwargs)()
        b_inst = ctx.builder_instance if hasattr(ctx, 'builder_instance') else ctx.app_instance
        
        try:
            # 2. UI Setup
            print("DEBUG: creating frame")
            frame = FrameFactory.create_frame(parent_widget, config)
            print("DEBUG: calculating dimensions")
            w, h, ox, oy = FrameFactory.calculate_dimensions(config)
            frame.pivot_offset_x, frame.pivot_offset_y = ox, oy
            print("DEBUG: creating canvas")
            canvas = FrameFactory.create_canvas(frame, w, h, config.canvas_bg)

            if hasattr(b_inst, '_apply_transparency'):
                print("DEBUG: applying transparency")
                TransparencyManager.apply_transparency(frame, frame, config_data, b_inst)
                TransparencyManager.apply_transparency(frame, canvas, config_data, b_inst)
                if hasattr(frame, 'lbl'): TransparencyManager.apply_transparency(frame.lbl, None, config_data, b_inst)

            # 3. Animation Logic
            def render_cb(full_redraw=False):
                try:
                    now = time.time() * 1000; v1, v2 = frame.anim_current_value, (frame.anim_current_value_2 if config.meter_mode == "stereo" else None)
                    if v1 >= config.red_zone_start or (v2 is not None and v2 >= config.red_zone_start):
                        frame.anim_peak_on, frame.anim_peak_expiry = True, now + config.peak_hold_ms
                    elif now > frame.anim_peak_expiry: frame.anim_peak_on = False
                    
                    # Wrap rendering in try-except to catch potential TclError (e.g., tagOrId not found)
                    MeterRenderingEngine.render(canvas, config, v1, v2, frame.anim_peak_on, ox, oy, full_redraw=full_redraw)
                except tk.TclError as e:
                    # Log the error, but don't let it crash the application or tests
                    builder_logger.warning(f"TclError during meter rendering for '{config.label}': {e}. This might be due to missing tags or canvas items.")
                except Exception as e:
                    builder_logger.exception(f"Unexpected error during meter rendering for '{config.label}': {e}")

            
            frame.render = lambda: render_cb(full_redraw=True)
            print("DEBUG: creating animator")
            animator = MeterAnimator(frame, config, canvas, render_cb)
            canvas.tag_bind("peak_dot", "<Button-1>", animator.reset_peak)

            # 4. State Integration
            print("DEBUG: creating linker")
            linker = StateLinker(ctx.state_mirror_engine, ctx.subscriber_router, config, base_topic_path=ctx.base_mqtt_topic_from_path, master=frame)
            print("DEBUG: setting up links")
            linker.setup_links(animator); frame.vu_value_var, frame.vu_value_var_2 = linker.vu_value_var, linker.vu_value_var_2

            print("DEBUG: initial render")
            render_cb(full_redraw=True)
            print("DEBUG: returning frame")
            return frame

        except Exception as e:
            if BUILDER_DEBUG: builder_logger.exception(f"❌ Critical failure creating VU meter '{config.label}': {e}")
            return None

    def _draw_needle_vu_meter(self, *args, **kwargs): pass # Deprecated shim
