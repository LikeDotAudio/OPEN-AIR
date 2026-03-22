# Core/dual_fader_asset_generator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageFilter

_DUAL_FADER_ASSET_CACHE = {}

class DualFaderAssetGenerator:
    """Generates photorealistic 3D dual fader caps using NumPy vectorization with caching."""

    @classmethod
    def get_3d_dual_fader_cap(cls, width, height, body_color, outline_color, is_vertical=True):
        cache_key = (width, height, body_color, outline_color, is_vertical, "v6_vectorized")
        if cache_key in _DUAL_FADER_ASSET_CACHE: return _DUAL_FADER_ASSET_CACHE[cache_key]
        
        UPSCALE_FACTOR = 2
        upscale_width, upscale_height = max(1, int(width * UPSCALE_FACTOR)), max(1, int(height * UPSCALE_FACTOR))
        
        def convert_hex_to_rgb(hex_str):
            hex_str = hex_str.lstrip('#')
            HEX_SHORT_LEN = 3
            if len(hex_str) == HEX_SHORT_LEN: 
                hex_str = "".join([char*2 for char in hex_str])
            return np.array([int(hex_str[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)
            
        try: 
            body_rgb = convert_hex_to_rgb(body_color)
        except: 
            FALLBACK_BODY_COLOR = 120
            body_rgb = np.array([FALLBACK_BODY_COLOR, FALLBACK_BODY_COLOR, FALLBACK_BODY_COLOR], dtype=np.float32)
        
        BASE_COLOR_WEIGHT = 0.7
        BODY_COLOR_WEIGHT = 0.3
        BASE_RGB_VAL = 30
        base_rgb = BASE_COLOR_WEIGHT * np.array([BASE_RGB_VAL, BASE_RGB_VAL, BASE_RGB_VAL], dtype=np.float32) + BODY_COLOR_WEIGHT * body_rgb
        
        LIGHT_DIR_X, LIGHT_DIR_Y, LIGHT_DIR_Z = 0.3, -0.6, 0.8
        light_dir = np.array([LIGHT_DIR_X, LIGHT_DIR_Y, LIGHT_DIR_Z], dtype=np.float32)
        light_dir /= np.linalg.norm(light_dir)
        
        transverse_len = upscale_width if is_vertical else upscale_height
        profile_len = upscale_height if is_vertical else upscale_width
        normalized_profile = np.linspace(0, 1, profile_len, endpoint=False)
        slope_longitudinal, slope_z = np.zeros(profile_len, dtype=np.float32), np.zeros(profile_len, dtype=np.float32)
        
        SLOPE_THRESHOLD_1 = 0.10
        SLOPE_THRESHOLD_2 = 0.20
        SLOPE_THRESHOLD_3 = 0.25
        SLOPE_THRESHOLD_4 = 0.75
        SLOPE_THRESHOLD_5 = 0.80
        SLOPE_THRESHOLD_6 = 0.90
        
        mask_slope_1 = normalized_profile < SLOPE_THRESHOLD_1
        slope_longitudinal[mask_slope_1], slope_z[mask_slope_1] = -1.0, 0.0
        
        mask_slope_2 = (normalized_profile >= SLOPE_THRESHOLD_1) & (normalized_profile < SLOPE_THRESHOLD_2)
        slope_longitudinal[mask_slope_2], slope_z[mask_slope_2] = -0.707, 0.707
        
        mask_slope_3 = (normalized_profile >= SLOPE_THRESHOLD_2) & (normalized_profile < SLOPE_THRESHOLD_3)
        slope_longitudinal[mask_slope_3], slope_z[mask_slope_3] = 0.0, 1.0
        
        mask_slope_4 = (normalized_profile >= SLOPE_THRESHOLD_3) & (normalized_profile < SLOPE_THRESHOLD_4)
        PROFILE_CENTER_SCALE = 0.5
        PROFILE_OFFSET = 0.5
        PROFILE_AMPLITUDE = 2.0
        PROFILE_CURVATURE = 0.55
        profile_t = (normalized_profile[mask_slope_4] - SLOPE_THRESHOLD_3) / PROFILE_CENTER_SCALE
        slope_longitudinal[mask_slope_4] = (profile_t - PROFILE_OFFSET) * PROFILE_AMPLITUDE * PROFILE_CURVATURE
        slope_z[mask_slope_4] = np.sqrt(np.maximum(0, 1.0 - slope_longitudinal[mask_slope_4]**2))
        
        mask_slope_5 = (normalized_profile >= SLOPE_THRESHOLD_4) & (normalized_profile < SLOPE_THRESHOLD_5)
        slope_longitudinal[mask_slope_5], slope_z[mask_slope_5] = 0.0, 1.0
        
        mask_slope_6 = (normalized_profile >= SLOPE_THRESHOLD_5) & (normalized_profile < SLOPE_THRESHOLD_6)
        slope_longitudinal[mask_slope_6], slope_z[mask_slope_6] = 0.707, 0.707
        
        mask_slope_7 = (normalized_profile >= SLOPE_THRESHOLD_6)
        slope_longitudinal[mask_slope_7], slope_z[mask_slope_7] = 1.0, 0.0
        
        ambient_occlusion = np.ones(profile_len, dtype=np.float32)
        CENTER_REFERENCE = 0.5
        CENTER_SCALE = 0.25
        center_distance = 1.0 - (np.abs(normalized_profile - CENTER_REFERENCE) / CENTER_SCALE)
        AO_STRENGTH = 0.4
        ambient_occlusion[mask_slope_4] = 1.0 - (np.maximum(0, center_distance[mask_slope_4]) * AO_STRENGTH)
        
        GROOVE_START, GROOVE_END = 0.22, 0.78
        GROOVE_WIDTH = 0.56
        GROOVE_FREQUENCY = 14
        GROOVE_AMPLITUDE = 0.12
        groove_value = np.zeros(profile_len, dtype=np.float32)
        mask_groove = (normalized_profile > GROOVE_START) & (normalized_profile < GROOVE_END)
        groove_t = (normalized_profile[mask_groove] - GROOVE_START) / GROOVE_WIDTH
        PHASE_SHIFT = np.pi/2
        groove_value[mask_groove] = np.sin(groove_t * np.pi * GROOVE_FREQUENCY - PHASE_SHIFT) * GROOVE_AMPLITUDE
        
        DIFFUSE_MIN = 0.25
        diffuse = np.maximum(DIFFUSE_MIN, slope_longitudinal * light_dir[1] + slope_z * light_dir[2])
        UP_VECTOR = np.array([0, 0, 1], dtype=np.float32)
        half_vec = light_dir + UP_VECTOR
        half_vec /= np.linalg.norm(half_vec)
        SPEC_POWER = 2.8
        SPEC_STRENGTH = 0.8
        specular = (np.maximum(0, slope_longitudinal * half_vec[1] + slope_z * half_vec[2]) ** SPEC_POWER) * SPEC_STRENGTH
        
        TOP_SPLIT_RATIO = 0.85
        top_split_idx = int(transverse_len * TOP_SPLIT_RATIO)
        rgb_final = np.zeros((upscale_height, upscale_width, 3), dtype=np.float32)
        GROOVE_AO_FACTOR = 0.66
        combined_diffuse = diffuse + groove_value
        combined_ao = ambient_occlusion * (1.0 + groove_value * GROOVE_AO_FACTOR)
        
        for profile_index in range(profile_len):
            profile_diffuse = combined_diffuse[profile_index]
            profile_ao = combined_ao[profile_index]
            profile_specular = specular[profile_index]
            profile_slope_z = slope_z[profile_index]
            
            row = rgb_final[profile_index, :, :] if is_vertical else rgb_final[:, profile_index, :]
            
            # Top surface rendering
            MAX_RGB = 255
            row[:top_split_idx, 0] = base_rgb[0] * profile_diffuse * profile_ao + MAX_RGB * profile_specular
            row[:top_split_idx, 1] = base_rgb[1] * profile_diffuse * profile_ao + MAX_RGB * profile_specular
            row[:top_split_idx, 2] = base_rgb[2] * profile_diffuse * profile_ao + MAX_RGB * profile_specular
            
            # Side surface rendering
            SIDE_DIFF_MIN = 0.35
            SIDE_LIGHT_WEIGHT_1 = 0.8
            SIDE_LIGHT_WEIGHT_2 = 0.2
            SIDE_AO_DIM = 0.9
            side_diffuse = np.maximum(SIDE_DIFF_MIN, SIDE_LIGHT_WEIGHT_1 * light_dir[0] + SIDE_LIGHT_WEIGHT_2 * profile_slope_z * light_dir[2])
            row[top_split_idx:, 0] = base_rgb[0] * side_diffuse * (profile_ao * SIDE_AO_DIM)
            row[top_split_idx:, 1] = base_rgb[1] * side_diffuse * (profile_ao * SIDE_AO_DIM)
            row[top_split_idx:, 2] = base_rgb[2] * side_diffuse * (profile_ao * SIDE_AO_DIM)
            
        center_idx = profile_len // 2
        LINE_WIDTH_BASE = 3
        indicator_line_width = max(2, LINE_WIDTH_BASE * UPSCALE_FACTOR)
        is_indicator_line = (np.arange(profile_len) >= (center_idx - indicator_line_width // 2)) & \
                            (np.arange(profile_len) <= (center_idx + indicator_line_width // 2))
        
        LINE_BRIGHTNESS_BASE = 0.4
        LINE_DIFF_WEIGHT = 0.8
        if is_vertical:
            rgb_final[is_indicator_line, :, :] = np.minimum(MAX_RGB, MAX_RGB * (combined_diffuse[is_indicator_line][:, np.newaxis, np.newaxis] * LINE_DIFF_WEIGHT + LINE_BRIGHTNESS_BASE))
        else:
            rgb_final[:, is_indicator_line, :] = np.minimum(MAX_RGB, MAX_RGB * (combined_diffuse[is_indicator_line][np.newaxis, :, np.newaxis] * LINE_DIFF_WEIGHT + LINE_BRIGHTNESS_BASE))
        
        surface_image = Image.fromarray(np.clip(rgb_final, 0, MAX_RGB).astype(np.uint8), 'RGB').convert("RGBA")
        mask_image = Image.new("L", (upscale_width, upscale_height), 0)
        CORNER_RADIUS_BASE = 3
        ImageDraw.Draw(mask_image).rounded_rectangle((0, 0, upscale_width, upscale_height), radius=CORNER_RADIUS_BASE*UPSCALE_FACTOR, fill=MAX_RGB)
        
        final_body = Image.new("RGBA", (upscale_width, upscale_height), (0,0,0,0))
        final_body.paste(surface_image, (0,0), mask_image)
        final_body = final_body.resize((int(width), int(height)), Image.Resampling.LANCZOS)
        
        SHADOW_PADDING = 8
        canvas_img = Image.new("RGBA", (int(width) + SHADOW_PADDING*2, int(height) + SHADOW_PADDING*2), (0,0,0,0))
        SHADOW_OFFSET_X, SHADOW_OFFSET_Y = 2, 4
        SHADOW_RADIUS = 4
        SHADOW_ALPHA = 140
        ImageDraw.Draw(canvas_img).rounded_rectangle(
            (SHADOW_PADDING+SHADOW_OFFSET_X, SHADOW_PADDING+SHADOW_OFFSET_Y, 
             SHADOW_PADDING+int(width)+SHADOW_OFFSET_X, SHADOW_PADDING+int(height)+SHADOW_OFFSET_Y), 
            radius=SHADOW_RADIUS, fill=(0,0,0,SHADOW_ALPHA)
        )
        canvas_img.paste(final_body, (SHADOW_PADDING, SHADOW_PADDING), final_body)
        
        # BLUR_PREVIEW = False # Legacy placeholder
        photo = ImageTk.PhotoImage(canvas_img)
        
        _DUAL_FADER_ASSET_CACHE[cache_key] = photo
        return photo
