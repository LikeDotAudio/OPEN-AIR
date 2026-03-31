# cosmetics/lighting_overlay.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageTk
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import math
import numpy as np
import tkinter as tk

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaGuiElements.Core.metering.meter_needle.cosmetics.geometry import BezelGeometry
from oaGuiElements.Core.metering.meter_needle.constants import (
    GEM_BEZEL_EXPANSION, GEM_BASE_HEIGHT, SHAPE_Y_SHIFTS, HILL_CONFIGS
)

# --- Constants ---
SUPERSAMPLING_SCALE = 2
DEFAULT_GLOW_COLOR_HEX = "#FFB450"
DEFAULT_GLOW_INTENSITY = 0.25
DEFAULT_SIZE_X_MULT = 0.5
DEFAULT_SIZE_Y_MULT = 0.25
DEFAULT_GLOW_RGB = (255, 180, 80)
GAUSSIAN_BLUR_SCALE_VIGNETTE = 4
GAUSSIAN_BLUR_SCALE_HILL_SHADOW = 4
GAUSSIAN_BLUR_SCALE_TOP_SPEC = 4.0
GAUSSIAN_BLUR_SCALE_BOTTOM_SPEC = 7.0
MAX_ALPHA = 255
GLOW_INTENSITY_FACTOR = 0.8
SHADOW_OPACITY = 200
SHADOW_OFFSET_FACTOR = 4
GLINT_Y_FACTOR = 0.1
GLINT_W_FACTOR = 0.25
GLINT_H_FACTOR = 0.06
LOW_SPEC_Y_OFFSET_FACTOR = 0.05
LOW_SPEC_W_FACTOR = 0.35
LOW_SPEC_H_FACTOR = 0.12

class VintageLightingGenerator:
    """
    Refined procedural glass renderer. 
    Simulates light emerging from the pivot/mechanism, 
    multi-stage specular reflections, and bezel cast shadows.
    """

    @staticmethod
    def create_lighting_overlay(width, height, bezel_shape, bezel_width, pivot_x, pivot_y, lighting_config={}):
        # 1. High-Res Canvas (Supersampling)
        scale = SUPERSAMPLING_SCALE
        upscaled_width, upscaled_height = width * scale, height * scale
        pivot_x_scaled, pivot_y_scaled = pivot_x * scale, pivot_y * scale
        shape_key = bezel_shape.lower() if bezel_shape else "default"
        
        # Extract Config
        glow_color_hex = lighting_config.get("color", DEFAULT_GLOW_COLOR_HEX)
        glow_intensity = float(lighting_config.get("intensity", DEFAULT_GLOW_INTENSITY))
        y_offset_user = float(lighting_config.get("y_offset", 0)) * scale
        size_x_mult = float(lighting_config.get("size_x", DEFAULT_SIZE_X_MULT))
        size_y_mult = float(lighting_config.get("size_y", DEFAULT_SIZE_Y_MULT))
        overlay_style = lighting_config.get("overlay_style", None)
        
        # 2. Shape Mask - CLIPPED TO INNER EDGE
        inner_shrink = (bezel_width * scale) / 2.0
        points_inner, is_smooth = BezelGeometry.get_bezel_points(
            pivot_x_scaled, pivot_y_scaled, upscaled_width, upscaled_height, bezel_shape, bezel_width * scale, shrink_px=inner_shrink
        )
        
        radius_calc, _, _ = BezelGeometry.get_scaling_params(upscaled_width, upscaled_height, bezel_shape, bezel_width * scale)
        
        mask = Image.new('L', (upscaled_width, upscaled_height), 0)
        if points_inner:
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.polygon(points_inner, fill=MAX_ALPHA)
        
        # 3. Layer A: Bezel Edge Occlusion (Inner Depth)
        vignette = Image.new('RGBA', (upscaled_width, upscaled_height), (0,0,0,0))
        draw_vign = ImageDraw.Draw(vignette)
        if points_inner:
            draw_vign.polygon(points_inner, outline=(0,0,0,220), width=int(6*scale))
        vignette = vignette.filter(ImageFilter.GaussianBlur(radius=GAUSSIAN_BLUR_SCALE_VIGNETTE*scale))
        vignette.putalpha(ImageChops.multiply(vignette.split()[3], mask))

        # 4. Layer B: Pivot Glow
        glow_layer = Image.new('RGBA', (upscaled_width, upscaled_height), (0,0,0,0))
        draw_glow = ImageDraw.Draw(glow_layer)
        
        # Safe Color Parsing
        rgb = DEFAULT_GLOW_RGB
        if isinstance(glow_color_hex, str) and len(glow_color_hex) >= 7:
            try:
                color_hex_clean = str(glow_color_hex).lstrip('#')
                rgb = tuple(int(color_hex_clean[channel_index:channel_index+2], 16) for channel_index in (0, 2, 4))
            except Exception:
                pass
            
        glow_center_y = pivot_y_scaled + y_offset_user
        glow_radius_w = int(upscaled_width * size_x_mult) 
        glow_radius_h = int(upscaled_height * size_y_mult)
        
        draw_glow.pieslice(
            [pivot_x_scaled-glow_radius_w, glow_center_y-glow_radius_h, pivot_x_scaled+glow_radius_w, glow_center_y+glow_radius_h], 
            start=180, end=0, fill=rgb + (MAX_ALPHA,)
        )
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=upscaled_width*0.15))
        
        red, green, blue, alpha = glow_layer.split()
        alpha = alpha.point(lambda p: p * (glow_intensity * GLOW_INTENSITY_FACTOR))
        glow_layer = Image.merge('RGBA', (red, green, blue, alpha))

        # --- Layer B.5: Hill Shadow (If Aperture Mask) ---
        hill_shadow_layer = Image.new('RGBA', (upscaled_width, upscaled_height), (0,0,0,0))
        if overlay_style == "aperture_mask":
            VintageLightingGenerator._draw_hill_mask(
                hill_shadow_layer, pivot_x_scaled, pivot_y_scaled, radius_calc, shape_key, (0,0,0,SHADOW_OPACITY) # Black shadow
            )
            hill_shadow_layer = hill_shadow_layer.filter(ImageFilter.GaussianBlur(radius=GAUSSIAN_BLUR_SCALE_HILL_SHADOW*scale))
            shifted_shadow = Image.new('RGBA', (upscaled_width, upscaled_height), (0,0,0,0))
            shifted_shadow.alpha_composite(hill_shadow_layer, (0, int(SHADOW_OFFSET_FACTOR*scale)))
            hill_shadow_layer = shifted_shadow
            hill_shadow_layer.putalpha(ImageChops.multiply(hill_shadow_layer.split()[3], mask))

        # 5. Layer C: Convex Glass Specular (The "Pillow")
        glass_color = (224, 247, 250) 
        
        top_spec_layer = Image.new('RGBA', (upscaled_width, upscaled_height), (0,0,0,0))
        draw_top = ImageDraw.Draw(top_spec_layer)
        glint_y = int(upscaled_height * GLINT_Y_FACTOR) 
        glint_w = int(upscaled_width * GLINT_W_FACTOR)
        glint_h = int(upscaled_height * GLINT_H_FACTOR)
        draw_top.ellipse([upscaled_width//2-glint_w, glint_y-glint_h, upscaled_width//2+glint_w, glint_y+glint_h], 
                         fill=(255, 255, 255, 40))
        top_spec_layer = top_spec_layer.filter(ImageFilter.GaussianBlur(radius=GAUSSIAN_BLUR_SCALE_TOP_SPEC * scale))

        bottom_spec_layer = Image.new('RGBA', (upscaled_width, upscaled_height), (0,0,0,0))
        draw_bottom = ImageDraw.Draw(bottom_spec_layer)
        low_spec_y = int(glow_center_y + (upscaled_height * LOW_SPEC_Y_OFFSET_FACTOR))
        low_spec_w = int(upscaled_width * LOW_SPEC_W_FACTOR)
        low_spec_h = int(upscaled_height * LOW_SPEC_H_FACTOR)
        draw_bottom.ellipse([pivot_x_scaled-low_spec_w, low_spec_y-low_spec_h, pivot_x_scaled+low_spec_w, low_spec_y+low_spec_h], 
                            fill=glass_color + (35,))
        bottom_spec_layer = bottom_spec_layer.filter(ImageFilter.GaussianBlur(radius=GAUSSIAN_BLUR_SCALE_BOTTOM_SPEC * scale))
        
        spec_layer = Image.new('RGBA', (upscaled_width, upscaled_height), (0,0,0,0))
        spec_layer = Image.alpha_composite(spec_layer, top_spec_layer)
        spec_layer = Image.alpha_composite(spec_layer, bottom_spec_layer)

        # ⚡ OPTIMIZATION: Vectorized Glass Mask
        y_grid = np.linspace(0, 1, upscaled_height, dtype=np.float32).reshape(upscaled_height, 1)
        x_grid = np.abs(np.linspace(-1, 1, upscaled_width, dtype=np.float32)).reshape(1, upscaled_width)
        
        # Vertical alpha component
        v_alpha = np.cos(np.minimum(1.0, y_grid * 1.4) * (np.pi / 2))
        # Horizontal alpha component
        h_alpha = np.cos(np.minimum(1.0, x_grid * 0.4) * (np.pi / 2))
        
        # Combine and scale to 0-255
        alpha_matrix = (v_alpha * h_alpha * MAX_ALPHA).astype(np.uint8)
        glass_mask = Image.fromarray(alpha_matrix, mode="L")
            
        spec_layer.putalpha(ImageChops.multiply(spec_layer.split()[3], glass_mask))

        # 6. Composite
        final = Image.new('RGBA', (upscaled_width, upscaled_height), (0,0,0,0))
        final = Image.alpha_composite(final, glow_layer)
        final = Image.alpha_composite(final, hill_shadow_layer) 
        final = Image.alpha_composite(final, vignette)
        final = Image.alpha_composite(final, spec_layer)
        
        # 7. Final Clipping
        final.putalpha(ImageChops.multiply(final.split()[3], mask))
        
        return final.resize((width, height), Image.Resampling.LANCZOS)

    @staticmethod
    def _draw_hill_mask(image, cx, cy, radius, shape_key, color):
        """Draws the hill-shaped aperture mask for vintage meters."""
        # 1. Get dimensions
        w_factor, h_factor = HILL_CONFIGS.get(shape_key, HILL_CONFIGS["default"])
        hill_w, hill_h = radius * w_factor, radius * h_factor
        
        # 2. Get base Y
        base_y = VintageLightingGenerator._get_hill_base_y(cy, radius, shape_key)
            
        # 3. Generate points
        steps = 40
        poly_points = []
        for i in range(steps + 1):
            x_norm = 1.0 - (2.0 * i / steps)
            x = cx + (x_norm * hill_w)
            y = base_y - (math.cos(x_norm * math.pi / 2) * hill_h)
            poly_points.append((x, y))
            
        poly_points.append((cx - hill_w, base_y + hill_h*2))
        poly_points.append((cx + hill_w, base_y + hill_h*2))
        
        ImageDraw.Draw(image).polygon(poly_points, fill=color)

    @staticmethod
    def _get_hill_base_y(cy, radius, shape_key):
        """Calculates the baseline Y-coordinate for the hill mask."""
        y_shift = SHAPE_Y_SHIFTS.get(shape_key, 0.0) * radius
        
        if shape_key == "gem":
            gem_rad = radius * GEM_BEZEL_EXPANSION
            return cy - ((GEM_BASE_HEIGHT * gem_rad) + y_shift)
        
        if shape_key == "super_gem":
            return cy
            
        if shape_key == "octagon":
            oct_rad = radius * 1.4 # OCTAGON_BEZEL_EXPANSION
            return cy - ((-0.923 * oct_rad) + y_shift)
            
        return cy - y_shift

    @staticmethod
    def photo_image(width, height, bezel_shape, bezel_width, pivot_x, pivot_y, lighting_config={}):
        try:
            pil_img = VintageLightingGenerator.create_lighting_overlay(
                width, height, bezel_shape, bezel_width, pivot_x, pivot_y, lighting_config
            )
            # ⚡ SAFETY: Ensure width/height are positive before creating PhotoImage
            if width <= 0 or height <= 0:
                return None
            return ImageTk.PhotoImage(pil_img)
        except (RuntimeError, ValueError, tk.TclError) as e:
            # Handle headless environments or mock failures gracefully
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"ℹ️ Skipping PhotoImage creation (Headless/Mock): {e}", level="DEBUG")
            return None
        except Exception as e:
            logger.exception("Error generating glass overlay")
            return None
