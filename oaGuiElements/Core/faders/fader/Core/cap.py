# Core/cap.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import math
import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageFilter

# --- Module Level Cache for 3D Assets ---
_FADER_ASSET_CACHE = {}

# --- Constants ---
UPSCALE_FACTOR = 2
DEFAULT_BODY_COLOR_RGB = [40, 40, 40]
LIGHT_DIRECTION = [0.3, -0.6, 0.8]
AMBIENT_LIGHT = 0.25
SPECULAR_POWER = 1.5
SPECULAR_INTENSITY = 0.3
MAX_COLOR_VALUE = 255
INDICATOR_LINE_COLOR_DEFAULT = [40, 40, 180]
CORNER_RADIUS_MULTIPLIER = 3
SHADOW_RADIUS = 4
SHADOW_OPACITY = 110
GAUSSIAN_BLUR_RADIUS_SHADOW = 3.5
SPECULAR_HIGHLIGHT_COLOR_VALUE = 150

class CapDrawer:
    @staticmethod
    def get_3d_fader_cap(w, h, body_color, outline_color, highlight_color=None):
        """
        Optimized 'Next Gen' fader cap generator.
        Uses NumPy vectorization to eliminate 25 million 'putpixel' calls.
        """
        cache_key = (w, h, body_color, outline_color, highlight_color, "v18_vectorized")
        if cache_key in _FADER_ASSET_CACHE:
            return _FADER_ASSET_CACHE[cache_key]

        upscale = UPSCALE_FACTOR 
        upscaled_width, upscaled_height = w * upscale, h * upscale
        
        def convert_hex_to_rgb(hex_str):
            hex_str = hex_str.lstrip('#')
            return np.array([int(hex_str[channel_index:channel_index+2], 16) for channel_index in (0, 2, 4)], dtype=np.float32)

        try: 
            body_rgb = convert_hex_to_rgb(body_color)
        except: 
            body_rgb = np.array(DEFAULT_BODY_COLOR_RGB, dtype=np.float32)

        # 1. Create coordinate grids
        y_coords = np.linspace(0, 1, upscaled_height, dtype=np.float32).reshape(upscaled_height, 1)
        
        # 2. Vectorized Slope Logic
        slope_y = np.zeros((upscaled_height, 1), dtype=np.float32)
        slope_z = np.ones((upscaled_height, 1), dtype=np.float32)

        # Define zones
        slope_y[y_coords < 0.10] = -1.0
        slope_z[y_coords < 0.10] = 0.0
        
        mask_mid_top = (y_coords >= 0.10) & (y_coords < 0.20)
        slope_y[mask_mid_top] = -0.707
        slope_z[mask_mid_top] = 0.707
        
        mask_concave = (y_coords >= 0.25) & (y_coords < 0.75)
        interpolation_factor = (y_coords[mask_concave] - 0.25) / 0.5
        local_interpolation = (interpolation_factor - 0.5) * 2.0
        slope_y[mask_concave] = local_interpolation * 0.55
        slope_z[mask_concave] = np.sqrt(np.maximum(0, 1.0 - slope_y[mask_concave]**2))

        mask_mid_bottom = (y_coords >= 0.80) & (y_coords < 0.90)
        slope_y[mask_mid_bottom] = 0.707
        slope_z[mask_mid_bottom] = 0.707
        
        slope_y[y_coords >= 0.90] = 1.0
        slope_z[y_coords >= 0.90] = 0.0

        # 3. Vectorized Lighting
        light_dir = np.array(LIGHT_DIRECTION, dtype=np.float32)
        light_dir /= np.linalg.norm(light_dir)
        
        ambient = AMBIENT_LIGHT
        diffuse = np.maximum(ambient, slope_y * light_dir[1] + slope_z * light_dir[2])
        
        h_vec = light_dir + np.array([0, 0, 1], dtype=np.float32)
        h_vec /= np.linalg.norm(h_vec)
        spec_dot = np.maximum(0, slope_y * h_vec[1] + slope_z * h_vec[2])
        spec = np.power(spec_dot, SPECULAR_POWER) * SPECULAR_INTENSITY

        # 4. Ambient Occlusion & Grooves
        ambient_occlusion = np.ones((upscaled_height, 1), dtype=np.float32)
        dist = 1.0 - (np.abs(y_coords - 0.5) / 0.25)
        ambient_occlusion[mask_concave] = 1.0 - (np.maximum(0, dist[mask_concave]) * 0.4)
        
        groove_val = np.sin(((y_coords - 0.22) / 0.56) * np.pi * 14 - np.pi/2)
        is_groove = (y_coords > 0.22) & (y_coords < 0.78)
        
        # Apply grooves to diffuse and ambient_occlusion
        diffuse[is_groove] += groove_val[is_groove] * 0.12
        ambient_occlusion[is_groove] *= (1.0 + groove_val[is_groove] * 0.08)

        # 5. Final Color Calculation (UW x UH x 3)
        colors = body_rgb.reshape(1, 1, 3) * (diffuse * ambient_occlusion).reshape(upscaled_height, 1, 1) + (SPECULAR_HIGHLIGHT_COLOR_VALUE * spec).reshape(upscaled_height, 1, 1)
        colors = np.clip(colors, 0, MAX_COLOR_VALUE).astype(np.uint8)
        
        # Tile across width
        pixel_array = np.tile(colors, (1, upscaled_width, 1))
        
        # 6. Indicator Line
        center_y = upscaled_height // 2
        line_h = max(2, upscale)
        if highlight_color:
            h_rgb = convert_hex_to_rgb(highlight_color).astype(np.uint8)
            pixel_array[center_y - line_h//2 : center_y + line_h//2, :] = h_rgb
        else:
            pixel_array[center_y - line_h//2 : center_y + line_h//2, :] = INDICATOR_LINE_COLOR_DEFAULT

        surface = Image.fromarray(pixel_array, mode="RGB").convert("RGBA")

        # 7. Masking & Shadow
        mask = Image.new("L", (upscaled_width, upscaled_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle((0, 0, upscaled_width, upscaled_height), radius=CORNER_RADIUS_MULTIPLIER*upscale, fill=MAX_COLOR_VALUE)
        scoop_w = int(upscaled_width * 0.15) 
        mask_draw.ellipse((-scoop_w, -upscaled_height//4, scoop_w, 5*upscaled_height//4), fill=0) 
        mask_draw.ellipse((upscaled_width - scoop_w, -upscaled_height//4, upscaled_width + scoop_w, 5*upscaled_height//4), fill=0) 

        surface_final = Image.new("RGBA", (upscaled_width, upscaled_height), (0,0,0,0))
        surface_final.paste(surface, (0,0), mask)
        surface_final = surface_final.resize((w, h), Image.Resampling.LANCZOS)
        
        pad_x, pad_y = 10, 15
        canvas_img = Image.new("RGBA", (w + pad_x*2, h + pad_y*2), (0,0,0,0))
        
        shadow_layer = Image.new("RGBA", canvas_img.size, (0,0,0,0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_draw.rounded_rectangle((pad_x+4, pad_y+10, pad_x+w+4, pad_y+h+10), radius=SHADOW_RADIUS, fill=(0,0,0,SHADOW_OPACITY))
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=GAUSSIAN_BLUR_RADIUS_SHADOW))
        
        canvas_img.paste(shadow_layer, (0,0), shadow_layer)
        canvas_img.paste(surface_final, (pad_x, pad_y), surface_final)
        
        photo = ImageTk.PhotoImage(canvas_img)
        _FADER_ASSET_CACHE[cache_key] = photo
        return photo
