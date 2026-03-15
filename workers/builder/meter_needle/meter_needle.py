import time
import math
import tkinter as tk

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

# New Modules
from workers.builder.meter_needle.config.meter_config import MeterConfig
from workers.builder.meter_needle.ui.frame_factory import FrameFactory
from workers.builder.meter_needle.animation.animator import MeterAnimator
from workers.builder.meter_needle.integration.state_linker import StateLinker
from workers.builder.meter_needle.constants import (
    SCALE_TICK_LENGTH, SCALE_SUB_TICK_LENGTH, SCALE_TEXT_OFFSET, NUMBER_FONT_FAMILY
)

# Core Drawing Logic
from workers.builder.meter_needle.meter_modifyer import MeterModifier
from workers.builder.meter_needle.cosmetics.geometry import BezelGeometry
from workers.builder.meter_needle.core.scale import ScaleDrawer
from workers.builder.meter_needle.core.number import NumberDrawer
from workers.builder.meter_needle.core.needle import NeedleDrawer
from workers.builder.meter_needle.core.shadow import ShadowDrawer
from workers.builder.meter_needle.core.peak import PeakDrawer
from workers.builder.meter_needle.core.pivot import PivotDrawer
from workers.builder.panels.panel_generator import PanelGenerator
from managers.Display.transparency.transparency_mixin import TransparencyMixin

class BuilderMeterNeedleCreator(TransparencyMixin):
    """
    Orchestrates the creation of a needle-style VU meter.
    Delegates responsibilities to specialized modules for config, UI, animation, and state.
    """

    def make_meter_needle(self, parent_widget, config_data, context=None, **kwargs):
        """Orchestrates the creation of a needle-style VU meter."""
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️📶 [BUILDER] Entering make_meter_needle")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        current_function_name = "make_meter_needle"
        
        # 1. Configuration
        if BUILDER_DEBUG: builder_logger.trace("🎨📐⚙️ [CONFIG] Parsing MeterConfig object...")
        config = MeterConfig(config_data)
        
        # ⚡ HARDENED INTERFACE: Extract from context if available
        if BUILDER_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            app_instance = context.app_instance
            builder_instance = context.builder_instance or app_instance
            if BUILDER_DEBUG: builder_logger.debug("✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.")
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance")
            app_instance = kwargs.get("app_instance")
            if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to self/kwargs.")

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️📶 [BUILDER] Spawning needle VU meter for '{config.label}'.")

        try:
            # 2. UI Construction
            if BUILDER_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [CONSTRUCT] Creating frame via FrameFactory for '{config.label}'")
            frame = FrameFactory.create_frame(parent_widget, config)
            
            # Calculate dynamic geometry
            if BUILDER_DEBUG: builder_logger.trace("📐📏🔳 [LAYOUT] Calculating dimensions and pivot offsets...")
            total_width, total_height, offset_x, offset_y = FrameFactory.calculate_dimensions(config)
            if BUILDER_DEBUG: builder_logger.debug(f"📏📐🔳 [DIM] Meter dimensions: {total_width}x{total_height}, Offsets: ({offset_x}, {offset_y})")
            
            # Store offsets for composite widgets
            frame.pivot_offset_x = offset_x
            frame.pivot_offset_y = offset_y
            
            if BUILDER_DEBUG: builder_logger.trace("🏗️🪟🖼️ [CONSTRUCT] Creating canvas for needle meter drawing.")
            canvas = FrameFactory.create_canvas(frame, total_width, total_height, config.canvas_bg)

            # Apply Industrial Transparency to both frame and canvas
            if hasattr(builder_instance, '_apply_transparency'):
                if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to meter components for '{config.label}'")
                builder_instance._apply_transparency(frame, frame, config_data, builder_instance)
                builder_instance._apply_transparency(frame, canvas, config_data, builder_instance)
                if hasattr(frame, 'lbl'):
                    builder_instance._apply_transparency(frame.lbl, None, config_data, builder_instance)

            # 3. Animation & Rendering
            # Define the render callback that the animator will invoke
            def render_callback(full_redraw=False):
                # Check for peak state
                now_ms = time.time() * 1000
                val1 = frame.anim_current_value
                val2 = frame.anim_current_value_2 if config.meter_mode == "stereo" else None
                
                if val1 >= config.red_zone_start or (val2 is not None and val2 >= config.red_zone_start):
                    frame.anim_peak_on = True
                    frame.anim_peak_expiry = now_ms + config.peak_hold_ms
                elif now_ms > frame.anim_peak_expiry:
                    frame.anim_peak_on = False

                if BUILDER_DEBUG and full_redraw: builder_logger.trace(f"🔄✨🎨 [REDRAW] Executing FULL render for meter '{config.label}'")
                # Call static method explicitly
                BuilderMeterNeedleCreator._render_meter_components(
                    canvas, config, 
                    frame.anim_current_value, 
                    frame.anim_current_value_2, 
                    frame.anim_peak_on,
                    offset_x, offset_y,
                    full_redraw=full_redraw
                )
            
            # Set the render hook for transparency reslicing
            frame.render = lambda: render_callback(full_redraw=True)

            if BUILDER_DEBUG: builder_logger.trace(f"🌀⏳🌀 [ANIM] Initializing MeterAnimator for '{config.label}'")
            animator = MeterAnimator(frame, config, canvas, render_callback)
            
            # Bind peak reset
            canvas.tag_bind("peak_dot", "<Button-1>", animator.reset_peak)

            # 4. State Integration
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [STATE] Linking meter state to engine for '{config.label}'")
            linker = StateLinker(
                state_mirror_engine, 
                subscriber_router, 
                config, 
                base_topic_path=base_mqtt_topic_from_path
            )
            linker.setup_links(animator)
            
            # Expose variables on the frame for programmatic access
            frame.vu_value_var = linker.vu_value_var
            frame.vu_value_var_2 = linker.vu_value_var_2

            # Initial Draw - MUST be full redraw
            render_callback(full_redraw=True)

            if BUILDER_DEBUG: builder_logger.success(f"✅🆗📶 [SUCCESS] The themed needle VU meter '{config.label}' has materialized!")

            return frame

        except Exception as e:
            if BUILDER_DEBUG:
                builder_logger.exception(f"❌🚫🛑 [ERROR] Critical failure creating needle VU meter '{config.label}'")
            return None

    @staticmethod
    def _render_meter_components(canvas, config, val1, val2, peak_on, center_x, center_y, full_redraw=False):
        """
        Renders the visual components of the meter onto the canvas.
        OPTIMIZED: Separates static drawing from dynamic needle updates.
        """
        if BUILDER_DEBUG and full_redraw: builder_logger.trace(f"🔄🎨🔤 [REDRAW] Starting full component render for '{config.label}'")
        
        # ⚡ OPTIMIZATION: Only clear static elements on full redraw
        if full_redraw:
            if BUILDER_DEBUG: builder_logger.trace("❌🧹🎨 [REDRAW] Purging static elements from canvas.")
            canvas.delete("vu_static")
            canvas.delete("nextgen_background")
            canvas.delete("nextgen_foreground") 
            canvas.delete("industrial_text")

        # 1. Check for Custom Bezel
        style_overrides = config.cosmetics.get("style_overrides", {})
        has_custom_bezel = "bezel_shape" in style_overrides
        bezel_shape = style_overrides.get("bezel_shape", "").lower()
        bezel_width = int(style_overrides.get("bezel_width", 12))

        # Apply pivot offsets from config
        cx1 = center_x + config.pivot_offset_x
        cy1 = center_y - config.pivot_offset_y
        cx2 = center_x + config.pivot_offset_x_2
        cy2 = center_y - config.pivot_offset_y_2

        # --- 0. STATIC: Background & Faceplate ---
        if full_redraw:
            if BUILDER_DEBUG: builder_logger.trace(f"🏗️🖼️🎨 [CONSTRUCT] Drawing static faceplate/background elements for '{config.label}'")
            if hasattr(canvas, 'panel_bg_image') and canvas.panel_bg_image:
                 if BUILDER_DEBUG: builder_logger.debug("👻🌀🪟 [ALPHA] Applying background image slice.")
                 bg_id = canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw", tags="nextgen_background")
                 canvas.tag_lower(bg_id)
            elif config.intended_bg and not config.is_transparent and not has_custom_bezel:
                w = int(canvas.cget("width"))
                h = int(canvas.cget("height"))
                if BUILDER_DEBUG: builder_logger.debug(f"🎨🖌️🔳 [STYLE] Drawing solid background for meter: {config.intended_bg}")
                rect_id = BuilderMeterNeedleCreator._draw_rounded_rect_poly(canvas, 0, 0, w, h, 20, config.intended_bg)
                canvas.itemconfig(rect_id, tags=("vu_static", "nextgen_background"))
                canvas.tag_lower(rect_id)

            if config.label and config.show_label:
                w = int(canvas.cget("width"))
                canvas.create_text(
                    w/2, 10, text=config.label, fill=config.widget_label_color,
                    font=(NUMBER_FONT_FAMILY, config.font_size, "bold"),
                    anchor="n", tags=("industrial_text", "vu_static")
                )

            if config.cosmetics:
                 cw = int(canvas.cget("width"))
                 ch = int(canvas.cget("height"))
                 MeterModifier.draw_background_faceplate(canvas, center_x, center_y, cw, ch, config.cosmetics)
                 MeterModifier.draw_labels(canvas, center_x, center_y, config.cosmetics, current_value=val1)

        # --- 1. DYNAMIC: Geometry Setup ---
        base_radius = (config.size - config.scale_padding) / 2
        arc_radius = base_radius + (config.arc_radius_offset if config.arc_radius_offset is not None else 0)
        tick_radius = base_radius + (config.tick_radius_offset if config.tick_radius_offset is not None else 0)
        label_radius = base_radius + (config.label_radius_offset if config.label_radius_offset is not None else 0)
        
        tick_len = config.tick_length_override if config.tick_length_override is not None else SCALE_TICK_LENGTH
        sub_tick_len = config.sub_tick_length_override if config.sub_tick_length_override is not None else SCALE_SUB_TICK_LENGTH
        needle_scale_factor = config.needle_length_factor_override if config.needle_length_factor_override is not None else config.needle_scale

        half_angle = config.meter_viewable_angle / 2.0
        start_angle_deg = config.meter_center_angle + half_angle
        end_angle_deg = config.meter_center_angle - half_angle
        extent_deg = start_angle_deg - end_angle_deg

        pivots = [(cx1, cy1, val1, config.counter_clockwise)]
        if bezel_shape in ["stereo_diamond", "intersecting_overlay"] or config.meter_mode == "stereo":
            pivots.append((cx2, cy2, val2, not config.counter_clockwise if bezel_shape == "stereo_diamond" else config.counter_clockwise))

        if BUILDER_DEBUG and not full_redraw: builder_logger.trace(f"🔄✨📶 [RENDER] Updating needle positions for '{config.label}' (V1: {val1:.2f})")

        for i, (px, py, val, ccw) in enumerate(pivots):
            if i > 0 and val is None: continue
            
            # --- Draw Ticks (STATIC) ---
            if full_redraw:
                if BUILDER_DEBUG: builder_logger.trace(f"📐📏🎨 [STATIC] Drawing scale ticks for pivot {i}")
                tick_values = ScaleDrawer.draw_ticks(
                    canvas, px, py, config.min_val, config.max_val, 
                    start_angle_deg, end_angle_deg, extent_deg,
                    base_radius, config.curve_thickness, 
                    tick_len, sub_tick_len,
                    config.fg_color, config.ticks_visible, config.custom_ticks, config.tick_step, config.anchor_point,
                    config.sub_ticks, config.sub_tick_style, ccw,
                    tick_radius=tick_radius
                )
                # Apply static tags to whatever ScaleDrawer just created
                for item in canvas.find_withtag("vu_element"):
                    if not any(t.startswith("vu_needle") for t in canvas.gettags(item)):
                        canvas.addtag_withtag("vu_static", item)

                # --- Draw Labels (STATIC) ---
                if BUILDER_DEBUG: builder_logger.trace(f"🔡🔢🎨 [STATIC] Drawing scale labels for pivot {i}")
                NumberDrawer.draw_labels(
                    canvas, px, py, tick_values,
                    config.min_val, config.max_val, start_angle_deg, end_angle_deg, extent_deg,
                    base_radius, SCALE_TEXT_OFFSET,
                    config.scale_label_color, config.scale_numbers, config.label_overrides, ccw,
                    label_radius=label_radius
                )
                for item in canvas.find_withtag("industrial_text"):
                    canvas.addtag_withtag("vu_static", item)

                # --- Draw Arcs (STATIC) ---
                if BUILDER_DEBUG: builder_logger.trace(f"🌈📐🎨 [STATIC] Drawing color arcs for pivot {i}")
                ScaleDrawer.draw_arcs(
                    canvas, px, py, config.min_val, config.max_val,
                    start_angle_deg, end_angle_deg, extent_deg,
                    base_radius, config.curve_thickness,
                    config.lower_colour, config.middle_colour, config.upper_colour,
                    config.mid_range_start, config.red_zone_start,
                    ccw, arc_radius=arc_radius
                )
                for item in canvas.find_withtag("vu_element"):
                    if not any(t.startswith("vu_needle") for t in canvas.gettags(item)) and "vu_static" not in canvas.gettags(item):
                        canvas.addtag_withtag("vu_static", item)

            # --- DYNAMIC: Peak Dot ---
            range_val = config.max_val - config.min_val
            peak_val = config.red_zone_start
            norm_peak = (peak_val - config.min_val) / range_val if range_val != 0 else 0
            peak_angle = (end_angle_deg + (norm_peak * extent_deg)) if ccw else (start_angle_deg - (norm_peak * extent_deg))
            
            if peak_on and BUILDER_DEBUG: builder_logger.trace(f"🔴🔔✨ [RENDER] Peak indicator ACTIVE for '{config.label}'")
            PeakDrawer.draw_peak_dot(
                canvas, px, py, peak_angle,
                base_radius, config.curve_thickness, peak_on, config.peak_flag,
                arc_radius=arc_radius
            )

            # --- DYNAMIC: Needles & Shadows ---
            n_tag = f"vu_needle_{i}"
            s_tag = f"vu_shadow_{i}"
            
            ShadowDrawer.draw_shadow(
                canvas, px, py, val, config.min_val, config.max_val,
                start_angle_deg, end_angle_deg, extent_deg,
                base_radius, SCALE_TEXT_OFFSET,
                config.pointer_style if i==0 else config.pointer_style_2, 
                config.needle_thickness if i==0 else config.needle_thickness_2, 
                ccw, config.pivot_size, needle_scale=needle_scale_factor,
                tag=s_tag
            )
            
            NeedleDrawer.draw_needle(
                canvas, px, py, val, config.min_val, config.max_val,
                start_angle_deg, end_angle_deg, extent_deg,
                base_radius, SCALE_TEXT_OFFSET,
                config.pointer_colour if i==0 else config.pointer_colour_2, 
                config.pointer_style if i==0 else config.pointer_style_2, 
                config.needle_thickness if i==0 else config.needle_thickness_2, 
                ccw, config.pivot_size, needle_scale=needle_scale_factor,
                tag=n_tag
            )

            if full_redraw:
                if BUILDER_DEBUG: builder_logger.trace(f"🏗️🔘🎨 [STATIC] Drawing pivot hub for pivot {i}")
                PivotDrawer.draw_pivot(canvas, px, py, config.pivot_size, config.pivot_colour, config.secondary_color, config.fg_color)
                for item in canvas.find_withtag("vu_element"):
                    if not any(t.startswith("vu_needle") for t in canvas.gettags(item)) and "vu_static" not in canvas.gettags(item):
                        canvas.addtag_withtag("vu_static", item)

        # --- STATIC: Chassis & Overlays ---
        if full_redraw:
            if BUILDER_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [STATIC] Drawing chassis mask and glass overlays for '{config.label}'")
            # --- Draw Chassis Mask ---
            # ⚡ INDUSTRIAL TRANSPARENCY: We no longer draw solid-colored rectangles for the chassis
            # if they would block the patina.
            
            # --- Dynamic Bottom Mask ---
            R, global_y_shift, shape_key = BezelGeometry.get_scaling_params(
                int(canvas.cget("width")), int(canvas.cget("height")), bezel_shape, bezel_width
            )
            
            from workers.builder.meter_needle.constants import GEM_BEZEL_EXPANSION, GEM_BASE_HEIGHT, GEM_PEAK_HEIGHT
            
            if shape_key == "gem":
                gem_rad = R * GEM_BEZEL_EXPANSION
                y_base_user = (GEM_BASE_HEIGHT * gem_rad) + global_y_shift
                baseline_y = center_y - y_base_user
            elif shape_key == "super_gem":
                gem_rad = R * GEM_BEZEL_EXPANSION
                y_tip_user = -(GEM_PEAK_HEIGHT * gem_rad) + global_y_shift
                baseline_y = center_y - y_tip_user
            elif shape_key == "octagon":
                oct_rad = R * 1.4
                y_base_user = (-0.923 * oct_rad) + global_y_shift
                baseline_y = center_y - y_base_user
            else:
                baseline_y = center_y - global_y_shift
            
            # ⚡ Only draw solid mask if NOT transparent and NO patina slice is available
            if shape_key != "super_gem" and not (hasattr(canvas, 'panel_bg_image') and canvas.panel_bg_image):
                if not config.is_transparent:
                    bg = canvas.cget("bg")
                    canvas.create_rectangle(0, baseline_y + 1, int(canvas.cget("width")), int(canvas.cget("height")), 
                                             fill=bg, outline=bg, tags="vu_static")
            
            if config.cosmetics:
                 cw, ch = int(canvas.cget("width")), int(canvas.cget("height"))
                 MeterModifier.draw_glass_layer(canvas, center_x, center_y, cw, ch, config.cosmetics)
                 MeterModifier.draw_foreground_overlay(canvas, center_x, center_y, cw, ch, config.cosmetics)

        # ⚡ FINAL Z-ORDER (Only needed once or on full redraw)
        # Check if Z-order is already settled to avoid 1.1M redundant calls
        if full_redraw or not getattr(canvas, "_z_order_settled", False):
            if BUILDER_DEBUG: builder_logger.trace(f"🔀🏗️🔳 [SYNC] Finalizing Z-order layering for '{config.label}'")
            try: canvas.tag_lower("panel_bg_slice")
            except: pass
            
            try: canvas.tag_raise("nextgen_background", "panel_bg_slice")
            except: pass
            
            try: canvas.tag_raise("vu_shadow", "nextgen_background")
            except: pass
            
            try: canvas.tag_raise("vu_element", "vu_shadow")
            except: pass
            
            try: canvas.tag_raise("nextgen_foreground", "vu_element")
            except: pass
            
            try: canvas.tag_raise("industrial_text", "nextgen_foreground")
            except: pass
            
            canvas._z_order_settled = True

    @staticmethod
    def _draw_rounded_rect_poly(canvas, x1, y1, x2, y2, radius, color):
        points = [
            x1 + radius, y1, x1 + radius, y1, x2 - radius, y1, x2 - radius, y1,
            x2, y1, x2, y1 + radius, x2, y2 - radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x2 - radius, y2,
            x1 + radius, y2, x1 + radius, y2, x1, y2, x1, y2 - radius,
            x1, y2 - radius, x1, y1 + radius, x1, y1 + radius, x1, y1,
        ]
        return canvas.create_polygon(points, fill=color, outline=color, smooth=True, tags="vu_element")

    # Compatibility shim if needed by external callers
    def _draw_needle_vu_meter(self, *args, **kwargs):
        pass
