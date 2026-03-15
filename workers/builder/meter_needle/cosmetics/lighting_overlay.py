from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageTk
import math
import numpy as np

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from workers.builder.meter_needle.cosmetics.geometry import BezelGeometry
from workers.builder.meter_needle.constants import (
    GEM_BEZEL_EXPANSION, GEM_BASE_HEIGHT, SHAPE_Y_SHIFTS
)

class VintageLightingGenerator:
    """
    Refined procedural glass renderer. 
    Simulates light emerging from the pivot/mechanism, 
    multi-stage specular reflections, and bezel cast shadows.
    """

    @staticmethod
    def generate_overlay(width, height, bezel_shape, bezel_width, pivot_x, pivot_y, lighting_config={}):
        # 1. High-Res Canvas (Supersampling)
        scale = 2
        w, h = width * scale, height * scale
        p_x, p_y = pivot_x * scale, pivot_y * scale
        shape_key = bezel_shape.lower() if bezel_shape else "default"
        
        # Extract Config
        glow_color_hex = lighting_config.get("color", "#FFB450")
        glow_intensity = float(lighting_config.get("intensity", 0.25))
        y_offset_user = float(lighting_config.get("y_offset", 0)) * scale
        size_x_mult = float(lighting_config.get("size_x", 0.5))
        size_y_mult = float(lighting_config.get("size_y", 0.25))
        overlay_style = lighting_config.get("overlay_style", None)
        
        # 2. Shape Mask - CLIPPED TO INNER EDGE
        inner_shrink = (bezel_width * scale) / 2.0
        points_inner, is_smooth = BezelGeometry.get_bezel_points(
            p_x, p_y, w, h, bezel_shape, bezel_width * scale, shrink_px=inner_shrink
        )
        
        radius_calc, _, _ = BezelGeometry.get_scaling_params(w, h, bezel_shape, bezel_width * scale)
        
        mask = Image.new('L', (w, h), 0)
        if points_inner:
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.polygon(points_inner, fill=255)
        
        # 3. Layer A: Bezel Edge Occlusion (Inner Depth)
        vignette = Image.new('RGBA', (w, h), (0,0,0,0))
        draw_vign = ImageDraw.Draw(vignette)
        if points_inner:
            draw_vign.polygon(points_inner, outline=(0,0,0,220), width=int(6*scale))
        vignette = vignette.filter(ImageFilter.GaussianBlur(radius=4*scale))
        vignette.putalpha(ImageChops.multiply(vignette.split()[3], mask))

        # 4. Layer B: Pivot Glow
        glow_layer = Image.new('RGBA', (w, h), (0,0,0,0))
        draw_glow = ImageDraw.Draw(glow_layer)
        
        # Safe Color Parsing
        rgb = (255, 180, 80) # Default
        if isinstance(glow_color_hex, str) and len(glow_color_hex) >= 7:
            try:
                c = str(glow_color_hex).lstrip('#')
                rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
            except Exception:
                pass
            
        glow_center_y = p_y + y_offset_user
        g_rad_w = int(w * size_x_mult) 
        g_rad_h = int(h * size_y_mult)
        
        draw_glow.pieslice(
            [p_x-g_rad_w, glow_center_y-g_rad_h, p_x+g_rad_w, glow_center_y+g_rad_h], 
            start=180, end=0, fill=rgb + (255,)
        )
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=w*0.15))
        
        r, g, b, a = glow_layer.split()
        a = a.point(lambda p: p * (glow_intensity * 0.8))
        glow_layer = Image.merge('RGBA', (r, g, b, a))

        # --- Layer B.5: Hill Shadow (If Aperture Mask) ---
        hill_shadow_layer = Image.new('RGBA', (w, h), (0,0,0,0))
        if overlay_style == "aperture_mask":
            VintageLightingGenerator._draw_hill_mask(
                hill_shadow_layer, p_x, p_y, radius_calc, shape_key, (0,0,0,200) # Black shadow
            )
            hill_shadow_layer = hill_shadow_layer.filter(ImageFilter.GaussianBlur(radius=4*scale))
            shifted_shadow = Image.new('RGBA', (w, h), (0,0,0,0))
            shifted_shadow.alpha_composite(hill_shadow_layer, (0, int(4*scale)))
            hill_shadow_layer = shifted_shadow
            hill_shadow_layer.putalpha(ImageChops.multiply(hill_shadow_layer.split()[3], mask))

        # 5. Layer C: Convex Glass Specular (The "Pillow")
        glass_color = (224, 247, 250) 
        
        top_spec_layer = Image.new('RGBA', (w, h), (0,0,0,0))
        draw_top = ImageDraw.Draw(top_spec_layer)
        glint_y = int(h * 0.1) 
        glint_w = int(w * 0.25)
        glint_h = int(h * 0.06)
        draw_top.ellipse([w//2-glint_w, glint_y-glint_h, w//2+glint_w, glint_y+glint_h], 
                         fill=(255, 255, 255, 40))
        top_spec_layer = top_spec_layer.filter(ImageFilter.GaussianBlur(radius=4.0 * scale))

        bottom_spec_layer = Image.new('RGBA', (w, h), (0,0,0,0))
        draw_bottom = ImageDraw.Draw(bottom_spec_layer)
        low_spec_y = int(glow_center_y + (h * 0.05))
        low_spec_w = int(w * 0.35)
        low_spec_h = int(h * 0.12)
        draw_bottom.ellipse([p_x-low_spec_w, low_spec_y-low_spec_h, p_x+low_spec_w, low_spec_y+low_spec_h], 
                            fill=glass_color + (35,))
        bottom_spec_layer = bottom_spec_layer.filter(ImageFilter.GaussianBlur(radius=7.0 * scale))
        
        spec_layer = Image.new('RGBA', (w, h), (0,0,0,0))
        spec_layer = Image.alpha_composite(spec_layer, top_spec_layer)
        spec_layer = Image.alpha_composite(spec_layer, bottom_spec_layer)

        # ⚡ OPTIMIZATION: Vectorized Glass Mask
        # Replaces the nested loops and putpixel (28 million calls)
        y_grid = np.linspace(0, 1, h, dtype=np.float32).reshape(h, 1)
        x_grid = np.abs(np.linspace(-1, 1, w, dtype=np.float32)).reshape(1, w)
        
        # Vertical alpha component
        v_alpha = np.cos(np.minimum(1.0, y_grid * 1.4) * (np.pi / 2))
        # Horizontal alpha component
        h_alpha = np.cos(np.minimum(1.0, x_grid * 0.4) * (np.pi / 2))
        
        # Combine and scale to 0-255
        alpha_matrix = (v_alpha * h_alpha * 255).astype(np.uint8)
        glass_mask = Image.fromarray(alpha_matrix, mode="L")
            
        spec_layer.putalpha(ImageChops.multiply(spec_layer.split()[3], glass_mask))

        # 6. Composite
        final = Image.new('RGBA', (w, h), (0,0,0,0))
        final = Image.alpha_composite(final, glow_layer)
        final = Image.alpha_composite(final, hill_shadow_layer) 
        final = Image.alpha_composite(final, vignette)
        final = Image.alpha_composite(final, spec_layer)
        
        # 7. Final Clipping
        final.putalpha(ImageChops.multiply(final.split()[3], mask))
        
        return final.resize((width, height), Image.Resampling.LANCZOS)

    @staticmethod
    def _draw_hill_mask(image, cx, cy, radius, shape_key, color):
        draw = ImageDraw.Draw(image)
        
        if shape_key == "hotdog":
            hill_w = radius * 2.5
            hill_h = radius * 0.3
        elif shape_key == "gem":
            hill_w = radius * 0.8
            hill_h = radius * 0.3
        elif shape_key == "super_gem":
            hill_w = radius * 0.4
            hill_h = radius * 0.3
        elif shape_key == "hex":
            hill_w = radius * 1.8
            hill_h = radius * 0.3
        elif shape_key == "octagon":
            hill_w = radius * 1.8
            hill_h = radius * 0.3
        elif shape_key in ["triangle", "pyramid", "parking_meter"]:
            hill_w = radius * 0.2
            hill_h = radius * 0.1
        elif shape_key in ["squircle", "squimonde"]:
            hill_w = radius * 0.5
            hill_h = radius * 0.3
        elif shape_key == "crest":
            hill_w = radius * 1.0
            hill_h = radius * 0.3
        elif shape_key == "squectangle":
            hill_w = radius * 0.7
            hill_h = radius * 0.3
        elif shape_key == "trapezoid":
            hill_w = radius * 1.2
            hill_h = radius * 0.3
        else:
            hill_w = radius * 1.5
            hill_h = radius * 0.3
            
        y_shift_factor = SHAPE_Y_SHIFTS.get(shape_key, 0.0)
        global_y_shift = y_shift_factor * radius
        
        if shape_key == "gem":
            gem_rad = radius * GEM_BEZEL_EXPANSION
            y_base_user = (GEM_BASE_HEIGHT * gem_rad) + global_y_shift
            base_y = cy - y_base_user
        elif shape_key == "super_gem":
            base_y = cy
        elif shape_key == "octagon":
            oct_rad = radius * 1.4
            y_base_user = (-0.923 * oct_rad) + global_y_shift
            base_y = cy - y_base_user
        else:
            base_y = cy - global_y_shift
            
        steps = 40
        poly_points = []
        for i in range(steps + 1):
            x_norm = 1.0 - (2.0 * i / steps)
            x = cx + (x_norm * hill_w)
            y = base_y - (math.cos(x_norm * math.pi / 2) * hill_h)
            poly_points.append((x, y))
            
        poly_points.append((cx - hill_w, base_y + hill_h*2))
        poly_points.append((cx + hill_w, base_y + hill_h*2))
        
        draw.polygon(poly_points, fill=color)

    @staticmethod
    def photo_image(width, height, bezel_shape, bezel_width, pivot_x, pivot_y, lighting_config={}):
        try:
            pil_img = VintageLightingGenerator.generate_overlay(
                width, height, bezel_shape, bezel_width, pivot_x, pivot_y, lighting_config
            )
            return ImageTk.PhotoImage(pil_img)
        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("Error generating glass overlay")
            return None
