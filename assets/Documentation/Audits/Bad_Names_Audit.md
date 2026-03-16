# Clean Code Audit: Bad Naming Report

## Executive Summary
Analyzed codebase for magic numbers, short variables, noise words, and poor function names.
- **Files with Issues**: 443
- **Total Violations**: 3703

## Top Offenders

### workers/builder/fader_dual/core/dual_fader_asset_generator.py
#### Short Variable Name
- Line 14: Variable 'uw' is too short for its scope.
  `upscale = 2; uw, uh = max(1, int(w * upscale)), max(1, int(h * upscale))`
- Line 14: Variable 'uh' is too short for its scope.
  `upscale = 2; uw, uh = max(1, int(w * upscale)), max(1, int(h * upscale))`
- Line 18: Variable 'c' is too short for its scope.
  `if len(hex_str) == 3: hex_str = "".join([c*2 for c in hex_str])`
- Line 19: Variable 'i' is too short for its scope.
  `return np.array([int(hex_str[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)`
- Line 28: Variable 'nx' is too short for its scope.
  `nx = np.linspace(0, 1, prof_len, endpoint=False)`
- Line 31: Variable 'm1' is too short for its scope.
  `m1 = nx < 0.10; slope_long[m1], slope_z[m1] = -1.0, 0.0`
- Line 32: Variable 'm2' is too short for its scope.
  `m2 = (nx >= 0.10) & (nx < 0.20); slope_long[m2], slope_z[m2] = -0.707, 0.707`
- Line 33: Variable 'm3' is too short for its scope.
  `m3 = (nx >= 0.20) & (nx < 0.25); slope_long[m3], slope_z[m3] = 0.0, 1.0`
- Line 34: Variable 'm4' is too short for its scope.
  `m4 = (nx >= 0.25) & (nx < 0.75); t = (nx[m4] - 0.25) / 0.5; slope_long[m4] = (t - 0.5) * 2.0 * 0.55; slope_z[m4] = np.sqrt(np.maximum(0, 1.0 - slope_long[m4]**2))`
- Line 34: Variable 't' is too short for its scope.
  `m4 = (nx >= 0.25) & (nx < 0.75); t = (nx[m4] - 0.25) / 0.5; slope_long[m4] = (t - 0.5) * 2.0 * 0.55; slope_z[m4] = np.sqrt(np.maximum(0, 1.0 - slope_long[m4]**2))`
- ... and 6 more.
#### Function Naming
- Line 16: Function 'hex_to_rgb' may not be a verb phrase.
  `def hex_to_rgb(hex_str):`
#### Magic Number
- Line 18: Literal '3' should be a named constant.
  `if len(hex_str) == 3: hex_str = "".join([c*2 for c in hex_str])`
- Line 19: Literal '4' should be a named constant.
  `return np.array([int(hex_str[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)`
- Line 22: Literal '120' should be a named constant.
  `except: b_rgb = np.array([120, 120, 120], dtype=np.float32)`
- Line 22: Literal '120' should be a named constant.
  `except: b_rgb = np.array([120, 120, 120], dtype=np.float32)`
- Line 22: Literal '120' should be a named constant.
  `except: b_rgb = np.array([120, 120, 120], dtype=np.float32)`
- Line 24: Literal '0.7' should be a named constant.
  `base_rgb = 0.7 * np.array([30, 30, 30], dtype=np.float32) + 0.3 * b_rgb`
- Line 24: Literal '30' should be a named constant.
  `base_rgb = 0.7 * np.array([30, 30, 30], dtype=np.float32) + 0.3 * b_rgb`
- Line 24: Literal '30' should be a named constant.
  `base_rgb = 0.7 * np.array([30, 30, 30], dtype=np.float32) + 0.3 * b_rgb`
- Line 24: Literal '30' should be a named constant.
  `base_rgb = 0.7 * np.array([30, 30, 30], dtype=np.float32) + 0.3 * b_rgb`
- Line 24: Literal '0.3' should be a named constant.
  `base_rgb = 0.7 * np.array([30, 30, 30], dtype=np.float32) + 0.3 * b_rgb`
- ... and 50 more.
#### Encoding/Prefix
- Line 40: Variable 'm_gr' uses legacy prefix.
  `groove_val = np.zeros(prof_len, dtype=np.float32); m_gr = (nx > 0.22) & (nx < 0.78); tg = (nx[m_gr] - 0.22) / 0.56; groove_val[m_gr] = np.sin(tg * np.pi * 14 - np.pi/2) * 0.12`

---
### workers/builder/fader_bar_graph/core/fader_bar_asset_generator.py
#### Short Variable Name
- Line 18: Variable 'uw' is too short for its scope.
  `upscale = 2; uw, uh = w * upscale, h * upscale`
- Line 18: Variable 'uh' is too short for its scope.
  `upscale = 2; uw, uh = w * upscale, h * upscale`
- Line 21: Variable 's' is too short for its scope.
  `s = s.lstrip('#')`
- Line 22: Variable 'i' is too short for its scope.
  `return np.array([int(s[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)`
- Line 30: Variable 'ny' is too short for its scope.
  `ny = np.linspace(0, 1, uh, dtype=np.float32)`
- Line 34: Variable 'm1' is too short for its scope.
  `m1 = ny < 0.10; slope_y[m1], slope_z[m1] = -1.0, 0.0`
- Line 35: Variable 'm2' is too short for its scope.
  `m2 = (ny >= 0.10) & (ny < 0.20); slope_y[m2], slope_z[m2] = -0.707, 0.707`
- Line 36: Variable 'm3' is too short for its scope.
  `m3 = (ny >= 0.20) & (ny < 0.25); slope_y[m3], slope_z[m3] = 0.0, 1.0`
- Line 37: Variable 'm4' is too short for its scope.
  `m4 = (ny >= 0.25) & (ny < 0.75); t = (ny[m4]-0.25)/0.5; sy = (t-0.5)*2.0*0.55; slope_y[m4] = sy; slope_z[m4] = np.sqrt(np.maximum(0, 1.0-sy**2))`
- Line 37: Variable 't' is too short for its scope.
  `m4 = (ny >= 0.25) & (ny < 0.75); t = (ny[m4]-0.25)/0.5; sy = (t-0.5)*2.0*0.55; slope_y[m4] = sy; slope_z[m4] = np.sqrt(np.maximum(0, 1.0-sy**2))`
- ... and 8 more.
#### Function Naming
- Line 20: Function 'hex_to_rgb' may not be a verb phrase.
  `def hex_to_rgb(s):`
#### Magic Number
- Line 22: Literal '4' should be a named constant.
  `return np.array([int(s[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)`
- Line 25: Literal '40' should be a named constant.
  `except: b_rgb = np.array([40, 40, 40], dtype=np.float32)`
- Line 25: Literal '40' should be a named constant.
  `except: b_rgb = np.array([40, 40, 40], dtype=np.float32)`
- Line 25: Literal '40' should be a named constant.
  `except: b_rgb = np.array([40, 40, 40], dtype=np.float32)`
- Line 27: Literal '0.7' should be a named constant.
  `base_rgb = 0.7 * np.array([30, 30, 30], dtype=np.float32) + 0.3 * b_rgb`
- Line 27: Literal '30' should be a named constant.
  `base_rgb = 0.7 * np.array([30, 30, 30], dtype=np.float32) + 0.3 * b_rgb`
- Line 27: Literal '30' should be a named constant.
  `base_rgb = 0.7 * np.array([30, 30, 30], dtype=np.float32) + 0.3 * b_rgb`
- Line 27: Literal '30' should be a named constant.
  `base_rgb = 0.7 * np.array([30, 30, 30], dtype=np.float32) + 0.3 * b_rgb`
- Line 27: Literal '0.3' should be a named constant.
  `base_rgb = 0.7 * np.array([30, 30, 30], dtype=np.float32) + 0.3 * b_rgb`
- Line 28: Literal '0.3' should be a named constant.
  `light_dir = np.array([0.3, -0.6, 0.8], dtype=np.float32); light_dir /= np.linalg.norm(light_dir)`
- ... and 46 more.

---
### workers/builder/button_wink/core/wink_renderer.py
#### Function Naming
- Line 14: Function 'draw_circular_mask' may not be a verb phrase.
  `def draw_circular_mask(canvas, width, height):`
- Line 62: Function 'draw_rounded_mask' may not be a verb phrase.
  `def draw_rounded_mask(canvas, width, height, radius):`
- Line 102: Function 'draw_glass_lens' may not be a verb phrase.
  `def draw_glass_lens(canvas, width, height, shape_type, radius, border_color, border_thickness, state):`
- Line 152: Function 'draw_wink_visuals' may not be a verb phrase.
  `def draw_wink_visuals(canvas, state, config, label_text=None):`
#### Magic Number
- Line 32: Literal '4' should be a named constant.
  `upscale = 4`
- Line 39: Literal '255' should be a named constant.
  `mask = Image.new("L", (uw, uh), 255)`
- Line 79: Literal '4' should be a named constant.
  `upscale = 4`
- Line 86: Literal '255' should be a named constant.
  `mask = Image.new("L", (uw, uh), 255)`
- Line 121: Literal '6' should be a named constant.
  `rim_width = (border_thickness + 6) / 2 * upscale`
- Line 125: Literal '255' should be a named constant.
  `m_draw.ellipse((ox, oy, ox+size, oy+size), fill=255)`
- Line 127: Literal '255' should be a named constant.
  `draw.arc((ox+1, oy+1, ox+size-1, oy+size-1), start=180, end=300, fill=(255, 255, 255, 90), width=int(upscale))`
- Line 127: Literal '255' should be a named constant.
  `draw.arc((ox+1, oy+1, ox+size-1, oy+size-1), start=180, end=300, fill=(255, 255, 255, 90), width=int(upscale))`
- Line 127: Literal '255' should be a named constant.
  `draw.arc((ox+1, oy+1, ox+size-1, oy+size-1), start=180, end=300, fill=(255, 255, 255, 90), width=int(upscale))`
- Line 129: Literal '255' should be a named constant.
  `m_draw.rounded_rectangle((0, 0, uw, uh), radius=ur, fill=255)`
- ... and 21 more.
#### Short Variable Name
- Line 33: Variable 'uw' is too short for its scope.
  `uw, uh = int(width * upscale), int(height * upscale)`
- Line 33: Variable 'uh' is too short for its scope.
  `uw, uh = int(width * upscale), int(height * upscale)`
- Line 42: Variable 'ox' is too short for its scope.
  `ox, oy = (uw-size)/2, (uh-size)/2`
- Line 42: Variable 'oy' is too short for its scope.
  `ox, oy = (uw-size)/2, (uh-size)/2`
- Line 80: Variable 'uw' is too short for its scope.
  `uw, uh, ur = int(width * upscale), int(height * upscale), int(radius * upscale)`
- Line 80: Variable 'uh' is too short for its scope.
  `uw, uh, ur = int(width * upscale), int(height * upscale), int(radius * upscale)`
- Line 80: Variable 'ur' is too short for its scope.
  `uw, uh, ur = int(width * upscale), int(height * upscale), int(radius * upscale)`
- Line 113: Variable 'uw' is too short for its scope.
  `uw, uh = int(width * upscale), int(height * upscale)`
- Line 113: Variable 'uh' is too short for its scope.
  `uw, uh = int(width * upscale), int(height * upscale)`
- Line 114: Variable 'ur' is too short for its scope.
  `ur = radius * upscale`
- ... and 20 more.
#### Encoding/Prefix
- Line 40: Variable 'm_draw' uses legacy prefix.
  `m_draw = ImageDraw.Draw(mask)`
- Line 87: Variable 'm_draw' uses legacy prefix.
  `m_draw = ImageDraw.Draw(mask)`
- Line 119: Variable 'm_draw' uses legacy prefix.
  `m_draw = ImageDraw.Draw(mask)`
- Line 179: Variable 'f_size' uses legacy prefix.
  `f_size = config["font_size"] or int(min(width, height) * 0.25)`

---
### workers/builder/meter_needle/cosmetics/lighting_overlay.py
#### Function Naming
- Line 27: Function 'generate_overlay' may not be a verb phrase.
  `def generate_overlay(width, height, bezel_shape, bezel_width, pivot_x, pivot_y, lighting_config={}):`
- Line 223: Function 'photo_image' may not be a verb phrase.
  `def photo_image(width, height, bezel_shape, bezel_width, pivot_x, pivot_y, lighting_config={}):`
#### Short Variable Name
- Line 30: Variable 'w' is too short for its scope.
  `w, h = width * scale, height * scale`
- Line 30: Variable 'h' is too short for its scope.
  `w, h = width * scale, height * scale`
- Line 71: Variable 'c' is too short for its scope.
  `c = str(glow_color_hex).lstrip('#')`
- Line 72: Variable 'i' is too short for its scope.
  `rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))`
- Line 86: Variable 'r' is too short for its scope.
  `r, g, b, a = glow_layer.split()`
- Line 86: Variable 'g' is too short for its scope.
  `r, g, b, a = glow_layer.split()`
- Line 86: Variable 'b' is too short for its scope.
  `r, g, b, a = glow_layer.split()`
- Line 86: Variable 'a' is too short for its scope.
  `r, g, b, a = glow_layer.split()`
- Line 87: Variable 'a' is too short for its scope.
  `a = a.point(lambda p: p * (glow_intensity * 0.8))`
#### Magic Number
- Line 36: Literal '0.25' should be a named constant.
  `glow_intensity = float(lighting_config.get("intensity", 0.25))`
- Line 39: Literal '0.25' should be a named constant.
  `size_y_mult = float(lighting_config.get("size_y", 0.25))`
- Line 53: Literal '255' should be a named constant.
  `draw_mask.polygon(points_inner, fill=255)`
- Line 60: Literal '4' should be a named constant.
  `vignette = vignette.filter(ImageFilter.GaussianBlur(radius=4*scale))`
- Line 68: Literal '255' should be a named constant.
  `rgb = (255, 180, 80) # Default`
- Line 68: Literal '180' should be a named constant.
  `rgb = (255, 180, 80) # Default`
- Line 68: Literal '80' should be a named constant.
  `rgb = (255, 180, 80) # Default`
- Line 72: Literal '16' should be a named constant.
  `rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))`
- Line 72: Literal '4' should be a named constant.
  `rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))`
- Line 82: Literal '180' should be a named constant.
  `start=180, end=0, fill=rgb + (255,)`
- ... and 46 more.

---
### workers/builder/fader_horizontal/core/horizontal_fader_renderer_mixin.py
#### Function Naming
- Line 9: Function 'render' may not be a verb phrase.
  `def render(self):`
#### Short Variable Name
- Line 11: Variable 'w' is too short for its scope.
  `w, h = float(self.canvas.winfo_width()), float(self.canvas.winfo_height())`
- Line 11: Variable 'h' is too short for its scope.
  `w, h = float(self.canvas.winfo_width()), float(self.canvas.winfo_height())`
- Line 12: Variable 'w' is too short for its scope.
  `if w <= 1: w, h = self.width, self.height`
- Line 12: Variable 'h' is too short for its scope.
  `if w <= 1: w, h = self.width, self.height`
- Line 20: Variable 'cy' is too short for its scope.
  `cy, accent = h/2.0, THEMES.get(DEFAULT_THEME, THEMES["dark"]).get("accent", "#f4902c")`
- Line 24: Variable 'fs' is too short for its scope.
  `fs = int(float(self.config_data.get("layout", {}).get("font", 9)))`
- Line 29: Variable 'px' is too short for its scope.
  `px = cap_w/2.0 + 10.0`
- Line 44: Variable 'vr' is too short for its scope.
  `vr = self.max_val - self.min_val`
- Line 45: Variable 'ti' is too short for its scope.
  `ti = self.config_data.get("tick_interval")`
- Line 48: Variable 'e' is too short for its scope.
  `e = math.floor(math.log10(vr/10.0)); f = (vr/10.0)/(10**e)`
- ... and 15 more.
#### Magic Number
- Line 24: Literal '9' should be a named constant.
  `fs = int(float(self.config_data.get("layout", {}).get("font", 9)))`
- Line 28: Literal '50' should be a named constant.
  `cap_w, cap_h = int(float(self.config_data.get("cap_width", 50))*scale), int(float(self.config_data.get("cap_height", 55))*scale)`
- Line 29: Literal '10.0' should be a named constant.
  `px = cap_w/2.0 + 10.0`
- Line 31: Literal '5' should be a named constant.
  `self.canvas.create_rectangle(px-5, cy-4, w-px+5, cy+4, fill="#050505", outline="#222", width=1, tags=("static", "track_slot"))`
- Line 31: Literal '5' should be a named constant.
  `self.canvas.create_rectangle(px-5, cy-4, w-px+5, cy+4, fill="#050505", outline="#222", width=1, tags=("static", "track_slot"))`
- Line 48: Literal '10.0' should be a named constant.
  `e = math.floor(math.log10(vr/10.0)); f = (vr/10.0)/(10**e)`
- Line 48: Literal '10.0' should be a named constant.
  `e = math.floor(math.log10(vr/10.0)); f = (vr/10.0)/(10**e)`
- Line 48: Literal '10' should be a named constant.
  `e = math.floor(math.log10(vr/10.0)); f = (vr/10.0)/(10**e)`
- Line 49: Literal '1.5' should be a named constant.
  `s = 1 if f < 1.5 else (2 if f < 3.5 else (5 if f < 7.5 else 10))`
- Line 49: Literal '3.5' should be a named constant.
  `s = 1 if f < 1.5 else (2 if f < 3.5 else (5 if f < 7.5 else 10))`
- ... and 30 more.

---
### workers/builder/knob/core/knob_renderer.py
#### Function Naming
- Line 5: Function 'draw_knob_visuals' may not be a verb phrase.
  `def draw_knob_visuals(canvas, state, config, value, label_text=None):`
#### Short Variable Name
- Line 20: Variable 'cx' is too short for its scope.
  `cx, cy = width / 2, height / 2`
- Line 20: Variable 'cy' is too short for its scope.
  `cx, cy = width / 2, height / 2`
- Line 117: Variable 'fg' is too short for its scope.
  `fg = config["fg_color"]`
- Line 126: Variable 'lx' is too short for its scope.
  `lx, ly, l_anchor = cx, adj_cy - visual_radius - text_padding, "s"`
- Line 126: Variable 'ly' is too short for its scope.
  `lx, ly, l_anchor = cx, adj_cy - visual_radius - text_padding, "s"`
- Line 127: Variable 'ly' is too short for its scope.
  `if config["text_pos"] == "bottom": ly, l_anchor = adj_cy + visual_radius + text_padding, "n"`
- Line 128: Variable 'lx' is too short for its scope.
  `elif config["text_pos"] == "left": lx, ly, l_anchor = cx - visual_radius - text_padding, adj_cy, "e"`
- Line 128: Variable 'ly' is too short for its scope.
  `elif config["text_pos"] == "left": lx, ly, l_anchor = cx - visual_radius - text_padding, adj_cy, "e"`
- Line 129: Variable 'lx' is too short for its scope.
  `elif config["text_pos"] == "right": lx, ly, l_anchor = cx + visual_radius + text_padding, adj_cy, "w"`
- Line 129: Variable 'ly' is too short for its scope.
  `elif config["text_pos"] == "right": lx, ly, l_anchor = cx + visual_radius + text_padding, adj_cy, "w"`
- ... and 13 more.
#### Magic Number
- Line 33: Literal '9' should be a named constant.
  `label_font_size = 9`
- Line 34: Literal '12' should be a named constant.
  `label_padding = 12`
- Line 42: Literal '4' should be a named constant.
  `padding += tick_length + 4`
- Line 52: Literal '0.8' should be a named constant.
  `radius = (min(usable_w, usable_h) / 2) * 0.8  # ⚡ 20% reduction for better framing`
- Line 53: Literal '8' should be a named constant.
  `if radius < 8: radius = 8 # Increased absolute minimum floor for safety`
- Line 53: Literal '8' should be a named constant.
  `if radius < 8: radius = 8 # Increased absolute minimum floor for safety`
- Line 62: Literal '240' should be a named constant.
  `start_angle = 240`
- Line 63: Literal '300' should be a named constant.
  `extent = -300`
- Line 70: Literal '135' should be a named constant.
  `panner_max_arc = 135`
- Line 71: Literal '90' should be a named constant.
  `start_angle = 90`
- ... and 32 more.

---
### workers/builder/fader_ganged_controlled_array/core/gca_renderer_mixin.py
#### Magic Number
- Line 10: Literal '40' should be a named constant.
  `draw_h = self.height - 40`
- Line 34: Literal '5' should be a named constant.
  `self.canvas.create_text(offset_x + 5, y - 5, text=tick_text, fill=self.tick_color, anchor="w", font=("Arial", 8))`
- Line 34: Literal '5' should be a named constant.
  `self.canvas.create_text(offset_x + 5, y - 5, text=tick_text, fill=self.tick_color, anchor="w", font=("Arial", 8))`
- Line 34: Literal '8' should be a named constant.
  `self.canvas.create_text(offset_x + 5, y - 5, text=tick_text, fill=self.tick_color, anchor="w", font=("Arial", 8))`
- Line 35: Literal '5' should be a named constant.
  `self.canvas.create_text(offset_x + width - 5, y - 5, text=tick_text, fill=self.tick_color, anchor="e", font=("Arial", 8))`
- Line 35: Literal '5' should be a named constant.
  `self.canvas.create_text(offset_x + width - 5, y - 5, text=tick_text, fill=self.tick_color, anchor="e", font=("Arial", 8))`
- Line 35: Literal '8' should be a named constant.
  `self.canvas.create_text(offset_x + width - 5, y - 5, text=tick_text, fill=self.tick_color, anchor="e", font=("Arial", 8))`
- Line 38: Literal '10' should be a named constant.
  `cap_w = width - 10`
- Line 39: Literal '8' should be a named constant.
  `sx1 = offset_x + width/2 - cap_w/2 + 8`
- Line 40: Literal '8' should be a named constant.
  `sx2 = offset_x + width/2 + cap_w/2 - 8`
- ... and 42 more.
#### Short Variable Name
- Line 18: Variable 'ti' is too short for its scope.
  `ti = float(self.tick_interval) if self.tick_interval else self._calculate_smart_interval(val_range)`
- Line 91: Variable 'h' is too short for its scope.
  `h = self.height`
- Line 146: Variable 'r' is too short for its scope.
  `if norm_val < 0.5: r, g, b = int(255 * (norm_val * 2)), 255, 0`
- Line 146: Variable 'g' is too short for its scope.
  `if norm_val < 0.5: r, g, b = int(255 * (norm_val * 2)), 255, 0`
- Line 146: Variable 'b' is too short for its scope.
  `if norm_val < 0.5: r, g, b = int(255 * (norm_val * 2)), 255, 0`
- Line 147: Variable 'r' is too short for its scope.
  `else: r, g, b = 255, int(255 * (1.0 - (norm_val - 0.5) * 2)), 0`
- Line 147: Variable 'g' is too short for its scope.
  `else: r, g, b = 255, int(255 * (1.0 - (norm_val - 0.5) * 2)), 0`
- Line 147: Variable 'b' is too short for its scope.
  `else: r, g, b = 255, int(255 * (1.0 - (norm_val - 0.5) * 2)), 0`
- Line 153: Variable 'r' is too short for its scope.
  `r, g, b = int(norm(self.child_values[0])*255), int(norm(self.child_values[1])*255), int(norm(self.child_values[2])*255)`
- Line 153: Variable 'g' is too short for its scope.
  `r, g, b = int(norm(self.child_values[0])*255), int(norm(self.child_values[1])*255), int(norm(self.child_values[2])*255)`
- ... and 1 more.
#### Encoding/Prefix
- Line 98: Variable 'm_val' uses legacy prefix.
  `m_val = self._safe_get(self.master_value)`

---
### workers/builder/knob/core/knob_renderer_mixin.py
#### Short Variable Name
- Line 25: Variable 'cx' is too short for its scope.
  `cx, cy = width / 2, height / 2`
- Line 25: Variable 'cy' is too short for its scope.
  `cx, cy = width / 2, height / 2`
- Line 93: Variable 'fg' is too short for its scope.
  `fg = cfg["fg_color"]`
- Line 98: Variable 'lx' is too short for its scope.
  `lx, ly, l_anchor = cx, adj_cy - visual_radius - text_padding, "s"`
- Line 98: Variable 'ly' is too short for its scope.
  `lx, ly, l_anchor = cx, adj_cy - visual_radius - text_padding, "s"`
- Line 99: Variable 'ly' is too short for its scope.
  `if cfg["text_pos"] == "bottom": ly, l_anchor = adj_cy + visual_radius + text_padding, "n"`
- Line 100: Variable 'lx' is too short for its scope.
  `elif cfg["text_pos"] == "left": lx, ly, l_anchor = cx - visual_radius - text_padding, adj_cy, "e"`
- Line 100: Variable 'ly' is too short for its scope.
  `elif cfg["text_pos"] == "left": lx, ly, l_anchor = cx - visual_radius - text_padding, adj_cy, "e"`
- Line 101: Variable 'lx' is too short for its scope.
  `elif cfg["text_pos"] == "right": lx, ly, l_anchor = cx + visual_radius + text_padding, adj_cy, "w"`
- Line 101: Variable 'ly' is too short for its scope.
  `elif cfg["text_pos"] == "right": lx, ly, l_anchor = cx + visual_radius + text_padding, adj_cy, "w"`
- ... and 13 more.
#### Magic Number
- Line 39: Literal '12' should be a named constant.
  `label_padding = 12`
- Line 43: Literal '12' should be a named constant.
  `padding = (arc_width / 2) + 12 # Safety margin`
- Line 44: Literal '4' should be a named constant.
  `if show_ticks: padding += tick_length + 4`
- Line 47: Literal '0.8' should be a named constant.
  `radius = (min(usable_w, usable_h) / 2) * 0.8`
- Line 48: Literal '8' should be a named constant.
  `if radius < 8: radius = 8`
- Line 48: Literal '8' should be a named constant.
  `if radius < 8: radius = 8`
- Line 56: Literal '240' should be a named constant.
  `start_angle, extent = 240, -300`
- Line 56: Literal '300' should be a named constant.
  `start_angle, extent = 240, -300`
- Line 63: Literal '90' should be a named constant.
  `panner_max_arc, start_angle = 135, 90`
- Line 65: Literal '90' should be a named constant.
  `pointer_angle_deg = 90 + (-1 * norm_from_center * panner_max_arc)`
- ... and 29 more.

---
### managers/Display/factory/button_canvas_base.py
#### Magic Number
- Line 12: Literal '6' should be a named constant.
  `corner_radius=6,`
- Line 116: Literal '4' should be a named constant.
  `pad = 4`
- Line 117: Literal '12' should be a named constant.
  `if width < 12 or height < 12: return ImageTk.PhotoImage(image)`
- Line 117: Literal '12' should be a named constant.
  `if width < 12 or height < 12: return ImageTk.PhotoImage(image)`
- Line 131: Literal '6' should be a named constant.
  `if height > pad*2 + 6:`
- Line 145: Literal '255' should be a named constant.
  `except: r_c, g_c, b_c = 255, 150, 0`
- Line 147: Literal '15' should be a named constant.
  `for i in range(15):`
- Line 148: Literal '255' should be a named constant.
  `alpha = int(255 * (0.1 + 0.9 * ((i/15)**2)) * self.glow_intensity)`
- Line 148: Literal '0.1' should be a named constant.
  `alpha = int(255 * (0.1 + 0.9 * ((i/15)**2)) * self.glow_intensity)`
- Line 148: Literal '0.9' should be a named constant.
  `alpha = int(255 * (0.1 + 0.9 * ((i/15)**2)) * self.glow_intensity)`
- ... and 31 more.
#### Short Variable Name
- Line 119: Variable 'r' is too short for its scope.
  `r = min(self.corner_radius, (width - pad*2)//2, (height - pad*2)//2)`
- Line 170: Variable 'tx' is too short for its scope.
  `tx, ty = width / 2, height / 2`
- Line 170: Variable 'ty' is too short for its scope.
  `tx, ty = width / 2, height / 2`
- Line 171: Variable 'ty' is too short for its scope.
  `if is_hovered: ty += 1`
- Line 181: Variable 'r' is too short for its scope.
  `r = (min(width, height) - pad*2) // 2`
- Line 182: Variable 'cx' is too short for its scope.
  `cx, cy = width//2, height//2`
- Line 182: Variable 'cy' is too short for its scope.
  `cx, cy = width//2, height//2`
- Line 223: Variable 'tx' is too short for its scope.
  `tx, ty = width / 2, height / 2`
- Line 223: Variable 'ty' is too short for its scope.
  `tx, ty = width / 2, height / 2`
- Line 224: Variable 'ty' is too short for its scope.
  `if is_hovered: ty += 1`
- ... and 2 more.
#### Encoding/Prefix
- Line 164: Variable 'f_size' uses legacy prefix.
  `f_size = self.active_font_size if is_active else self.inactive_font_size`
- Line 165: Variable 'f_size' uses legacy prefix.
  `if not f_size: f_size = int(self.font_info[1]) if len(self.font_info)>1 else 12`

---
### workers/builder/fader_horizontal/core/horizontal_fader_asset_generator.py
#### Short Variable Name
- Line 18: Variable 'uw' is too short for its scope.
  `upscale = 2; uw, uh = int(w*upscale), int(h*upscale)`
- Line 18: Variable 'uh' is too short for its scope.
  `upscale = 2; uw, uh = int(w*upscale), int(h*upscale)`
- Line 19: Variable 'uw' is too short for its scope.
  `if uw < 1: uw = 1`
- Line 20: Variable 'uh' is too short for its scope.
  `if uh < 1: uh = 1`
- Line 23: Variable 'hs' is too short for its scope.
  `hs = hs.lstrip('#')`
- Line 24: Variable 'hs' is too short for its scope.
  `if len(hs) == 3: hs = "".join([c*2 for c in hs])`
- Line 24: Variable 'c' is too short for its scope.
  `if len(hs) == 3: hs = "".join([c*2 for c in hs])`
- Line 25: Variable 'i' is too short for its scope.
  `return np.array([int(hs[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)`
- Line 30: Variable 'xc' is too short for its scope.
  `xc = np.linspace(0, 1, uw, dtype=np.float32).reshape(1, uw)`
- Line 31: Variable 'sx' is too short for its scope.
  `sx, sz = np.zeros((1, uw), dtype=np.float32), np.ones((1, uw), dtype=np.float32)`
- ... and 8 more.
#### Function Naming
- Line 22: Function 'htr' may not be a verb phrase.
  `def htr(hs):`
#### Magic Number
- Line 24: Literal '3' should be a named constant.
  `if len(hs) == 3: hs = "".join([c*2 for c in hs])`
- Line 28: Literal '120' should be a named constant.
  `except: b_rgb = np.array([120, 120, 120], dtype=np.float32)`
- Line 28: Literal '120' should be a named constant.
  `except: b_rgb = np.array([120, 120, 120], dtype=np.float32)`
- Line 28: Literal '120' should be a named constant.
  `except: b_rgb = np.array([120, 120, 120], dtype=np.float32)`
- Line 33: Literal '0.1' should be a named constant.
  `sx[xc < 0.10], sz[xc < 0.10] = -1.0, 0.0`
- Line 33: Literal '0.1' should be a named constant.
  `sx[xc < 0.10], sz[xc < 0.10] = -1.0, 0.0`
- Line 34: Literal '0.1' should be a named constant.
  `m02 = (xc >= 0.10) & (xc < 0.20); sx[m02], sz[m02] = -0.707, 0.707`
- Line 34: Literal '0.2' should be a named constant.
  `m02 = (xc >= 0.10) & (xc < 0.20); sx[m02], sz[m02] = -0.707, 0.707`
- Line 35: Literal '0.25' should be a named constant.
  `mc = (xc >= 0.25) & (xc < 0.75); t = (xc[mc]-0.25)/0.5; val = (t-0.5)*2.0*0.55; sx[mc] = val; sz[mc] = np.sqrt(np.maximum(0, 1.0-val**2))`
- Line 35: Literal '0.75' should be a named constant.
  `mc = (xc >= 0.25) & (xc < 0.75); t = (xc[mc]-0.25)/0.5; val = (t-0.5)*2.0*0.55; sx[mc] = val; sz[mc] = np.sqrt(np.maximum(0, 1.0-val**2))`
- ... and 21 more.
#### Encoding/Prefix
- Line 50: Variable 'm_draw' uses legacy prefix.
  `mask = Image.new("L", (uw, uh), 0); m_draw = ImageDraw.Draw(mask); m_draw.rounded_rectangle((0,0,uw,uh), radius=3*upscale, fill=255)`

---
### workers/builder/fader/core/cap.py
#### Short Variable Name
- Line 22: Variable 'uw' is too short for its scope.
  `uw, uh = w * upscale, h * upscale`
- Line 22: Variable 'uh' is too short for its scope.
  `uw, uh = w * upscale, h * upscale`
- Line 26: Variable 'i' is too short for its scope.
  `return np.array([int(hex_str[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)`
- Line 47: Variable 't' is too short for its scope.
  `t = (y_coords[mask_concave] - 0.25) / 0.5`
- Line 72: Variable 'ao' is too short for its scope.
  `ao = np.ones((uh, 1), dtype=np.float32)`
- Line 92: Variable 'cy' is too short for its scope.
  `cy = uh // 2`
#### Function Naming
- Line 24: Function 'hex_to_rgb' may not be a verb phrase.
  `def hex_to_rgb(hex_str):`
#### Magic Number
- Line 29: Literal '40' should be a named constant.
  `except: b_rgb = np.array([40, 40, 40], dtype=np.float32)`
- Line 29: Literal '40' should be a named constant.
  `except: b_rgb = np.array([40, 40, 40], dtype=np.float32)`
- Line 29: Literal '40' should be a named constant.
  `except: b_rgb = np.array([40, 40, 40], dtype=np.float32)`
- Line 39: Literal '0.1' should be a named constant.
  `slope_y[y_coords < 0.10] = -1.0`
- Line 40: Literal '0.1' should be a named constant.
  `slope_z[y_coords < 0.10] = 0.0`
- Line 42: Literal '0.1' should be a named constant.
  `mask_02 = (y_coords >= 0.10) & (y_coords < 0.20)`
- Line 42: Literal '0.2' should be a named constant.
  `mask_02 = (y_coords >= 0.10) & (y_coords < 0.20)`
- Line 46: Literal '0.25' should be a named constant.
  `mask_concave = (y_coords >= 0.25) & (y_coords < 0.75)`
- Line 46: Literal '0.75' should be a named constant.
  `mask_concave = (y_coords >= 0.25) & (y_coords < 0.75)`
- Line 47: Literal '0.25' should be a named constant.
  `t = (y_coords[mask_concave] - 0.25) / 0.5`
- ... and 25 more.
#### Noise Word
- Line 89: Variable 'pixel_data' contains redundant word 'Data'.
  `pixel_data = np.tile(colors, (1, uw, 1))`
#### Encoding/Prefix
- Line 104: Variable 'm_draw' uses legacy prefix.
  `m_draw = ImageDraw.Draw(mask)`
- Line 118: Variable 's_draw' uses legacy prefix.
  `s_draw = ImageDraw.Draw(shadow_layer)`

---
### workers/builder/circular_motion_displacement_potentiometer/cmdp_channel_handler.py
#### Magic Number
- Line 19: Literal '100.0' should be a named constant.
  `self.visible, self.val_min, self.val_max, self.rot_min, self.rot_max = True, 0.0, 100.0, 0.0, 100.0`
- Line 19: Literal '100.0' should be a named constant.
  `self.visible, self.val_min, self.val_max, self.rot_min, self.rot_max = True, 0.0, 100.0, 0.0, 100.0`
- Line 82: Literal '60' should be a named constant.
  `hb_w = 60`
- Line 83: Literal '20' should be a named constant.
  `hbp = [self.rotate_point(cx - hb_w/2, cy - tl/2 - 20, cx, cy, cos_t, sin_t),`
- Line 84: Literal '20' should be a named constant.
  `self.rotate_point(cx + hb_w/2, cy - tl/2 - 20, cx, cy, cos_t, sin_t),`
- Line 85: Literal '20' should be a named constant.
  `self.rotate_point(cx + hb_w/2, cy + tl/2 + 20, cx, cy, cos_t, sin_t),`
- Line 86: Literal '20' should be a named constant.
  `self.rotate_point(cx - hb_w/2, cy + tl/2 + 20, cx, cy, cos_t, sin_t)]`
- Line 99: Literal '10.0' should be a named constant.
  `ly = (-tl/2) + ((i/10.0) * tl)`
- Line 100: Literal '15' should be a named constant.
  `tp1 = self.rotate_point(cx - 15, cy + ly, cx, cy, cos_t, sin_t)`
- Line 101: Literal '25' should be a named constant.
  `tp2 = self.rotate_point(cx - 25, cy + ly, cx, cy, cos_t, sin_t)`
- ... and 8 more.
#### Short Variable Name
- Line 44: Variable 'cx' is too short for its scope.
  `cx, cy = self.widget_ref.center_x, self.widget_ref.center_y`
- Line 44: Variable 'cy' is too short for its scope.
  `cx, cy = self.widget_ref.center_x, self.widget_ref.center_y`
- Line 61: Variable 'dx' is too short for its scope.
  `dx, dy = px - cx, py - cy`
- Line 61: Variable 'dy' is too short for its scope.
  `dx, dy = px - cx, py - cy`
- Line 72: Variable 'cx' is too short for its scope.
  `cx, cy = self.x, self.y`
- Line 72: Variable 'cy' is too short for its scope.
  `cx, cy = self.x, self.y`
- Line 78: Variable 'tl' is too short for its scope.
  `tl, t_ang_rad = self.track_len, math.radians(ang + 90)`
- Line 88: Variable 'pt' is too short for its scope.
  `flat_hbp = [c for pt in hbp for c in pt]`
- Line 88: Variable 'c' is too short for its scope.
  `flat_hbp = [c for pt in hbp for c in pt]`
- Line 92: Variable 'p1' is too short for its scope.
  `p1 = self.rotate_point(cx, cy - tl/2, cx, cy, cos_t, sin_t)`
- ... and 13 more.
#### Function Naming
- Line 59: Function 'rotate_point' may not be a verb phrase.
  `def rotate_point(self, px, py, cx, cy, cos_a, sin_a):`
- Line 64: Function 'render' may not be a verb phrase.
  `def render(self):`
- Line 138: Function 'lift' may not be a verb phrase.
  `def lift(self):`

---
### workers/builder/composite_mdp/tester.py
#### Function Naming
- Line 39: Function 'rotate_point' may not be a verb phrase.
  `def rotate_point(self, px, py, cx, cy, angle_deg):`
- Line 46: Function 'render' may not be a verb phrase.
  `def render(self):`
- Line 102: Function 'lift' may not be a verb phrase.
  `def lift(self):`
#### Short Variable Name
- Line 42: Variable 'nx' is too short for its scope.
  `nx = cos_a * (px - cx) - sin_a * (py - cy) + cx`
- Line 43: Variable 'ny' is too short for its scope.
  `ny = sin_a * (px - cx) + cos_a * (py - cy) + cy`
- Line 48: Variable 'cx' is too short for its scope.
  `cx, cy, ang, tl = self.x, self.y, self.angle, self.track_len`
- Line 48: Variable 'cy' is too short for its scope.
  `cx, cy, ang, tl = self.x, self.y, self.angle, self.track_len`
- Line 48: Variable 'tl' is too short for its scope.
  `cx, cy, ang, tl = self.x, self.y, self.angle, self.track_len`
- Line 58: Variable 'pt' is too short for its scope.
  `flat_hbp = [coord for pt in hbp for coord in pt]`
- Line 62: Variable 'p1' is too short for its scope.
  `p1 = self.rotate_point(cx, cy - tl/2, cx, cy, ang)`
- Line 63: Variable 'p2' is too short for its scope.
  `p2 = self.rotate_point(cx, cy + tl/2, cx, cy, ang)`
- Line 80: Variable 'r' is too short for its scope.
  `r = 22`
- Line 89: Variable 'px' is too short for its scope.
  `px, py = ccx + (r-2)*math.cos(prad), ccy - (r-2)*math.sin(prad)`
- ... and 6 more.
#### Magic Number
- Line 51: Literal '60' should be a named constant.
  `hb_w = 60`
- Line 53: Literal '20' should be a named constant.
  `self.rotate_point(cx - hb_w/2, cy - tl/2 - 20, cx, cy, ang),`
- Line 54: Literal '20' should be a named constant.
  `self.rotate_point(cx + hb_w/2, cy - tl/2 - 20, cx, cy, ang),`
- Line 55: Literal '20' should be a named constant.
  `self.rotate_point(cx + hb_w/2, cy + tl/2 + 20, cx, cy, ang),`
- Line 56: Literal '20' should be a named constant.
  `self.rotate_point(cx - hb_w/2, cy + tl/2 + 20, cx, cy, ang)`
- Line 69: Literal '10' should be a named constant.
  `ly = (cy + tl/2) - (tl * (i/10))`
- Line 70: Literal '5' should be a named constant.
  `leng = 10 if i % 5 == 0 else 5`
- Line 70: Literal '10' should be a named constant.
  `leng = 10 if i % 5 == 0 else 5`
- Line 70: Literal '5' should be a named constant.
  `leng = 10 if i % 5 == 0 else 5`
- Line 80: Literal '22' should be a named constant.
  `r = 22`
- ... and 14 more.

---
### workers/splash_screen/makegif.py
#### Magic Number
- Line 29: Literal '6' should be a named constant.
  `WIDTH, HEIGHT = 6, 2.5`
- Line 40: Literal '4' should be a named constant.
  `ax.set_xlim(0, 4 * np.pi)`
- Line 43: Literal '120' should be a named constant.
  `num_bars = 120`
- Line 44: Literal '4' should be a named constant.
  `x_vals = np.linspace(0, 4 * np.pi, num_bars)`
- Line 65: Literal '0.08' should be a named constant.
  `x_vals, np.zeros(num_bars), width=0.08, color=bar_colors, alpha=alpha_bar`
- Line 73: Literal '0.15' should be a named constant.
  `bars1, line1 = create_layer(0.15, "#1E90FF", 1.0, 0.3)`
- Line 73: Literal '0.3' should be a named constant.
  `bars1, line1 = create_layer(0.15, "#1E90FF", 1.0, 0.3)`
- Line 75: Literal '1.5' should be a named constant.
  `bars2, line2 = create_layer(0.25, "#3633FD", 1.5, 0.5)`
- Line 87: Literal '0.025' should be a named constant.
  `envelope = np.exp(-0.025 * (np.linspace(-10, 10, num_bars)) ** 2)`
- Line 87: Literal '10' should be a named constant.
  `envelope = np.exp(-0.025 * (np.linspace(-10, 10, num_bars)) ** 2)`
- ... and 24 more.
#### Short Variable Name
- Line 37: Variable 'ax' is too short for its scope.
  `ax = fig.add_axes([0, 0.0, 1, 1.0], facecolor=BG_COLOR)`
- Line 48: Variable 'cm' is too short for its scope.
  `cm = LinearSegmentedColormap.from_list("orange_blue", colors, N=num_bars)`
- Line 113: Variable 't' is too short for its scope.
  `t = 2 * np.pi * progress  # Perfect Loop`
- Line 118: Variable 'h1' is too short for its scope.
  `h1 = get_wave(t, 1.0, 0) * envelope * 6 * (1.0 + 0.1 * np.sin(t))`
- Line 121: Variable 'h2' is too short for its scope.
  `h2 = get_wave(t, 2.0, 1.5) * envelope * 8 * (1.0 + 0.15 * np.sin(2 * t))`
- Line 125: Variable 'h3' is too short for its scope.
  `h3 = raw_main * envelope * 10 * (1.0 + 0.1 * np.sin(t))`
- Line 129: Variable 'h4' is too short for its scope.
  `h4 = raw_elec * envelope * 7 * (1.0 + 0.2 * np.sin(3 * t))`
- Line 137: Variable 'h5' is too short for its scope.
  `h5 = harmonics * envelope * 18 * spike_trigger`

---
### workers/builder/fader/core/scale.py
#### Function Naming
- Line 8: Function 'draw' may not be a verb phrase.
  `def draw(canvas, frame, width, height, layout):`
#### Short Variable Name
- Line 10: Variable 'cx' is too short for its scope.
  `cx = layout['cx']`
- Line 40: Variable 'ti' is too short for its scope.
  `ti = ScaleDrawer._get_smart_interval(frame, v_range)`
#### Magic Number
- Line 15: Literal '40' should be a named constant.
  `cap_w = layout.get('cap_width', 40)`
- Line 54: Literal '10' should be a named constant.
  `if v_range <= 0: return 10`
- Line 56: Literal '10.0' should be a named constant.
  `raw = v_range / 10.0`
- Line 58: Literal '10' should be a named constant.
  `frac = raw / (10**exp)`
- Line 62: Literal '5' should be a named constant.
  `elif frac < 7.5: snap = 5`
- Line 63: Literal '10' should be a named constant.
  `else: snap = 10`
- Line 64: Literal '10' should be a named constant.
  `return snap * (10**exp)`
- Line 69: Literal '5000' should be a named constant.
  `label_map = [(5000, 500), (1000, 200), (500, 50), (250, 20), (100, 10), (50, 5), (20, 2)]`
- Line 69: Literal '500' should be a named constant.
  `label_map = [(5000, 500), (1000, 200), (500, 50), (250, 20), (100, 10), (50, 5), (20, 2)]`
- Line 69: Literal '1000' should be a named constant.
  `label_map = [(5000, 500), (1000, 200), (500, 50), (250, 20), (100, 10), (50, 5), (20, 2)]`
- ... and 29 more.

---
### workers/builder/button_trapezoid/core/trapezoid_renderer_mixin.py
#### Short Variable Name
- Line 20: Variable 'w' is too short for its scope.
  `w = int(canvas.winfo_width()) if canvas.winfo_width() > 1 else config.get("width", 80)`
- Line 21: Variable 'h' is too short for its scope.
  `h = int(canvas.winfo_height()) if canvas.winfo_height() > 1 else config.get("height", 50) + (25 if state.get("label") else 0)`
- Line 23: Variable 'cw' is too short for its scope.
  `cw, ch = w / 2, h / 2`
- Line 23: Variable 'ch' is too short for its scope.
  `cw, ch = w / 2, h / 2`
- Line 24: Variable 'bw' is too short for its scope.
  `bw, bh = w * 0.8, config.get("height", 50) * 0.8`
- Line 24: Variable 'bh' is too short for its scope.
  `bw, bh = w * 0.8, config.get("height", 50) * 0.8`
- Line 31: Variable 'dy' is too short for its scope.
  `dy = 4 if pressed else 0`
- Line 42: Variable 'bx' is too short for its scope.
  `bx, by = cw - bw / 2, ch - bh / 2 - (10 if lbl else 0)`
- Line 42: Variable 'by' is too short for its scope.
  `bx, by = cw - bw / 2, ch - bh / 2 - (10 if lbl else 0)`
- Line 43: Variable 'by' is too short for its scope.
  `if lbl: by += 10`
- ... and 12 more.
#### Magic Number
- Line 20: Literal '80' should be a named constant.
  `w = int(canvas.winfo_width()) if canvas.winfo_width() > 1 else config.get("width", 80)`
- Line 21: Literal '50' should be a named constant.
  `h = int(canvas.winfo_height()) if canvas.winfo_height() > 1 else config.get("height", 50) + (25 if state.get("label") else 0)`
- Line 21: Literal '25' should be a named constant.
  `h = int(canvas.winfo_height()) if canvas.winfo_height() > 1 else config.get("height", 50) + (25 if state.get("label") else 0)`
- Line 24: Literal '0.8' should be a named constant.
  `bw, bh = w * 0.8, config.get("height", 50) * 0.8`
- Line 24: Literal '50' should be a named constant.
  `bw, bh = w * 0.8, config.get("height", 50) * 0.8`
- Line 24: Literal '0.8' should be a named constant.
  `bw, bh = w * 0.8, config.get("height", 50) * 0.8`
- Line 31: Literal '4' should be a named constant.
  `dy = 4 if pressed else 0`
- Line 35: Literal '0.8' should be a named constant.
  `face_color = self._adjust_color_lightness(base_color, 0.8 if pressed else 1.0)`
- Line 36: Literal '1.2' should be a named constant.
  `top_bevel = self._adjust_color_lightness(base_color, 1.2 if not pressed else 0.9)`
- Line 36: Literal '0.9' should be a named constant.
  `top_bevel = self._adjust_color_lightness(base_color, 1.2 if not pressed else 0.9)`
- ... and 10 more.

---
### workers/builder/panels/panel_generator.py
#### Function Naming
- Line 29: Function 'generate_panel' may not be a verb phrase.
  `def generate_panel(width, height, config={}):`
#### Magic Number
- Line 45: Literal '1000000' should be a named constant.
  `seed = random.randint(1, 1000000)`
- Line 57: Literal '0.3' should be a named constant.
  `dust_cfg = params.get("dust", {"enabled": False, "intensity": 0.3})`
- Line 69: Literal '0.15' should be a named constant.
  `grain_int = float(base_cfg.get("grain_intensity", 0.15))`
- Line 77: Literal '80' should be a named constant.
  `wrinkle = Image.effect_noise((width, height), sigma=80).convert("RGBA")`
- Line 81: Literal '10' should be a named constant.
  `h = SubstrateFactory.generate_streaks(width, height, vertical=False, sigma=10)`
- Line 82: Literal '10' should be a named constant.
  `v = SubstrateFactory.generate_streaks(width, height, vertical=True, sigma=10)`
- Line 87: Literal '4' should be a named constant.
  `peel = Image.effect_noise((width // 4, height // 4), sigma=10).resize((width, height), Image.BICUBIC).convert("RGBA")`
- Line 87: Literal '4' should be a named constant.
  `peel = Image.effect_noise((width // 4, height // 4), sigma=10).resize((width, height), Image.BICUBIC).convert("RGBA")`
- Line 87: Literal '10' should be a named constant.
  `peel = Image.effect_noise((width // 4, height // 4), sigma=10).resize((width, height), Image.BICUBIC).convert("RGBA")`
- Line 90: Literal '20' should be a named constant.
  `sigma = 20 if texture_type == "brushed" else 5`
- ... and 25 more.
#### Short Variable Name
- Line 81: Variable 'h' is too short for its scope.
  `h = SubstrateFactory.generate_streaks(width, height, vertical=False, sigma=10)`
- Line 82: Variable 'v' is too short for its scope.
  `v = SubstrateFactory.generate_streaks(width, height, vertical=True, sigma=10)`
#### Encoding/Prefix
- Line 103: Variable 's_depth' uses legacy prefix.
  `s_depth = int(edge_cfg.get("scratch_depth", 30))`
- Line 104: Variable 's_mask' uses legacy prefix.
  `s_mask = Image.new('L', (width, height), 0)`
- Line 159: Variable 'f_depth' uses legacy prefix.
  `f_depth = min(int(edge_cfg.get("fade_depth", 110)), min(width, height) // 2)`

---
### workers/builder/panel_screw/screw_generator.py
#### Function Naming
- Line 19: Function 'generate_screw' may not be a verb phrase.
  `def generate_screw(size_px, config={}):`
#### Magic Number
- Line 34: Literal '0.4' should be a named constant.
  `padding = int(size_px * 0.4)`
- Line 49: Literal '90' should be a named constant.
  `rotation = float(config.get("angle", random.randint(0, 90)))`
- Line 64: Literal '0.1' should be a named constant.
  `shadow_blur = size_px * 0.1`
- Line 67: Literal '0.05' should be a named constant.
  `shadow_blur = size_px * 0.05`
- Line 81: Literal '255' should be a named constant.
  `fill=rgb_color + (255,))`
- Line 90: Literal '0.3' should be a named constant.
  `spec_off = int(radius * 0.3)`
- Line 93: Literal '255' should be a named constant.
  `center, center), fill=255) # Highlight`
- Line 111: Literal '255' should be a named constant.
  `m_draw.ellipse((center - radius, center - radius, center + radius, center + radius), fill=255)`
- Line 119: Literal '0.55' should be a named constant.
  `drive_size = radius * 0.55`
- Line 139: Literal '20' should be a named constant.
  `d_draw.polygon(rotated_points, fill=(20, 20, 20, 240))`
- ... and 16 more.
#### Encoding/Prefix
- Line 55: Variable 's_draw' uses legacy prefix.
  `s_draw = ImageDraw.Draw(shadow_layer)`
- Line 110: Variable 'm_draw' uses legacy prefix.
  `m_draw = ImageDraw.Draw(mask)`
- Line 172: Variable 's_angle' uses legacy prefix.
  `s_angle = random.uniform(0, 360)`
#### Short Variable Name
- Line 149: Variable 'p0' is too short for its scope.
  `p0, p1, p2, p3 = rotated_points`
- Line 149: Variable 'p1' is too short for its scope.
  `p0, p1, p2, p3 = rotated_points`
- Line 149: Variable 'p2' is too short for its scope.
  `p0, p1, p2, p3 = rotated_points`
- Line 149: Variable 'p3' is too short for its scope.
  `p0, p1, p2, p3 = rotated_points`
- Line 214: Variable 'c' is too short for its scope.
  `c = hex_str.lstrip('#')`
- Line 215: Variable 'i' is too short for its scope.
  `return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))`

---
### managers/Display/transparency/transparency_manager.py
#### Function Naming
- Line 16: Function 'cleanup' may not be a verb phrase.
  `def cleanup(builder_instance):`
- Line 30: Function 'apply_transparency' may not be a verb phrase.
  `def apply_transparency(widget, canvas, config, builder_instance):`
#### Short Variable Name
- Line 47: Variable 'bg' is too short for its scope.
  `bg = config.get("bg_color") or config.get("bg") or config.get("background_color")`
- Line 52: Variable 'bg' is too short for its scope.
  `bg = style.get("background_color") or style.get("bg_color") or style.get("bg")`
- Line 57: Variable 'k' is too short for its scope.
  `is_struct_type = any(config.get(k) in STRUCTURAL_TYPES for k in ["type", "widget_type"])`
- Line 100: Variable 'w' is too short for its scope.
  `w, h = 0, 0`
- Line 100: Variable 'h' is too short for its scope.
  `w, h = 0, 0`
- Line 102: Variable 'w' is too short for its scope.
  `w, h = draw_target.winfo_width(), draw_target.winfo_height()`
- Line 102: Variable 'h' is too short for its scope.
  `w, h = draw_target.winfo_width(), draw_target.winfo_height()`
- Line 125: Variable 'wx' is too short for its scope.
  `wx, wy = 0, 0`
- Line 125: Variable 'wy' is too short for its scope.
  `wx, wy = 0, 0`
- Line 128: Variable 'wx' is too short for its scope.
  `wx, wy = cache[id(draw_target)]`
- ... and 21 more.
#### Magic Number
- Line 186: Literal '3' should be a named constant.
  `hex_bg = '#%02x%02x%02x' % center_rgb[:3]`

---
### workers/builder/data_graphing/core/view_controller.py
#### Short Variable Name
- Line 14: Variable 'x' is too short for its scope.
  `bbox, x, y = self.ax.bbox, event.x, event.y`
- Line 14: Variable 'y' is too short for its scope.
  `bbox, x, y = self.ax.bbox, event.x, event.y`
- Line 32: Variable 'x0' is too short for its scope.
  `x0, y0 = self.rect_start; x1, y1 = event.xdata, event.ydata`
- Line 32: Variable 'y0' is too short for its scope.
  `x0, y0 = self.rect_start; x1, y1 = event.xdata, event.ydata`
- Line 32: Variable 'x1' is too short for its scope.
  `x0, y0 = self.rect_start; x1, y1 = event.xdata, event.ydata`
- Line 32: Variable 'y1' is too short for its scope.
  `x0, y0 = self.rect_start; x1, y1 = event.xdata, event.ydata`
- Line 41: Variable 'w' is too short for its scope.
  `x_start, y_start = self.press; w, h = self.ax.bbox.width, self.ax.bbox.height`
- Line 41: Variable 'h' is too short for its scope.
  `x_start, y_start = self.press; w, h = self.ax.bbox.width, self.ax.bbox.height`
- Line 43: Variable 's' is too short for its scope.
  `if self.axis_mode == 'x': s = max(0.1, 1.0 - ((event.x - x_start)/500.0)); vmin, vmax = self.cur_xlim; c = (vmin+vmax)/2; sp = ((vmax-vmin)/2)*s; self.ax.set_xlim(c-sp, c+sp)`
- Line 43: Variable 'c' is too short for its scope.
  `if self.axis_mode == 'x': s = max(0.1, 1.0 - ((event.x - x_start)/500.0)); vmin, vmax = self.cur_xlim; c = (vmin+vmax)/2; sp = ((vmax-vmin)/2)*s; self.ax.set_xlim(c-sp, c+sp)`
- ... and 16 more.
#### Magic Number
- Line 43: Literal '0.1' should be a named constant.
  `if self.axis_mode == 'x': s = max(0.1, 1.0 - ((event.x - x_start)/500.0)); vmin, vmax = self.cur_xlim; c = (vmin+vmax)/2; sp = ((vmax-vmin)/2)*s; self.ax.set_xlim(c-sp, c+sp)`
- Line 43: Literal '500.0' should be a named constant.
  `if self.axis_mode == 'x': s = max(0.1, 1.0 - ((event.x - x_start)/500.0)); vmin, vmax = self.cur_xlim; c = (vmin+vmax)/2; sp = ((vmax-vmin)/2)*s; self.ax.set_xlim(c-sp, c+sp)`
- Line 44: Literal '0.1' should be a named constant.
  `else: s = max(0.1, 1.0 - ((event.y - y_start)/500.0)); vmin, vmax = self.cur_ylim; c = (vmin+vmax)/2; sp = ((vmax-vmin)/2)*s; self.ax.set_ylim(c-sp, c+sp)`
- Line 44: Literal '500.0' should be a named constant.
  `else: s = max(0.1, 1.0 - ((event.y - y_start)/500.0)); vmin, vmax = self.cur_ylim; c = (vmin+vmax)/2; sp = ((vmax-vmin)/2)*s; self.ax.set_ylim(c-sp, c+sp)`
- Line 62: Literal '1.1' should be a named constant.
  `f = 1/1.1 if event.button == "up" else 1.1; cur_x, cur_y = self.ax.get_xlim(), self.ax.get_ylim(); xd, yd = event.xdata, event.ydata`
- Line 62: Literal '1.1' should be a named constant.
  `f = 1/1.1 if event.button == "up" else 1.1; cur_x, cur_y = self.ax.get_xlim(), self.ax.get_ylim(); xd, yd = event.xdata, event.ydata`
#### Function Naming
- Line 67: Function 'reset_view' may not be a verb phrase.
  `def reset_view(self):`

---
### workers/builder/circular_motion_displacement_potentiometer/core/ltp_fader.py
#### Magic Number
- Line 24: Literal '100.0' should be a named constant.
  `self.val_min, self.val_max = 0.0, 100.0`
- Line 26: Literal '100.0' should be a named constant.
  `self.rot_min, self.rot_max = 0.0, 100.0`
- Line 48: Literal '90' should be a named constant.
  `t_ang = ang + 90`
- Line 58: Literal '10.0' should be a named constant.
  `norm = i / 10.0`
- Line 60: Literal '5' should be a named constant.
  `leng = 10 if i % 5 == 0 else 5`
- Line 60: Literal '10' should be a named constant.
  `leng = 10 if i % 5 == 0 else 5`
- Line 60: Literal '5' should be a named constant.
  `leng = 10 if i % 5 == 0 else 5`
- Line 61: Literal '15' should be a named constant.
  `tp1 = CircularMath.rotate_point(cx - 15, cy + local_y, cx, cy, t_ang)`
- Line 62: Literal '15' should be a named constant.
  `tp2 = CircularMath.rotate_point(cx - 15 - leng, cy + local_y, cx, cy, t_ang)`
- Line 64: Literal '15' should be a named constant.
  `tp3 = CircularMath.rotate_point(cx + 15, cy + local_y, cx, cy, t_ang)`
- ... and 12 more.
#### Function Naming
- Line 43: Function 'render' may not be a verb phrase.
  `def render(self):`
- Line 94: Function 'lift' may not be a verb phrase.
  `def lift(self):`
#### Short Variable Name
- Line 47: Variable 'cx' is too short for its scope.
  `cx, cy, ang, tl = self.x, self.y, self.angle, self.track_len`
- Line 47: Variable 'cy' is too short for its scope.
  `cx, cy, ang, tl = self.x, self.y, self.angle, self.track_len`
- Line 47: Variable 'tl' is too short for its scope.
  `cx, cy, ang, tl = self.x, self.y, self.angle, self.track_len`
- Line 51: Variable 'p1' is too short for its scope.
  `p1 = CircularMath.rotate_point(cx, cy - tl/2, cx, cy, t_ang)`
- Line 52: Variable 'p2' is too short for its scope.
  `p2 = CircularMath.rotate_point(cx, cy + tl/2, cx, cy, t_ang)`
- Line 71: Variable 'r' is too short for its scope.
  `r = 22`
- Line 87: Variable 'lx' is too short for its scope.
  `lx, ly = (600, 450) if is_active else CircularMath.get_position(self.angle, FAR_RADIUS + 25 + (self.widget_id%2)*25)`
- Line 87: Variable 'ly' is too short for its scope.
  `lx, ly = (600, 450) if is_active else CircularMath.get_position(self.angle, FAR_RADIUS + 25 + (self.widget_id%2)*25)`

---
### workers/builder/circular_motion_displacement_potentiometer/cmdp_group_handler.py
#### Short Variable Name
- Line 37: Variable 'iv' is too short for its scope.
  `iv = tk.BooleanVar(value=initial_visible)`
- Line 38: Variable 'im' is too short for its scope.
  `im = tk.BooleanVar(value=initial_mute)`
- Line 39: Variable 'cv' is too short for its scope.
  `cv = tk.StringVar(value=color)`
- Line 40: Variable 'nv' is too short for its scope.
  `nv = tk.StringVar(value=group_name)`
- Line 55: Variable 'bp' is too short for its scope.
  `bp = f"{self.w.path}/groups/{group_name}"`
- Line 56: Variable 'iv' is too short for its scope.
  `iv, im, cv, nv = vars["visible"], vars["mute"], vars["color"], vars["name"]`
- Line 56: Variable 'im' is too short for its scope.
  `iv, im, cv, nv = vars["visible"], vars["mute"], vars["color"], vars["name"]`
- Line 56: Variable 'cv' is too short for its scope.
  `iv, im, cv, nv = vars["visible"], vars["mute"], vars["color"], vars["name"]`
- Line 56: Variable 'nv' is too short for its scope.
  `iv, im, cv, nv = vars["visible"], vars["mute"], vars["color"], vars["name"]`
- Line 79: Variable 'fr' is too short for its scope.
  `fr = tk.Frame(self.w.groups_container)`
- ... and 10 more.
#### Magic Number
- Line 90: Literal '8' should be a named constant.
  `lbl = tk.Label(fr, textvariable=nv, fg=cv.get(), anchor="w", cursor="hand2", font=("Arial", 8, "bold"))`
- Line 101: Literal '7' should be a named constant.
  `btn = tk.Button(parent, text="👁", bg="#f4902c", fg="black", width=1, bd=0, font=("Arial", 7),`
- Line 109: Literal '7' should be a named constant.
  `btn = tk.Button(parent, text="🔊", bg="#f4902c", fg="black", width=1, bd=0, font=("Arial", 7),`
#### Function Naming
- Line 134: Function 'solo_group_visibility' may not be a verb phrase.
  `def solo_group_visibility(self, target_name):`
- Line 137: Function 'show_all_groups' may not be a verb phrase.
  `def show_all_groups(self):`
- Line 140: Function 'solo_group_mute' may not be a verb phrase.
  `def solo_group_mute(self, target_name):`
- Line 143: Function 'unmute_all_groups' may not be a verb phrase.
  `def unmute_all_groups(self):`
- Line 146: Function 'toggle_group_mute' may not be a verb phrase.
  `def toggle_group_mute(self, group_name):`
- Line 173: Function 'rename_group' may not be a verb phrase.
  `def rename_group(self, old):`
- Line 177: Function 'pick_group_color' may not be a verb phrase.
  `def pick_group_color(self, name):`

---
### assets/Stand Alone Utilities/SUB APP - CSV to json APP/csvtojson.py
#### Magic Number
- Line 29: Literal '10' should be a named constant.
  `top = tk.Frame(self, padx=10, pady=10); top.pack(fill=tk.X)`
- Line 29: Literal '10' should be a named constant.
  `top = tk.Frame(self, padx=10, pady=10); top.pack(fill=tk.X)`
- Line 31: Literal '5' should be a named constant.
  `self.csv_en = tk.Entry(top, width=50); self.csv_en.grid(row=0, column=1, padx=5)`
- Line 35: Literal '5' should be a named constant.
  `self.json_en = tk.Entry(top, width=50); self.json_en.grid(row=1, column=1, padx=5)`
- Line 39: Literal '5' should be a named constant.
  `self.root_en = tk.Entry(top, width=20); self.root_en.insert(0, "root"); self.root_en.grid(row=2, column=1, sticky="W", padx=5)`
- Line 41: Literal '10' should be a named constant.
  `btns = tk.Frame(top); btns.grid(row=3, column=0, columnspan=3, pady=10)`
- Line 42: Literal '5' should be a named constant.
  `tk.Button(btns, text="Load Headers", command=self.load_headers).pack(side=tk.LEFT, padx=5)`
- Line 43: Literal '5' should be a named constant.
  `tk.Button(btns, text="Preview JSON", command=self.preview).pack(side=tk.LEFT, padx=5)`
- Line 44: Literal '5' should be a named constant.
  `tk.Button(btns, text="Convert & Save", command=self.convert).pack(side=tk.LEFT, padx=5)`
- Line 47: Literal '10' should be a named constant.
  `main = tk.Frame(self, padx=10, pady=10); main.pack(fill=tk.BOTH, expand=True)`
- ... and 5 more.
#### Function Naming
- Line 63: Function 'load_csv' may not be a verb phrase.
  `def load_csv(self):`
- Line 69: Function 'save_json_dlg' may not be a verb phrase.
  `def save_json_dlg(self):`
- Line 73: Function 'load_headers' may not be a verb phrase.
  `def load_headers(self):`
- Line 82: Function 'generate_data' may not be a verb phrase.
  `def generate_data(self):`
- Line 94: Function 'preview' may not be a verb phrase.
  `def preview(self):`
- Line 98: Function 'convert' may not be a verb phrase.
  `def convert(self):`
#### Short Variable Name
- Line 64: Variable 'fp' is too short for its scope.
  `fp = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])`
- Line 70: Variable 'fp' is too short for its scope.
  `fp = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])`
- Line 77: Variable 'df' is too short for its scope.
  `df = pd.read_csv(self.csv_filepath, nrows=1, keep_default_na=False)`
- Line 84: Variable 'df' is too short for its scope.
  `df = pd.read_csv(self.csv_filepath, keep_default_na=False)`
- Line 86: Variable 'h' is too short for its scope.
  `sort_cols = [h for h, cfg in h_map.items() if cfg["role"] in ["Hierarchical Key", "Value as Key", "Key Name and Value"]]`
- Line 104: Variable 'f' is too short for its scope.
  `with open(path, "wb") as f: f.write(orjson.dumps(data))`
#### Noise Word
- Line 95: Variable 'data' contains redundant word 'Data'.
  `data = self.generate_data()`
- Line 101: Variable 'data' contains redundant word 'Data'.
  `data = self.generate_data()`

---
### display/right_50/bottom_90/2_monitors/22_Yak_Monitor/gui_yak_monitor.py
#### Magic Number
- Line 88: Literal '5' should be a named constant.
  `self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)`
- Line 88: Literal '5' should be a named constant.
  `self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)`
- Line 91: Literal '12' should be a named constant.
  `lbl = ttk.Label(self.main_frame, text="Yak Traffic Monitor", font=("Helvetica", 12, "bold"), style="Dark.TLabel")`
- Line 92: Literal '5' should be a named constant.
  `lbl.pack(side=tk.TOP, pady=(0, 5))`
- Line 139: Literal '5' should be a named constant.
  `self.dissect_header_frame.pack(side=tk.TOP, fill=tk.X, pady=(5, 0))`
- Line 155: Literal '10' should be a named constant.
  `font=("Helvetica", 10, "bold"), style="Dark.TLabel", padding=(0, 0, 10, 0))`
- Line 155: Literal '10' should be a named constant.
  `font=("Helvetica", 10, "bold"), style="Dark.TLabel", padding=(0, 0, 10, 0))`
- Line 179: Literal '5' should be a named constant.
  `self.btn_clear.pack(side=tk.BOTTOM, pady=5)`
- Line 203: Literal '3' should be a named constant.
  `model = parts[3] if len(parts) > 3 else "-"`
- Line 203: Literal '3' should be a named constant.
  `model = parts[3] if len(parts) > 3 else "-"`
- ... and 10 more.
#### Noise Word
- Line 212: Variable 'data' contains redundant word 'Data'.
  `data = orjson.loads(payload)`
- Line 262: Variable 'data' contains redundant word 'Data'.
  `data = orjson.loads(payload)`
- Line 285: Variable 'data' contains redundant word 'Data'.
  `data = orjson.loads(payload)`
#### Function Naming
- Line 268: Function 'jump_to_latest_message' may not be a verb phrase.
  `def jump_to_latest_message(self):`
- Line 278: Function 'jump_to_latest_val_msg' may not be a verb phrase.
  `def jump_to_latest_val_msg(self):`
- Line 314: Function 'clear_log' may not be a verb phrase.
  `def clear_log(self):`
- Line 320: Function 'render' may not be a verb phrase.
  `def render(self):`
- Line 326: Function 'destroy' may not be a verb phrase.
  `def destroy(self):`
#### Short Variable Name
- Line 322: Variable 'bg' is too short for its scope.
  `bg = self.cget("bg")`

---
### workers/builder/meter_bar/core/layout_calculator.py
#### Function Naming
- Line 41: Function 'calculate' may not be a verb phrase.
  `def calculate(self, w: int, h: int, cfg) -> LayoutResult:`
- Line 231: Function 'norm' may not be a verb phrase.
  `def norm(v): return (v - cfg.min_val) / (cfg.max_val - cfg.min_val)`
#### Magic Number
- Line 45: Literal '15' should be a named constant.
  `scale_text_padding = 15 # Horizontal buffer for numbers`
- Line 49: Literal '3' should be a named constant.
  `label_thickness = (cfg.font_size * 3) if (cfg.scale_position != "none" and cfg.show_scale_labels) else 0`
- Line 51: Literal '4' should be a named constant.
  `label_thickness = (cfg.font_size + 4) if (cfg.scale_position != "none" and cfg.show_scale_labels) else 0`
- Line 64: Literal '5' should be a named constant.
  `peak_led_gap = 5 if cfg.peak_display else 0`
- Line 89: Literal '5' should be a named constant.
  `peak_led_gap = 5 if cfg.peak_display else 0`
- Line 148: Literal '5' should be a named constant.
  `num_main = 5`
- Line 158: Literal '5' should be a named constant.
  `label_x, label_y = tx2, ty2 + (5 * tick_dir)`
- Line 164: Literal '5' should be a named constant.
  `label_x, label_y = tx2 + (5 * tick_dir), ty2`
- Line 224: Literal '5' should be a named constant.
  `indicator=get_poly(0, 5, 0, b_thick), # placeholder`
- Line 273: Literal '0.15' should be a named constant.
  `ext = layout.bar_thick * 0.15`
- ... and 1 more.
#### Short Variable Name
- Line 111: Variable 'x1' is too short for its scope.
  `x1 = bar_x + v_start`
- Line 112: Variable 'x2' is too short for its scope.
  `x2 = bar_x + v_end`
- Line 113: Variable 'y1' is too short for its scope.
  `y1 = bar_y + t_start`
- Line 114: Variable 'y2' is too short for its scope.
  `y2 = bar_y + t_end`
- Line 125: Variable 'cx' is too short for its scope.
  `cx, cy = bar_x + (b_len / 2), bar_y + (b_thick / 2)`
- Line 125: Variable 'cy' is too short for its scope.
  `cx, cy = bar_x + (b_len / 2), bar_y + (b_thick / 2)`
- Line 238: Variable 'x1' is too short for its scope.
  `x1 = layout.bar_x + v_start`
- Line 239: Variable 'x2' is too short for its scope.
  `x2 = layout.bar_x + v_end`
- Line 240: Variable 'y1' is too short for its scope.
  `y1 = layout.bar_y + t_start`
- Line 241: Variable 'y2' is too short for its scope.
  `y2 = layout.bar_y + t_end`
- ... and 5 more.

---
### workers/builder/meter_needle/config/meter_config.py
#### Function Naming
- Line 82: Function 'widget_label_color' may not be a verb phrase.
  `def widget_label_color(self):`
- Line 86: Function 'intended_bg' may not be a verb phrase.
  `def intended_bg(self): return "transparent"`
- Line 92: Function 'bezel_shape' may not be a verb phrase.
  `def bezel_shape(self):`
- Line 96: Function 'faceplate_color' may not be a verb phrase.
  `def faceplate_color(self):`
- Line 101: Function 'canvas_bg' may not be a verb phrase.
  `def canvas_bg(self): return self.default_theme_bg`
- Line 104: Function 'fg_color' may not be a verb phrase.
  `def fg_color(self):`
- Line 109: Function 'scale_label_color' may not be a verb phrase.
  `def scale_label_color(self):`
- Line 113: Function 'scale_padding' may not be a verb phrase.
  `def scale_padding(self):`
- Line 117: Function 'needle_scale' may not be a verb phrase.
  `def needle_scale(self):`
- Line 121: Function 'size' may not be a verb phrase.
  `def size(self):`
- ... and 14 more.
#### Short Variable Name
- Line 97: Variable 'c' is too short for its scope.
  `c = self.colors_cfg.get("meter_face_colour") or self.config.get("meter_face_colour") or self.colors_cfg.get("faceplate")`
- Line 105: Variable 'c' is too short for its scope.
  `c = self.colors_cfg.get("foreground", self.config.get("fg_color", ""))`
- Line 150: Variable 'v' is too short for its scope.
  `v = self.config.get("reff_point", self.config.get("zero_point"))`

---
### workers/builder/data_radar/data_radar.py
#### Function Naming
- Line 29: Function 'make_data_radar' may not be a verb phrase.
  `def make_data_radar(self, parent_widget, config_data, context=None, **kwargs):`
- Line 111: Function 'draw_static_grid' may not be a verb phrase.
  `def draw_static_grid():`
- Line 177: Function 'redraw_full' may not be a verb phrase.
  `def redraw_full():`
- Line 212: Function 'sweep_loop' may not be a verb phrase.
  `def sweep_loop():`
- Line 225: Function 'perform_resize' may not be a verb phrase.
  `def perform_resize(w, h):`
#### Noise Word
- Line 56: Variable 'data_parameters' contains redundant word 'Data'.
  `data_parameters = config_data.get("data_parameters", {})`
#### Magic Number
- Line 61: Literal '600' should be a named constant.
  `width = app_settings.get("window_size", [600, 600])[0]`
- Line 61: Literal '600' should be a named constant.
  `width = app_settings.get("window_size", [600, 600])[0]`
- Line 62: Literal '600' should be a named constant.
  `height = app_settings.get("window_size", [600, 600])[1]`
- Line 62: Literal '600' should be a named constant.
  `height = app_settings.get("window_size", [600, 600])[1]`
- Line 63: Literal '33' should be a named constant.
  `refresh_rate = app_settings.get("refresh_rate_ms", 33)`
- Line 67: Literal '360' should be a named constant.
  `points_count = data_parameters.get("points_per_revolution", 360)`
- Line 69: Literal '90' should be a named constant.
  `start_angle = data_parameters.get("start_angle", 90)`
- Line 86: Literal '360.0' should be a named constant.
  `offset = i * (360.0 / points_count)`
- Line 94: Literal '20' should be a named constant.
  `"cx": width / 2, "cy": height / 2, "radius": min(width, height) / 2 - 20,`
- Line 130: Literal '20' should be a named constant.
  `ring_int = grid_sys.get("ring_interval", 20)`
- ... and 2 more.
#### Short Variable Name
- Line 103: Variable 'c' is too short for its scope.
  `c, s = radar_state["trig_cache"][idx % points_count]`
- Line 103: Variable 's' is too short for its scope.
  `c, s = radar_state["trig_cache"][idx % points_count]`
- Line 115: Variable 'cx' is too short for its scope.
  `cx, cy, r_max = radar_state["cx"], radar_state["cy"], radar_state["radius"]`
- Line 115: Variable 'cy' is too short for its scope.
  `cx, cy, r_max = radar_state["cx"], radar_state["cy"], radar_state["radius"]`
- Line 172: Variable 'lx' is too short for its scope.
  `lx, ly = get_pos(radar_state["current_angle_idx"], radar_state["radius"])`
- Line 172: Variable 'ly' is too short for its scope.
  `lx, ly = get_pos(radar_state["current_angle_idx"], radar_state["radius"])`
- Line 193: Variable 'dx' is too short for its scope.
  `dx, dy = event.x - radar_state["cx"], radar_state["cy"] - event.y`
- Line 193: Variable 'dy' is too short for its scope.
  `dx, dy = event.x - radar_state["cx"], radar_state["cy"] - event.y`

---
### workers/wysiwyg_editor/workspaces/layout_overlays/sizing.py
#### Function Naming
- Line 5: Function 'apply' may not be a verb phrase.
  `def apply(layout, widget, path, is_focused, design_elements):`
- Line 90: Function 'sync' may not be a verb phrase.
  `def sync(x, y, w, h):`
#### Magic Number
- Line 8: Literal '8' should be a named constant.
  `res_diag = tk.Label(widget.master, text="⤡", bg="#FF9900", fg="black", font=("Arial", 8), cursor="sizing")`
- Line 9: Literal '8' should be a named constant.
  `res_horiz = tk.Label(widget.master, text="↔", bg="#FF9900", fg="black", font=("Arial", 8), cursor="sb_h_double_arrow")`
- Line 10: Literal '8' should be a named constant.
  `res_vert = tk.Label(widget.master, text="↕", bg="#FF9900", fg="black", font=("Arial", 8), cursor="sb_v_double_arrow")`
- Line 11: Literal '6' should be a named constant.
  `pad_x_handle = tk.Label(widget.master, text="PX", bg="#33A1FD", fg="white", font=("Arial", 6, "bold"), cursor="sb_h_double_arrow")`
- Line 12: Literal '6' should be a named constant.
  `pad_y_handle = tk.Label(widget.master, text="PY", bg="#33A1FD", fg="white", font=("Arial", 6, "bold"), cursor="sb_v_double_arrow")`
- Line 22: Literal '8' should be a named constant.
  `font=("Arial", 8, "bold"), padx=5, pady=2, relief="solid", bd=1)`
- Line 22: Literal '5' should be a named constant.
  `font=("Arial", 8, "bold"), padx=5, pady=2, relief="solid", bd=1)`
- Line 46: Literal '5' should be a named constant.
  `pv = max(0, int(dx // 5))`
- Line 49: Literal '5' should be a named constant.
  `pv = max(0, int(dy // 5))`
- Line 70: Literal '5' should be a named constant.
  `state_manager.update_state(max(0, int(dx // 5)), path=f"{path}.layout.padx", source=layout)`
- ... and 1 more.
#### Short Variable Name
- Line 44: Variable 'dx' is too short for its scope.
  `dx, dy = event.x_root - widget.winfo_rootx(), event.y_root - widget.winfo_rooty()`
- Line 44: Variable 'dy' is too short for its scope.
  `dx, dy = event.x_root - widget.winfo_rootx(), event.y_root - widget.winfo_rooty()`
- Line 46: Variable 'pv' is too short for its scope.
  `pv = max(0, int(dx // 5))`
- Line 49: Variable 'pv' is too short for its scope.
  `pv = max(0, int(dy // 5))`
- Line 52: Variable 'nw' is too short for its scope.
  `nw, nh = max(20, dx), max(20, dy)`
- Line 52: Variable 'nh' is too short for its scope.
  `nw, nh = max(20, dx), max(20, dy)`
- Line 53: Variable 'nh' is too short for its scope.
  `if mode == "horiz": nh = widget.winfo_height()`
- Line 54: Variable 'nw' is too short for its scope.
  `if mode == "vert": nw = widget.winfo_width()`
- Line 67: Variable 'dx' is too short for its scope.
  `dx, dy = event.x_root - widget.winfo_rootx(), event.y_root - widget.winfo_rooty()`
- Line 67: Variable 'dy' is too short for its scope.
  `dx, dy = event.x_root - widget.winfo_rootx(), event.y_root - widget.winfo_rooty()`
- ... and 2 more.

---
### workers/builder/meter_needle/cosmetics/mask.py
#### Function Naming
- Line 11: Function 'draw' may not be a verb phrase.
  `def draw(canvas, cx, cy, w, h, cosmetics):`
#### Magic Number
- Line 30: Literal '12' should be a named constant.
  `line_width = int(style_overrides.get("bezel_width", 12))`
- Line 40: Literal '2.5' should be a named constant.
  `hill_w = radius * 2.5`
- Line 41: Literal '0.3' should be a named constant.
  `hill_h = radius * 0.3`
- Line 43: Literal '0.8' should be a named constant.
  `hill_w = radius * 0.8`
- Line 44: Literal '0.3' should be a named constant.
  `hill_h = radius * 0.3`
- Line 46: Literal '0.4' should be a named constant.
  `hill_w = radius * 0.4`
- Line 47: Literal '0.3' should be a named constant.
  `hill_h = radius * 0.3`
- Line 49: Literal '1.8' should be a named constant.
  `hill_w = radius * 1.8`
- Line 50: Literal '0.3' should be a named constant.
  `hill_h = radius * 0.3`
- Line 52: Literal '1.8' should be a named constant.
  `hill_w = radius * 1.8`
- ... and 14 more.

---
### workers/builder/composite_mdp/core/mdp_ltp_component.py
#### Function Naming
- Line 27: Function 'render' may not be a verb phrase.
  `def render(self):`
- Line 66: Function 'lift' may not be a verb phrase.
  `def lift(self): self.canvas.tag_raise(self.tag_root)`
#### Short Variable Name
- Line 29: Variable 'cx' is too short for its scope.
  `cx, cy, ang, tl = self.x, self.y, self.angle, self.track_len`
- Line 29: Variable 'cy' is too short for its scope.
  `cx, cy, ang, tl = self.x, self.y, self.angle, self.track_len`
- Line 29: Variable 'tl' is too short for its scope.
  `cx, cy, ang, tl = self.x, self.y, self.angle, self.track_len`
- Line 34: Variable 'hw' is too short for its scope.
  `hw = 60; hb = [MDPMath.rotate_point(cx-hw/2, cy-tl/2-20, cx, cy, ang), MDPMath.rotate_point(cx+hw/2, cy-tl/2-20, cx, cy, ang),`
- Line 34: Variable 'hb' is too short for its scope.
  `hw = 60; hb = [MDPMath.rotate_point(cx-hw/2, cy-tl/2-20, cx, cy, ang), MDPMath.rotate_point(cx+hw/2, cy-tl/2-20, cx, cy, ang),`
- Line 36: Variable 'p' is too short for its scope.
  `self.canvas.create_polygon([c for p in hb for c in p], fill="", outline="", tags=(self.tag_root, "hitbox"))`
- Line 36: Variable 'c' is too short for its scope.
  `self.canvas.create_polygon([c for p in hb for c in p], fill="", outline="", tags=(self.tag_root, "hitbox"))`
- Line 39: Variable 'p1' is too short for its scope.
  `p1, p2 = MDPMath.rotate_point(cx, cy-tl/2, cx, cy, ang), MDPMath.rotate_point(cx, cy+tl/2, cx, cy, ang)`
- Line 39: Variable 'p2' is too short for its scope.
  `p1, p2 = MDPMath.rotate_point(cx, cy-tl/2, cx, cy, ang), MDPMath.rotate_point(cx, cy+tl/2, cx, cy, ang)`
- Line 54: Variable 'r' is too short for its scope.
  `r = 22; out = self.outline_hover if self.hovered else self.outline_normal`
- ... and 2 more.
#### Magic Number
- Line 34: Literal '60' should be a named constant.
  `hw = 60; hb = [MDPMath.rotate_point(cx-hw/2, cy-tl/2-20, cx, cy, ang), MDPMath.rotate_point(cx+hw/2, cy-tl/2-20, cx, cy, ang),`
- Line 34: Literal '20' should be a named constant.
  `hw = 60; hb = [MDPMath.rotate_point(cx-hw/2, cy-tl/2-20, cx, cy, ang), MDPMath.rotate_point(cx+hw/2, cy-tl/2-20, cx, cy, ang),`
- Line 34: Literal '20' should be a named constant.
  `hw = 60; hb = [MDPMath.rotate_point(cx-hw/2, cy-tl/2-20, cx, cy, ang), MDPMath.rotate_point(cx+hw/2, cy-tl/2-20, cx, cy, ang),`
- Line 35: Literal '20' should be a named constant.
  `MDPMath.rotate_point(cx+hw/2, cy+tl/2+20, cx, cy, ang), MDPMath.rotate_point(cx-hw/2, cy+tl/2+20, cx, cy, ang)]`
- Line 35: Literal '20' should be a named constant.
  `MDPMath.rotate_point(cx+hw/2, cy+tl/2+20, cx, cy, ang), MDPMath.rotate_point(cx-hw/2, cy+tl/2+20, cx, cy, ang)]`
- Line 45: Literal '10.0' should be a named constant.
  `ly = (cy + tl/2) - (tl * (i/10.0)); leng = 10 if i % 5 == 0 else 5`
- Line 45: Literal '5' should be a named constant.
  `ly = (cy + tl/2) - (tl * (i/10.0)); leng = 10 if i % 5 == 0 else 5`
- Line 45: Literal '10' should be a named constant.
  `ly = (cy + tl/2) - (tl * (i/10.0)); leng = 10 if i % 5 == 0 else 5`
- Line 45: Literal '5' should be a named constant.
  `ly = (cy + tl/2) - (tl * (i/10.0)); leng = 10 if i % 5 == 0 else 5`
- Line 54: Literal '22' should be a named constant.
  `r = 22; out = self.outline_hover if self.hovered else self.outline_normal`
- ... and 1 more.

---
