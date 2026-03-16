from PIL import Image, ImageDraw, ImageTk, ImageFilter
from workers.logger.logger import builder_logger

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    

_GCA_ASSET_CACHE = {}

class GCAAssetGenerator:
    """Generates photorealistic 3D 'Bridge' caps for GCA arrays with caching."""

    @classmethod
    def get_3d_bridge(cls, w, h, body_color, outline_color):
        cache_key = (w, h, body_color, outline_color)
        if cache_key in _GCA_ASSET_CACHE:
            return _GCA_ASSET_CACHE[cache_key]

        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🖼️🎨 [ASSET] Generating NEW 3D GCA bridge: {w}x{h}")
        pad = 15
        full_w, full_h = w + pad*2, h + pad*2
        base = Image.new("RGBA", (full_w, full_h), (0,0,0,0))
        
        # 1. Drop Shadow
        shadow = Image.new("RGBA", (full_w, full_h), (0,0,0,0))
        s_draw = ImageDraw.Draw(shadow)
        s_draw.rounded_rectangle((pad+2, pad+4, pad+w+2, pad+h+4), radius=8, fill=(0,0,0,120))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=6))
        base = Image.alpha_composite(base, shadow)
        
        # 2. Main Body
        body = Image.new("RGBA", (full_w, full_h), (0,0,0,0))
        b_draw = ImageDraw.Draw(body)
        b_draw.rounded_rectangle((pad, pad, pad+w, pad+h), radius=8, fill=body_color, outline=outline_color, width=1)
        
        # Metallic Glint
        b_draw.line((pad+6, pad+1, pad+w-6, pad+1), fill=(255,255,255,100), width=1)
        b_draw.line((pad+1, pad+6, pad+1, pad+h-6), fill=(255,255,255,50), width=1)
        b_draw.line((pad+6, pad+h-1, pad+w-6, pad+h-1), fill=(0,0,0,80), width=1)
        
        # 3. Inner Screen Area
        screen_pad = 4
        b_draw.rounded_rectangle((pad+screen_pad, pad+screen_pad, pad+w-screen_pad, pad+h-screen_pad), radius=4, fill="#000000")
        b_draw.line((pad+screen_pad+1, pad+screen_pad+1, pad+w-screen_pad-1, pad+screen_pad+1), fill=(40,40,40,255), width=1)

        base = Image.alpha_composite(base, body)
        
        # 4. Gloss
        gloss = Image.new("RGBA", (full_w, full_h), (0,0,0,0))
        g_draw = ImageDraw.Draw(gloss)
        g_draw.rounded_rectangle((pad+2, pad+2, pad+w-2, pad+h//2), radius=6, fill=(255,255,255,15))
        base = Image.alpha_composite(base, gloss)

        photo = ImageTk.PhotoImage(base)
        _GCA_ASSET_CACHE[cache_key] = photo
        return photo
