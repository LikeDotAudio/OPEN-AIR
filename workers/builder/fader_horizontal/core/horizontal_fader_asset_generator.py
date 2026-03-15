import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from workers.logger.logger import builder_logger

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True
_HORIZONTAL_FADER_ASSET_CACHE = {}

class HorizontalFaderAssetGenerator:
    """Generates photorealistic horizontal concave saddle fader caps using NumPy vectorization with caching."""

    @classmethod
    def get_3d_cap(cls, w, h, body_color, track_color, highlight_color=None):
        cache_key = (w, h, body_color, track_color, highlight_color, "v23_vectorized")
        if cache_key in _HORIZONTAL_FADER_ASSET_CACHE: return _HORIZONTAL_FADER_ASSET_CACHE[cache_key]

        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🖼️🎨 [ASSET] Generating NEW 3D horizontal fader cap: {w}x{h}")
        upscale = 2; uw, uh = int(w*upscale), int(h*upscale)
        if uw < 1: uw = 1
        if uh < 1: uh = 1
        
        def htr(hs):
            hs = hs.lstrip('#')
            if len(hs) == 3: hs = "".join([c*2 for c in hs])
            return np.array([int(hs[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)

        try: b_rgb = htr(body_color)
        except: b_rgb = np.array([120, 120, 120], dtype=np.float32)
        
        xc = np.linspace(0, 1, uw, dtype=np.float32).reshape(1, uw)
        sx, sz = np.zeros((1, uw), dtype=np.float32), np.ones((1, uw), dtype=np.float32)

        sx[xc < 0.10], sz[xc < 0.10] = -1.0, 0.0
        m02 = (xc >= 0.10) & (xc < 0.20); sx[m02], sz[m02] = -0.707, 0.707
        mc = (xc >= 0.25) & (xc < 0.75); t = (xc[mc]-0.25)/0.5; val = (t-0.5)*2.0*0.55; sx[mc] = val; sz[mc] = np.sqrt(np.maximum(0, 1.0-val**2))
        m09 = (xc >= 0.80) & (xc < 0.90); sx[m09], sz[m09] = 0.707, 0.707
        sx[xc >= 0.90], sz[xc >= 0.90] = 1.0, 0.0

        ld = np.array([0.3, -0.6, 0.8], dtype=np.float32); ld /= np.linalg.norm(ld)
        hv = (ld + np.array([0,0,1], dtype=np.float32)); hv /= np.linalg.norm(hv)
        diff, spec = np.maximum(0.25, sx*ld[0] + sz*ld[2]), np.power(np.maximum(0, sx*hv[0] + sz*hv[2]), 1.5)*0.3

        colors = b_rgb.reshape(1,1,3)*diff.reshape(1,uw,1) + (150*spec).reshape(1,uw,1)
        pix = np.tile(np.clip(colors, 0, 255).astype(np.uint8), (uh, 1, 1))
        
        line_w = max(2, upscale); h_col = htr(highlight_color) if highlight_color else np.array([40,40,180], dtype=np.float32)
        pix[:, (uw//2-line_w//2):(uw//2+line_w//2), :] = h_col.astype(np.uint8)

        surf = Image.fromarray(pix, mode="RGB").convert("RGBA")
        mask = Image.new("L", (uw, uh), 0); m_draw = ImageDraw.Draw(mask); m_draw.rounded_rectangle((0,0,uw,uh), radius=3*upscale, fill=255)
        sh = int(uh * 0.08); m_draw.ellipse((-uw//4, -sh, 5*uw//4, sh), fill=0); m_draw.ellipse((-uw//4, uh-sh, 5*uw//4, uh+sh), fill=0)

        res = Image.new("RGBA", (uw, uh), (0,0,0,0)); res.paste(surf, (0,0), mask); res = res.resize((int(w), int(h)), Image.Resampling.LANCZOS)
        
        pad = 10; canv = Image.new("RGBA", (int(w)+pad*2, int(h)+pad*2), (0,0,0,0))
        shad = Image.new("RGBA", canv.size, (0,0,0,0)); ImageDraw.Draw(shad).rounded_rectangle((pad+4, pad+6, pad+int(w)+4, pad+int(h)+6), radius=4, fill=(0,0,0,110))
        canv.paste(shad.filter(ImageFilter.GaussianBlur(radius=3.5)), (0,0)); canv.paste(res, (pad, pad), res)
        
        photo = ImageTk.PhotoImage(canv); _HORIZONTAL_FADER_ASSET_CACHE[cache_key] = photo
        return photo
