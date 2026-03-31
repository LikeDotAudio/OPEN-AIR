# Core/ltp_asset_generator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import math
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from oaLogging.Core.logger import builder_logger

# --- Standard Debug Logging Setup ---
_LTP_ASSET_CACHE = {}

class LTPAssetGenerator:
    """Generates photorealistic 3D knob images for the LTP handle with caching."""

    @classmethod
    def get_3d_knob(cls, radius, body_color, outline_color, shape="circle", teeth=12):
        cache_key = (radius, body_color, outline_color, shape, teeth, "next_gen_ltp_v6")
        if cache_key in _LTP_ASSET_CACHE:
            return _LTP_ASSET_CACHE[cache_key]

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🏗️🖼️🎨 [ASSET] Generating NEW 3D LTP knob asset: {radius}px", level="TRACE")
        
        def hex_to_rgb(hex_str):
            if not isinstance(hex_str, str) or not hex_str.startswith("#"): return (40,40,40)
            h = hex_str.lstrip('#')
            if len(h) == 3: h = "".join([c*2 for c in h])
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        b_rgb = hex_to_rgb(body_color)
        base_rgb = tuple(int(0.7 * 30 + 0.3 * c) for c in b_rgb)
        fill_col = f"#{base_rgb[0]:02x}{base_rgb[1]:02x}{base_rgb[2]:02x}"

        pad = 15
        diameter = radius * 2
        full_w, full_h = diameter + pad*2, diameter + pad*2
        base = Image.new("RGBA", (full_w, full_h), (0,0,0,0))
        cx, cy = full_w // 2, full_h // 2
        
        def draw_shape(draw_obj, r, fill=None, outline=None, width=1, offset=(0,0)):
            ocx, ocy = cx + offset[0], cy + offset[1]
            if shape == "octagon":
                pts = [(ocx + r * math.cos(math.radians(i*45+22.5)), ocy + r * math.sin(math.radians(i*45+22.5))) for i in range(8)]
                draw_obj.polygon(pts, fill=fill, outline=outline, width=width)
            elif shape == "gear":
                pts = []
                for i in range(teeth * 2):
                    ang = math.radians(i * (360/(teeth*2)))
                    cr = r if i % 2 == 0 else r * 0.85
                    pts.append((ocx + cr * math.cos(ang), ocy + cr * math.sin(ang)))
                draw_obj.polygon(pts, fill=fill, outline=outline, width=width)
            else: draw_obj.ellipse((ocx-r, ocy-r, ocx+r, ocy+r), fill=fill, outline=outline, width=width)

        # 1. Drop Shadow
        shadow = Image.new("RGBA", (full_w, full_h), (0,0,0,0))
        draw_shape(ImageDraw.Draw(shadow), radius, fill=(0,0,0,150), offset=(4,5))
        base = Image.alpha_composite(base, shadow.filter(ImageFilter.GaussianBlur(radius=5)))
        
        # 2. Main Body
        body = Image.new("RGBA", (full_w, full_h), (0,0,0,0))
        b_draw = ImageDraw.Draw(body)
        draw_shape(b_draw, radius, fill=fill_col, outline=outline_color, width=1)
        draw_shape(b_draw, radius-2, outline=(255,255,255,60), width=1)
        base = Image.alpha_composite(base, body)
        
        # 3. Top Face (Gloss)
        face = Image.new("RGBA", (full_w, full_h), (0,0,0,0))
        draw_shape(ImageDraw.Draw(face), radius-4, fill=(255,255,255,15))
        base = Image.alpha_composite(base, face)

        photo = ImageTk.PhotoImage(base)
        _LTP_ASSET_CACHE[cache_key] = photo
        return photo
