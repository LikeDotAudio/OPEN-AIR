import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageFilter

_DUAL_FADER_ASSET_CACHE = {}

class DualFaderAssetGenerator:
    """Generates photorealistic 3D dual fader caps using NumPy vectorization with caching."""

    @classmethod
    def get_3d_dual_fader_cap(cls, w, h, body_color, outline_color, is_vertical=True):
        cache_key = (w, h, body_color, outline_color, is_vertical, "v6_vectorized")
        if cache_key in _DUAL_FADER_ASSET_CACHE: return _DUAL_FADER_ASSET_CACHE[cache_key]
        
        upscale = 2; uw, uh = max(1, int(w * upscale)), max(1, int(h * upscale))
        
        def hex_to_rgb(hex_str):
            hex_str = hex_str.lstrip('#')
            if len(hex_str) == 3: hex_str = "".join([c*2 for c in hex_str])
            return np.array([int(hex_str[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)
            
        try: b_rgb = hex_to_rgb(body_color)
        except: b_rgb = np.array([120, 120, 120], dtype=np.float32)
        
        base_rgb = 0.7 * np.array([30, 30, 30], dtype=np.float32) + 0.3 * b_rgb
        light_dir = np.array([0.3, -0.6, 0.8], dtype=np.float32); light_dir /= np.linalg.norm(light_dir)
        
        trans_len = uw if is_vertical else uh; prof_len = uh if is_vertical else uw
        nx = np.linspace(0, 1, prof_len, endpoint=False)
        slope_long, slope_z = np.zeros(prof_len, dtype=np.float32), np.zeros(prof_len, dtype=np.float32)
        
        m1 = nx < 0.10; slope_long[m1], slope_z[m1] = -1.0, 0.0
        m2 = (nx >= 0.10) & (nx < 0.20); slope_long[m2], slope_z[m2] = -0.707, 0.707
        m3 = (nx >= 0.20) & (nx < 0.25); slope_long[m3], slope_z[m3] = 0.0, 1.0
        m4 = (nx >= 0.25) & (nx < 0.75); t = (nx[m4] - 0.25) / 0.5; slope_long[m4] = (t - 0.5) * 2.0 * 0.55; slope_z[m4] = np.sqrt(np.maximum(0, 1.0 - slope_long[m4]**2))
        m5 = (nx >= 0.75) & (nx < 0.80); slope_long[m5], slope_z[m5] = 0.0, 1.0
        m6 = (nx >= 0.80) & (nx < 0.90); slope_long[m6], slope_z[m6] = 0.707, 0.707
        m7 = (nx >= 0.90); slope_long[m7], slope_z[m7] = 1.0, 0.0
        
        ao = np.ones(prof_len, dtype=np.float32); dist = 1.0 - (np.abs(nx - 0.5) / 0.25); ao[m4] = 1.0 - (np.maximum(0, dist[m4]) * 0.4)
        groove_val = np.zeros(prof_len, dtype=np.float32); m_gr = (nx > 0.22) & (nx < 0.78); tg = (nx[m_gr] - 0.22) / 0.56; groove_val[m_gr] = np.sin(tg * np.pi * 14 - np.pi/2) * 0.12
        
        diff = np.maximum(0.25, slope_long * light_dir[1] + slope_z * light_dir[2])
        h_vec = light_dir + np.array([0, 0, 1], dtype=np.float32); h_vec /= np.linalg.norm(h_vec)
        spec = (np.maximum(0, slope_long * h_vec[1] + slope_z * h_vec[2]) ** 2.8) * 0.8
        
        top_split = int(trans_len * 0.85); rgb_final = np.zeros((uh, uw, 3), dtype=np.float32)
        c_diff, c_ao = diff + groove_val, ao * (1.0 + groove_val * 0.66)
        
        for p in range(prof_len):
            p_d, p_a, p_s, p_sz = c_diff[p], c_ao[p], spec[p], slope_z[p]
            row = rgb_final[p, :, :] if is_vertical else rgb_final[:, p, :]
            row[:top_split, 0], row[:top_split, 1], row[:top_split, 2] = base_rgb[0] * p_d * p_a + 255 * p_s, base_rgb[1] * p_d * p_a + 255 * p_s, base_rgb[2] * p_d * p_a + 255 * p_s
            side_d = np.maximum(0.35, 0.8 * light_dir[0] + 0.2 * p_sz * light_dir[2])
            row[top_split:, 0], row[top_split:, 1], row[top_split:, 2] = base_rgb[0] * side_d * (p_a * 0.9), base_rgb[1] * side_d * (p_a * 0.9), base_rgb[2] * side_d * (p_a * 0.9)
            
        cp, line_w = prof_len // 2, max(2, 3 * upscale)
        is_line = (np.arange(prof_len) >= (cp - line_w//2)) & (np.arange(prof_len) <= (cp + line_w//2))
        if is_vertical: rgb_final[is_line, :, :] = np.minimum(255, 255 * (c_diff[is_line][:, np.newaxis, np.newaxis] * 0.8 + 0.4))
        else: rgb_final[:, is_line, :] = np.minimum(255, 255 * (c_diff[is_line][np.newaxis, :, np.newaxis] * 0.8 + 0.4))
        
        surface = Image.fromarray(np.clip(rgb_final, 0, 255).astype(np.uint8), 'RGB').convert("RGBA")
        mask = Image.new("L", (uw, uh), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, uw, uh), radius=3*upscale, fill=255)
        final_body = Image.new("RGBA", (uw, uh), (0,0,0,0)); final_body.paste(surface, (0,0), mask)
        final_body = final_body.resize((int(w), int(h)), Image.Resampling.LANCZOS)
        
        pad = 8; canvas_img = Image.new("RGBA", (int(w) + pad*2, int(h) + pad*2), (0,0,0,0))
        ImageDraw.Draw(canvas_img).rounded_rectangle((pad+2, pad+4, pad+int(w)+2, pad+int(h)+4), radius=4, fill=(0,0,0,140))
        canvas_img.paste(final_body, (pad, pad), final_body)
        photo = ImageTk.PhotoImage(canvas_img.filter(ImageFilter.GaussianBlur(radius=4)) if False else canvas_img)
        
        _DUAL_FADER_ASSET_CACHE[cache_key] = photo; return photo
