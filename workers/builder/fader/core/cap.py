# workers/builder/fader/core/cap.py

import math
import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageFilter

# --- Module Level Cache for 3D Assets ---
_FADER_ASSET_CACHE = {}

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

        upscale = 2 # Reduced upscale for speed, still look great with Lanczos
        uw, uh = w * upscale, h * upscale
        
        def hex_to_rgb(hex_str):
            hex_str = hex_str.lstrip('#')
            return np.array([int(hex_str[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)

        try: b_rgb = hex_to_rgb(body_color)
        except: b_rgb = np.array([40, 40, 40], dtype=np.float32)

        # 1. Create coordinate grids
        y_coords = np.linspace(0, 1, uh, dtype=np.float32).reshape(uh, 1)
        
        # 2. Vectorized Slope Logic
        slope_y = np.zeros((uh, 1), dtype=np.float32)
        slope_z = np.ones((uh, 1), dtype=np.float32)

        # Define zones
        slope_y[y_coords < 0.10] = -1.0
        slope_z[y_coords < 0.10] = 0.0
        
        mask_02 = (y_coords >= 0.10) & (y_coords < 0.20)
        slope_y[mask_02] = -0.707
        slope_z[mask_02] = 0.707
        
        mask_concave = (y_coords >= 0.25) & (y_coords < 0.75)
        t = (y_coords[mask_concave] - 0.25) / 0.5
        local_t = (t - 0.5) * 2.0
        slope_y[mask_concave] = local_t * 0.55
        slope_z[mask_concave] = np.sqrt(np.maximum(0, 1.0 - slope_y[mask_concave]**2))

        mask_09 = (y_coords >= 0.80) & (y_coords < 0.90)
        slope_y[mask_09] = 0.707
        slope_z[mask_09] = 0.707
        
        slope_y[y_coords >= 0.90] = 1.0
        slope_z[y_coords >= 0.90] = 0.0

        # 3. Vectorized Lighting
        light_dir = np.array([0.3, -0.6, 0.8], dtype=np.float32)
        light_dir /= np.linalg.norm(light_dir)
        
        ambient = 0.25
        diffuse = np.maximum(ambient, slope_y * light_dir[1] + slope_z * light_dir[2])
        
        h_vec = light_dir + np.array([0, 0, 1], dtype=np.float32)
        h_vec /= np.linalg.norm(h_vec)
        spec_dot = np.maximum(0, slope_y * h_vec[1] + slope_z * h_vec[2])
        spec = np.power(spec_dot, 1.5) * 0.3 # Reduced spec power for matte look

        # 4. Ambient Occlusion & Grooves
        ao = np.ones((uh, 1), dtype=np.float32)
        dist = 1.0 - (np.abs(y_coords - 0.5) / 0.25)
        ao[mask_concave] = 1.0 - (np.maximum(0, dist[mask_concave]) * 0.4)
        
        groove_val = np.sin(((y_coords - 0.22) / 0.56) * np.pi * 14 - np.pi/2)
        is_groove = (y_coords > 0.22) & (y_coords < 0.78)
        
        # Apply grooves to diffuse and AO
        diffuse[is_groove] += groove_val[is_groove] * 0.12
        ao[is_groove] *= (1.0 + groove_val[is_groove] * 0.08)

        # 5. Final Color Calculation (UW x UH x 3)
        # R = base_rgb[0] * diffuse * ao + 150 * spec
        colors = b_rgb.reshape(1, 1, 3) * (diffuse * ao).reshape(uh, 1, 1) + (150 * spec).reshape(uh, 1, 1)
        colors = np.clip(colors, 0, 255).astype(np.uint8)
        
        # Tile across width
        pixel_data = np.tile(colors, (1, uw, 1))
        
        # 6. Indicator Line
        cy = uh // 2
        line_h = max(2, upscale)
        if highlight_color:
            h_rgb = hex_to_rgb(highlight_color).astype(np.uint8)
            pixel_data[cy - line_h//2 : cy + line_h//2, :] = h_rgb
        else:
            pixel_data[cy - line_h//2 : cy + line_h//2, :] = [40, 40, 180]

        surface = Image.fromarray(pixel_data, mode="RGB").convert("RGBA")

        # 7. Masking & Shadow
        mask = Image.new("L", (uw, uh), 0)
        m_draw = ImageDraw.Draw(mask)
        m_draw.rounded_rectangle((0, 0, uw, uh), radius=3*upscale, fill=255)
        scoop_w = int(uw * 0.15) 
        m_draw.ellipse((-scoop_w, -uh//4, scoop_w, 5*uh//4), fill=0) 
        m_draw.ellipse((uw - scoop_w, -uh//4, uw + scoop_w, 5*uh//4), fill=0) 

        surface_final = Image.new("RGBA", (uw, uh), (0,0,0,0))
        surface_final.paste(surface, (0,0), mask)
        surface_final = surface_final.resize((w, h), Image.Resampling.LANCZOS)
        
        pad_x, pad_y = 10, 15
        canvas_img = Image.new("RGBA", (w + pad_x*2, h + pad_y*2), (0,0,0,0))
        
        shadow_layer = Image.new("RGBA", canvas_img.size, (0,0,0,0))
        s_draw = ImageDraw.Draw(shadow_layer)
        s_draw.rounded_rectangle((pad_x+4, pad_y+10, pad_x+w+4, pad_y+h+10), radius=4, fill=(0,0,0,110))
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=3.5))
        
        canvas_img.paste(shadow_layer, (0,0), shadow_layer)
        canvas_img.paste(surface_final, (pad_x, pad_y), surface_final)
        
        photo = ImageTk.PhotoImage(canvas_img)
        _FADER_ASSET_CACHE[cache_key] = photo
        return photo
