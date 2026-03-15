import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from workers.logger.logger import builder_logger

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True
_FADER_BAR_ASSET_CACHE = {}

class FaderBarAssetGenerator:
    """Generates photorealistic saddle fader caps using NumPy vectorization with caching."""

    @classmethod
    def get_3d_cap(cls, w, h, body_color, outline_color):
        cache_key = (w, h, body_color, outline_color, "v7_vectorized")
        if cache_key in _FADER_BAR_ASSET_CACHE: return _FADER_BAR_ASSET_CACHE[cache_key]

        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🖼️🎨 [ASSET] Generating NEW 3D fader cap: {w}x{h}")
        upscale = 2; uw, uh = w * upscale, h * upscale
        
        def hex_to_rgb(s):
            s = s.lstrip('#')
            return np.array([int(s[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)

        try: b_rgb = hex_to_rgb(body_color)
        except: b_rgb = np.array([40, 40, 40], dtype=np.float32)
        
        base_rgb = 0.7 * np.array([30, 30, 30], dtype=np.float32) + 0.3 * b_rgb
        light_dir = np.array([0.3, -0.6, 0.8], dtype=np.float32); light_dir /= np.linalg.norm(light_dir)
        
        ny = np.linspace(0, 1, uh, dtype=np.float32)
        slope_y, slope_z = np.zeros(uh, dtype=np.float32), np.zeros(uh, dtype=np.float32)
        
        # Profile Logic (1D masks)
        m1 = ny < 0.10; slope_y[m1], slope_z[m1] = -1.0, 0.0
        m2 = (ny >= 0.10) & (ny < 0.20); slope_y[m2], slope_z[m2] = -0.707, 0.707
        m3 = (ny >= 0.20) & (ny < 0.25); slope_y[m3], slope_z[m3] = 0.0, 1.0
        m4 = (ny >= 0.25) & (ny < 0.75); t = (ny[m4]-0.25)/0.5; sy = (t-0.5)*2.0*0.55; slope_y[m4] = sy; slope_z[m4] = np.sqrt(np.maximum(0, 1.0-sy**2))
        m5 = (ny >= 0.75) & (ny < 0.80); slope_y[m5], slope_z[m5] = 0.0, 1.0
        m6 = (ny >= 0.80) & (ny < 0.90); slope_y[m6], slope_z[m6] = 0.707, 0.707
        m7 = (ny >= 0.90); slope_y[m7], slope_z[m7] = 1.0, 0.0

        ao = np.ones(uh, dtype=np.float32); dist = 1.0 - (np.abs(ny-0.5)/0.25); ao[m4] = 1.0 - (np.maximum(0, dist[m4])*0.4)
        tg = (ny-0.22)/0.56; gv = np.where((ny>0.22) & (ny<0.78), np.sin(tg*np.pi*14 - np.pi/2)*0.12, 0)
        
        diff = np.maximum(0.25, slope_y*light_dir[1] + slope_z*light_dir[2])
        h_vec = (light_dir + np.array([0,0,1], dtype=np.float32)); h_vec /= np.linalg.norm(h_vec)
        spec = (np.maximum(0, slope_y*h_vec[1] + slope_z*h_vec[2])**(1.0/0.35))*0.8

        rgb_final = np.zeros((uh, uw, 3), dtype=np.float32); split_x = int(uw*0.92)
        top_shading = base_rgb * (diff + gv)[:,None] * (ao*(1.0+gv*0.66))[:,None] + 255*spec[:,None]
        rgb_final[:, :split_x, :] = top_shading[:,None,:]
        side_diff = np.maximum(0.35, 0.8*light_dir[0] + 0.2*slope_z[:,None]*light_dir[2])
        rgb_final[:, split_x:, :] = (base_rgb * side_diff * (ao*0.9)[:,None])[:,None,:]

        line_h, cy = max(2, 3*upscale), uh//2
        is_line = (np.arange(uh) >= (cy-line_h//2)) & (np.arange(uh) <= (cy+line_h//2))
        rgb_final[is_line, :, :] = np.minimum(255, 255*((diff+gv)[is_line, None, None]*0.8+0.4))

        surface = Image.fromarray(np.clip(rgb_final, 0, 255).astype(np.uint8), 'RGB').convert("RGBA")
        mask = Image.new("L", (uw, uh), 0); ImageDraw.Draw(mask).rounded_rectangle((0,0,uw,uh), radius=3*upscale, fill=255)
        body = Image.new("RGBA", (uw, uh), (0,0,0,0)); body.paste(surface, (0,0), mask); body = body.resize((w, h), Image.Resampling.LANCZOS)
        
        pad = 8; canv = Image.new("RGBA", (w+pad*2, h+pad*2), (0,0,0,0))
        ImageDraw.Draw(canv).rounded_rectangle((pad+2, pad+4, pad+w+2, pad+h+4), radius=4, fill=(0,0,0,140))
        canv = canv.filter(ImageFilter.GaussianBlur(radius=4)); canv.paste(body, (pad, pad), body)
        
        photo = ImageTk.PhotoImage(canv); _FADER_BAR_ASSET_CACHE[cache_key] = photo
        return photo
