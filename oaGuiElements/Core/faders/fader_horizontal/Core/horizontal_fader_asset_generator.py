import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from oaLogging.Core.logger import builder_logger

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True
_HORIZONTAL_FADER_ASSET_CACHE = {}

class HorizontalFaderAssetGenerator:
    """Generates photorealistic horizontal concave saddle fader caps using NumPy vectorization with caching."""

    @classmethod
    def get_3d_cap(cls, width, height, body_color, track_color, highlight_color=None):
        cache_key = (width, height, body_color, track_color, highlight_color, "v23_vectorized")
        if cache_key in _HORIZONTAL_FADER_ASSET_CACHE: return _HORIZONTAL_FADER_ASSET_CACHE[cache_key]

        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🖼️🎨 [ASSET] Generating NEW 3D horizontal fader cap: {width}x{height}")
        UPSCALE_FACTOR = 2
        upscaled_width, upscaled_height = int(width * UPSCALE_FACTOR), int(height * UPSCALE_FACTOR)
        if upscaled_width < 1: upscaled_width = 1
        if upscaled_height < 1: upscaled_height = 1
        
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
        
        normalized_x = np.linspace(0, 1, upscaled_width, dtype=np.float32).reshape(1, upscaled_width)
        slope_x, slope_z = np.zeros((1, upscaled_width), dtype=np.float32), np.ones((1, upscaled_width), dtype=np.float32)

        SLOPE_THRESHOLD_1 = 0.10
        SLOPE_THRESHOLD_2 = 0.20
        SLOPE_THRESHOLD_3 = 0.25
        SLOPE_THRESHOLD_4 = 0.75
        SLOPE_THRESHOLD_5 = 0.80
        SLOPE_THRESHOLD_6 = 0.90

        slope_x[normalized_x < SLOPE_THRESHOLD_1], slope_z[normalized_x < SLOPE_THRESHOLD_1] = -1.0, 0.0
        mask_slope_2 = (normalized_x >= SLOPE_THRESHOLD_1) & (normalized_x < SLOPE_THRESHOLD_2)
        slope_x[mask_slope_2], slope_z[mask_slope_2] = -0.707, 0.707
        
        mask_center = (normalized_x >= SLOPE_THRESHOLD_3) & (normalized_x < SLOPE_THRESHOLD_4)
        PROFILE_CENTER_SCALE = 0.5
        PROFILE_OFFSET = 0.5
        PROFILE_AMPLITUDE = 2.0
        PROFILE_CURVATURE = 0.55
        profile_t = (normalized_x[mask_center] - SLOPE_THRESHOLD_3) / PROFILE_CENTER_SCALE
        slope_x_val = (profile_t - PROFILE_OFFSET) * PROFILE_AMPLITUDE * PROFILE_CURVATURE
        slope_x[mask_center] = slope_x_val
        slope_z[mask_center] = np.sqrt(np.maximum(0, 1.0 - slope_x_val**2))
        
        mask_slope_9 = (normalized_x >= SLOPE_THRESHOLD_5) & (normalized_x < SLOPE_THRESHOLD_6)
        slope_x[mask_slope_9], slope_z[mask_slope_9] = 0.707, 0.707
        slope_x[normalized_x >= SLOPE_THRESHOLD_6], slope_z[normalized_x >= SLOPE_THRESHOLD_6] = 1.0, 0.0

        LIGHT_DIR_X, LIGHT_DIR_Y, LIGHT_DIR_Z = 0.3, -0.6, 0.8
        light_dir = np.array([LIGHT_DIR_X, LIGHT_DIR_Y, LIGHT_DIR_Z], dtype=np.float32)
        light_dir /= np.linalg.norm(light_dir)
        
        UP_VECTOR = np.array([0, 0, 1], dtype=np.float32)
        half_vector = (light_dir + UP_VECTOR)
        half_vector /= np.linalg.norm(half_vector)
        
        DIFFUSE_MIN = 0.25
        diffuse = np.maximum(DIFFUSE_MIN, slope_x * light_dir[0] + slope_z * light_dir[2])
        SPEC_POWER = 1.5
        SPEC_STRENGTH = 0.3
        specular = np.power(np.maximum(0, slope_x * half_vector[0] + slope_z * half_vector[2]), SPEC_POWER) * SPEC_STRENGTH

        SPEC_COLOR_SCALE = 150
        colors = body_rgb.reshape(1, 1, 3) * diffuse.reshape(1, upscaled_width, 1) + (SPEC_COLOR_SCALE * specular).reshape(1, upscaled_width, 1)
        pixel_data = np.tile(np.clip(colors, 0, 255).astype(np.uint8), (upscaled_height, 1, 1))
        
        indicator_line_width = max(2, UPSCALE_FACTOR)
        HIGHLIGHT_FALLBACK_RGB = np.array([40, 40, 180], dtype=np.float32)
        highlight_rgb = convert_hex_to_rgb(highlight_color) if highlight_color else HIGHLIGHT_FALLBACK_RGB
        pixel_data[:, (upscaled_width // 2 - indicator_line_width // 2):(upscaled_width // 2 + indicator_line_width // 2), :] = highlight_rgb.astype(np.uint8)

        surface_image = Image.fromarray(pixel_data, mode="RGB").convert("RGBA")
        mask_image = Image.new("L", (upscaled_width, upscaled_height), 0)
        mask_draw = ImageDraw.Draw(mask_image)
        CORNER_RADIUS_BASE = 3
        mask_draw.rounded_rectangle((0, 0, upscaled_width, upscaled_height), radius=CORNER_RADIUS_BASE * UPSCALE_FACTOR, fill=255)
        
        SHADOW_HEIGHT_RATIO = 0.08
        shadow_height = int(upscaled_height * SHADOW_HEIGHT_RATIO)
        mask_draw.ellipse((-upscaled_width // 4, -shadow_height, 5 * upscaled_width // 4, shadow_height), fill=0)
        mask_draw.ellipse((-upscaled_width // 4, upscaled_height - shadow_height, 5 * upscaled_width // 4, upscaled_height + shadow_height), fill=0)

        result_image = Image.new("RGBA", (upscaled_width, upscaled_height), (0, 0, 0, 0))
        result_image.paste(surface_image, (0, 0), mask_image)
        result_image = result_image.resize((int(width), int(height)), Image.Resampling.LANCZOS)
        
        shadow_padding = 10
        canvas_image = Image.new("RGBA", (int(width) + shadow_padding * 2, int(height) + shadow_padding * 2), (0, 0, 0, 0))
        shadow_image = Image.new("RGBA", canvas_image.size, (0, 0, 0, 0))
        SHADOW_OFFSET_X, SHADOW_OFFSET_Y = 4, 6
        SHADOW_RADIUS = 4
        SHADOW_ALPHA = 110
        ImageDraw.Draw(shadow_image).rounded_rectangle(
            (shadow_padding + SHADOW_OFFSET_X, shadow_padding + SHADOW_OFFSET_Y, 
             shadow_padding + int(width) + SHADOW_OFFSET_X, shadow_padding + int(height) + SHADOW_OFFSET_Y), 
            radius=SHADOW_RADIUS, fill=(0, 0, 0, SHADOW_ALPHA)
        )
        
        BLUR_RADIUS = 3.5
        canvas_image.paste(shadow_image.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS)), (0, 0))
        canvas_image.paste(result_image, (shadow_padding, shadow_padding), result_image)
        
        photo = ImageTk.PhotoImage(canvas_image)
        _HORIZONTAL_FADER_ASSET_CACHE[cache_key] = photo
        return photo
