# Core/fader_bar_asset_generator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from oaLogging.Core.logger import builder_logger

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = False
_FADER_BAR_ASSET_CACHE = {}

class FaderBarAssetGenerator:
    """Generates photorealistic saddle fader caps using NumPy vectorization with caching."""

    @classmethod
    def get_3d_cap(cls, width, height, body_color, outline_color):
        cache_key = (width, height, body_color, outline_color, "v7_vectorized")
        if cache_key in _FADER_BAR_ASSET_CACHE: return _FADER_BAR_ASSET_CACHE[cache_key]

        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🖼️🎨 [ASSET] Generating NEW 3D fader cap: {width}x{height}")
        
        UPSCALE_FACTOR = 2
        upscale_width, upscale_height = width * UPSCALE_FACTOR, height * UPSCALE_FACTOR
        
        def convert_hex_to_rgb(hex_str):
            hex_str = hex_str.lstrip('#')
            return np.array([int(hex_str[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)

        try: 
            body_rgb = convert_hex_to_rgb(body_color)
        except: 
            FALLBACK_BODY_VAL = 40
            body_rgb = np.array([FALLBACK_BODY_VAL, FALLBACK_BODY_VAL, FALLBACK_BODY_VAL], dtype=np.float32)
        
        BASE_COLOR_WEIGHT = 0.7
        BODY_COLOR_WEIGHT = 0.3
        BASE_RGB_VAL = 30
        base_rgb = BASE_COLOR_WEIGHT * np.array([BASE_RGB_VAL, BASE_RGB_VAL, BASE_RGB_VAL], dtype=np.float32) + BODY_COLOR_WEIGHT * body_rgb
        
        LIGHT_DIR_X, LIGHT_DIR_Y, LIGHT_DIR_Z = 0.3, -0.6, 0.8
        light_dir = np.array([LIGHT_DIR_X, LIGHT_DIR_Y, LIGHT_DIR_Z], dtype=np.float32)
        light_dir /= np.linalg.norm(light_dir)
        
        normalized_y = np.linspace(0, 1, upscale_height, dtype=np.float32)
        slope_y, slope_z = np.zeros(upscale_height, dtype=np.float32), np.zeros(upscale_height, dtype=np.float32)
        
        # Profile Logic (1D masks)
        SLOPE_THRESHOLD_1 = 0.10
        SLOPE_THRESHOLD_2 = 0.20
        SLOPE_THRESHOLD_3 = 0.25
        SLOPE_THRESHOLD_4 = 0.75
        SLOPE_THRESHOLD_5 = 0.80
        SLOPE_THRESHOLD_6 = 0.90

        mask_slope_1 = normalized_y < SLOPE_THRESHOLD_1
        slope_y[mask_slope_1], slope_z[mask_slope_1] = -1.0, 0.0
        
        mask_slope_2 = (normalized_y >= SLOPE_THRESHOLD_1) & (normalized_y < SLOPE_THRESHOLD_2)
        slope_y[mask_slope_2], slope_z[mask_slope_2] = -0.707, 0.707
        
        mask_slope_3 = (normalized_y >= SLOPE_THRESHOLD_2) & (normalized_y < SLOPE_THRESHOLD_3)
        slope_y[mask_slope_3], slope_z[mask_slope_3] = 0.0, 1.0
        
        mask_slope_4 = (normalized_y >= SLOPE_THRESHOLD_3) & (normalized_y < SLOPE_THRESHOLD_4)
        PROFILE_CENTER_SCALE = 0.5
        PROFILE_OFFSET = 0.5
        PROFILE_AMPLITUDE = 2.0
        PROFILE_CURVATURE = 0.55
        profile_t = (normalized_y[mask_slope_4] - SLOPE_THRESHOLD_3) / PROFILE_CENTER_SCALE
        slope_y_val = (profile_t - PROFILE_OFFSET) * PROFILE_AMPLITUDE * PROFILE_CURVATURE
        slope_y[mask_slope_4] = slope_y_val
        slope_z[mask_slope_4] = np.sqrt(np.maximum(0, 1.0 - slope_y_val**2))
        
        mask_slope_5 = (normalized_y >= SLOPE_THRESHOLD_4) & (normalized_y < SLOPE_THRESHOLD_5)
        slope_y[mask_slope_5], slope_z[mask_slope_5] = 0.0, 1.0
        
        mask_slope_6 = (normalized_y >= SLOPE_THRESHOLD_5) & (normalized_y < SLOPE_THRESHOLD_6)
        slope_y[mask_slope_6], slope_z[mask_slope_6] = 0.707, 0.707
        
        mask_slope_7 = (normalized_y >= SLOPE_THRESHOLD_6)
        slope_y[mask_slope_7], slope_z[mask_slope_7] = 1.0, 0.0

        ambient_occlusion = np.ones(upscale_height, dtype=np.float32)
        CENTER_REFERENCE = 0.5
        CENTER_SCALE = 0.25
        center_distance = 1.0 - (np.abs(normalized_y - CENTER_REFERENCE) / CENTER_SCALE)
        AO_STRENGTH = 0.4
        ambient_occlusion[mask_slope_4] = 1.0 - (np.maximum(0, center_distance[mask_slope_4]) * AO_STRENGTH)
        
        GROOVE_START, GROOVE_END = 0.22, 0.78
        GROOVE_WIDTH = 0.56
        GROOVE_FREQUENCY = 14
        GROOVE_AMPLITUDE = 0.12
        PHASE_SHIFT = np.pi/2
        groove_t = (normalized_y - GROOVE_START) / GROOVE_WIDTH
        groove_value = np.where((normalized_y > GROOVE_START) & (normalized_y < GROOVE_END), 
                                np.sin(groove_t * np.pi * GROOVE_FREQUENCY - PHASE_SHIFT) * GROOVE_AMPLITUDE, 0)
        
        DIFFUSE_MIN = 0.25
        diffuse = np.maximum(DIFFUSE_MIN, slope_y * light_dir[1] + slope_z * light_dir[2])
        UP_VECTOR = np.array([0, 0, 1], dtype=np.float32)
        half_vec = (light_dir + UP_VECTOR)
        half_vec /= np.linalg.norm(half_vec)
        SPEC_POWER = 1.0 / 0.35
        SPEC_STRENGTH = 0.8
        specular = (np.maximum(0, slope_y * half_vec[1] + slope_z * half_vec[2]) ** SPEC_POWER) * SPEC_STRENGTH

        rgb_final = np.zeros((upscale_height, upscale_width, 3), dtype=np.float32)
        TOP_SPLIT_RATIO = 0.92
        split_x_idx = int(upscale_width * TOP_SPLIT_RATIO)
        
        GROOVE_AO_FACTOR = 0.66
        MAX_RGB = 255
        top_shading = base_rgb * (diffuse + groove_value)[:, np.newaxis] * (ambient_occlusion * (1.0 + groove_value * GROOVE_AO_FACTOR))[:, np.newaxis] + MAX_RGB * specular[:, np.newaxis]
        rgb_final[:, :split_x_idx, :] = top_shading[:, np.newaxis, :]
        
        SIDE_DIFF_MIN = 0.35
        SIDE_LIGHT_WEIGHT_1 = 0.8
        SIDE_LIGHT_WEIGHT_2 = 0.2
        SIDE_AO_DIM = 0.9
        side_diffuse = np.maximum(SIDE_DIFF_MIN, SIDE_LIGHT_WEIGHT_1 * light_dir[0] + SIDE_LIGHT_WEIGHT_2 * slope_z[:, np.newaxis] * light_dir[2])
        rgb_final[:, split_x_idx:, :] = (base_rgb * side_diffuse * (ambient_occlusion * SIDE_AO_DIM)[:, np.newaxis])[:, np.newaxis, :]

        LINE_WIDTH_BASE = 3
        center_y_idx = upscale_height // 2
        indicator_line_height = max(2, LINE_WIDTH_BASE * UPSCALE_FACTOR)
        is_indicator_line = (np.arange(upscale_height) >= (center_y_idx - indicator_line_height // 2)) & \
                            (np.arange(upscale_height) <= (center_y_idx + indicator_line_height // 2))
        
        LINE_BRIGHTNESS_BASE = 0.4
        LINE_DIFF_WEIGHT = 0.8
        MAX_RGB = 255
        rgb_final[is_indicator_line, :, :] = np.minimum(MAX_RGB, MAX_RGB * ((diffuse + groove_value)[is_indicator_line, np.newaxis, np.newaxis] * LINE_DIFF_WEIGHT + LINE_BRIGHTNESS_BASE))

        surface_image = Image.fromarray(np.clip(rgb_final, 0, MAX_RGB).astype(np.uint8), 'RGB').convert("RGBA")
        mask_image = Image.new("L", (upscale_width, upscale_height), 0)
        CORNER_RADIUS_BASE = 3
        ImageDraw.Draw(mask_image).rounded_rectangle((0, 0, upscale_width, upscale_height), radius=CORNER_RADIUS_BASE*UPSCALE_FACTOR, fill=MAX_RGB)
        
        final_body = Image.new("RGBA", (upscale_width, upscale_height), (0,0,0,0))
        final_body.paste(surface_image, (0,0), mask_image)
        final_body = final_body.resize((width, height), Image.Resampling.LANCZOS)
        
        SHADOW_PADDING = 8
        canvas_img = Image.new("RGBA", (width + SHADOW_PADDING*2, height + SHADOW_PADDING*2), (0,0,0,0))
        SHADOW_OFFSET_X, SHADOW_OFFSET_Y = 2, 4
        SHADOW_RADIUS = 4
        SHADOW_ALPHA = 140
        ImageDraw.Draw(canvas_img).rounded_rectangle(
            (SHADOW_PADDING+SHADOW_OFFSET_X, SHADOW_PADDING+SHADOW_OFFSET_Y, 
             SHADOW_PADDING+width+SHADOW_OFFSET_X, SHADOW_PADDING+height+SHADOW_OFFSET_Y), 
            radius=SHADOW_RADIUS, fill=(0,0,0,SHADOW_ALPHA)
        )
        
        canvas_img = canvas_img.filter(ImageFilter.GaussianBlur(radius=SHADOW_RADIUS))
        canvas_img.paste(final_body, (SHADOW_PADDING, SHADOW_PADDING), final_body)
        
        photo = ImageTk.PhotoImage(canvas_img)
        _FADER_BAR_ASSET_CACHE[cache_key] = photo
        return photo
