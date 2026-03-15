# fader_horizontal/dynamic_guimake_fader_horizontal.py
#
# A high-performance, photorealistic horizontal fader widget.
# Refactored to use single-canvas tagging for zero-flicker surgical updates.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260220.Modular.5

import orjson
import tkinter as tk
from tkinter import ttk
import math
import sys
import os
import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageFilter, ImageChops

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from workers.styling.style import THEMES, DEFAULT_THEME
from workers.Command_Router.mqtt.mqtt_topic_utils import get_topic
from workers.handlers.widget_event_binder import bind_variable_trace
from managers.Display.transparency.transparency_mixin import TransparencyMixin
from managers.Display.transparency.transparency_manager import TransparencyManager

_HORIZONTAL_FADER_ASSET_CACHE = {}

def get_3d_horizontal_fader_cap(w, h, body_color, track_color, highlight_color=None):
    """Generates a photorealistic horizontal concave saddle fader cap."""
    cache_key = (w, h, body_color, track_color, highlight_color, "v23_vectorized")
    if cache_key in _HORIZONTAL_FADER_ASSET_CACHE:
        if BUILDER_DEBUG: builder_logger.trace(f"📦🖼️✨ [CACHE] Retaining 3D horizontal fader cap asset from cache: {w}x{h}")
        return _HORIZONTAL_FADER_ASSET_CACHE[cache_key]

    if BUILDER_DEBUG: builder_logger.trace(f"🏗️🖼️🎨 [ASSET] Generating NEW 3D horizontal fader cap: {w}x{h} ({body_color})")
    upscale = 2 
    uw, uh = int(w * upscale), int(h * upscale)
    if uw < 1: uw = 1
    if uh < 1: uh = 1
    
    def hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 3: hex_str = "".join([c*2 for c in hex_str])
        return np.array([int(hex_str[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)

    try: b_rgb = hex_to_rgb(body_color)
    except: b_rgb = np.array([120, 120, 120], dtype=np.float32)
    
    x_coords = np.linspace(0, 1, uw, dtype=np.float32).reshape(1, uw)
    slope_x = np.zeros((1, uw), dtype=np.float32)
    slope_z = np.ones((1, uw), dtype=np.float32)

    slope_x[x_coords < 0.10] = -1.0
    slope_z[x_coords < 0.10] = 0.0
    m_02 = (x_coords >= 0.10) & (x_coords < 0.20)
    slope_x[m_02], slope_z[m_02] = -0.707, 0.707
    m_concave = (x_coords >= 0.25) & (x_coords < 0.75)
    t = (x_coords[m_concave] - 0.25) / 0.5
    slope_x[m_concave] = (t - 0.5) * 2.0 * 0.55
    slope_z[m_concave] = np.sqrt(np.maximum(0, 1.0 - slope_x[m_concave]**2))
    m_09 = (x_coords >= 0.80) & (x_coords < 0.90)
    slope_x[m_09], slope_z[m_09] = 0.707, 0.707
    slope_x[x_coords >= 0.90], slope_z[x_coords >= 0.90] = 1.0, 0.0

    light_dir = np.array([0.3, -0.6, 0.8], dtype=np.float32)
    light_dir /= np.linalg.norm(light_dir)
    ambient = 0.25
    diffuse = np.maximum(ambient, slope_x * light_dir[0] + slope_z * light_dir[2])
    h_vec = light_dir + np.array([0, 0, 1], dtype=np.float32)
    h_vec /= np.linalg.norm(h_vec)
    spec = np.power(np.maximum(0, slope_x * h_vec[0] + slope_z * h_vec[2]), 1.5) * 0.3

    colors = b_rgb.reshape(1, 1, 3) * diffuse.reshape(1, uw, 1) + (150 * spec).reshape(1, uw, 1)
    pixel_data = np.tile(np.clip(colors, 0, 255).astype(np.uint8), (uh, 1, 1))
    
    cx = uw // 2
    line_w = max(2, upscale)
    h_col = hex_to_rgb(highlight_color) if highlight_color else np.array([40, 40, 180], dtype=np.float32)
    pixel_data[:, cx - line_w//2 : cx + line_w//2, :] = h_col.astype(np.uint8)

    surface = Image.fromarray(pixel_data, mode="RGB").convert("RGBA")
    mask = Image.new("L", (uw, uh), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.rounded_rectangle((0, 0, uw, uh), radius=3*upscale, fill=255)
    # ⚡ SHALOWER SCOOPS: Using 0.08 instead of 0.15 for more vertical mass
    scoop_h = int(uh * 0.08)
    m_draw.ellipse((-uw//4, -scoop_h, 5*uw//4, scoop_h), fill=0)
    m_draw.ellipse((-uw//4, uh - scoop_h, 5*uw//4, uh + scoop_h), fill=0)

    surface_final = Image.new("RGBA", (uw, uh), (0,0,0,0))
    surface_final.paste(surface, (0,0), mask)
    surface_final = surface_final.resize((int(w), int(h)), Image.Resampling.LANCZOS)
    
    pad = 10
    canvas_img = Image.new("RGBA", (int(w) + pad*2, int(h) + pad*2), (0,0,0,0))
    shadow_layer = Image.new("RGBA", canvas_img.size, (0,0,0,0))
    ImageDraw.Draw(shadow_layer).rounded_rectangle((pad+4, pad+6, pad+int(w)+4, pad+int(h)+6), radius=4, fill=(0,0,0,110))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=3.5))
    canvas_img.paste(shadow_layer, (0,0), shadow_layer)
    canvas_img.paste(surface_final, (pad, pad), surface_final)
    
    photo = ImageTk.PhotoImage(canvas_img)
    _HORIZONTAL_FADER_ASSET_CACHE[cache_key] = photo
    return photo


class CustomHorizontalFaderFrame(tk.Canvas):
    def __init__(self, master, variable, config, path, state_mirror_engine, command):
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        super().__init__(master, bd=0, highlightthickness=0, bg=colors.get("bg", "#2b2b2b"), relief="flat")
        
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🎚️ [BUILDER] Initializing CustomHorizontalFaderFrame")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config}")

        self.variable = variable
        self.path = path
        self.config_data = config
        self.state_mirror_engine = state_mirror_engine
        self.command = command
        
        # ⚡ OPTIMIZATION: Prioritize 'min'/'max' keys from the homogenized schema
        self.min_val = float(config.get("min", config.get("value_min", 0.0)))
        self.max_val = float(config.get("max", config.get("value_max", 100.0)))
        self.log_exponent = float(config.get("log_exponent", 1.0))
        self.reff_point = float(config.get("reff_point", (self.min_val + self.max_val) / 2.0))
        if BUILDER_DEBUG: builder_logger.debug(f"📐📏🔢 [RANGE] Fader range: {self.min_val} to {self.max_val}, Log: {self.log_exponent}")

        self.is_sliding = False
        self.is_locked = False # ⚡ INTERACTION LOCK
        self.is_hovered = False
        self.track_hover_color = "#444444"
        self._resize_timer = None
        
        l_cfg = config.get("layout", {})
        self.width = float(config.get("width", l_cfg.get("width", 200)))
        self.height = float(config.get("height", l_cfg.get("height", 100)))
        
        # ⚡ HIGH-FIDELITY: Use single-canvas architecture if possible, or nested canvases for transparency
        if BUILDER_DEBUG: builder_logger.trace("🏗️🪟🎨 [CONSTRUCT] Creating main drawing canvas for horizontal fader.")
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=self.cget("bg"), width=int(self.width), height=int(self.height))
        self.canvas.pack(fill="both", expand=True)

        self.variable.trace_add("write", self._update_positions)
        
        def _schedule_render(e=None):
            if self._resize_timer: self.after_cancel(self._resize_timer)
            curr_w = self.canvas.winfo_width()
            if curr_w <= 1: return
            if BUILDER_DEBUG: builder_logger.trace(f"📐📏🔄 [LAYOUT] Fader configured. Width: {curr_w}. Debouncing render.")
            self._resize_timer = self.after(100, self.render)
            
        self.canvas.bind("<Configure>", _schedule_render)
        self.canvas.bind("<Button-1>", self._start_sliding)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._stop_sliding)
        self.canvas.bind("<Button-2>", self._jump_to_reff_point)
        self.canvas.bind("<Alt-Button-1>", self._open_manual_entry)
            
        self.canvas.bind("<Enter>", lambda e: self._update_hover_state(True))
        self.canvas.bind("<Leave>", lambda e: self._update_hover_state(False))
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

        self.temp_entry = None
        self.after(50, self.render)

    def _on_mousewheel(self, event):
        current_val = self.variable.get()
        val_range = self.max_val - self.min_val
        step = val_range * 0.05
        delta = 1 if (event.num == 4 or (hasattr(event, 'delta') and event.delta > 0)) else -1
        if sys.platform == "linux" and event.num == 5: delta = -1
        new_val = max(self.min_val, min(self.max_val, current_val + (delta * step)))
        self.is_sliding = True
        self.variable.set(new_val)
        if self.state_mirror_engine: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)
        self.after(500, lambda: setattr(self, 'is_sliding', False) or self._update_positions())

    def _update_hover_state(self, hovering):
        self.is_hovered = hovering
        if self.canvas.find_withtag("track_slot"):
            col = self.track_hover_color if hovering else "#050505"
            self.canvas.itemconfig("track_slot", fill=col)

    def _update_positions(self, *args):
        if not self.winfo_exists() or not self.canvas.winfo_exists(): return
        try: val = self.variable.get()
        except: return
        w, h = float(self.canvas.winfo_width()), float(self.canvas.winfo_height())
        if w <= 1: w, h = self.width, self.height
        scale = float(self.config_data.get("fader_cap_scale", 1.0))
        cap_w = int(float(self.config_data.get("cap_width", 50)) * scale)
        px = cap_w / 2.0 + 10.0
        usable_w = w - (px * 2.0)
        norm = (val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
        disp_norm = max(0.0, min(1.0, norm)) ** (1.0 / self.log_exponent)
        hx = usable_w * disp_norm + px
        self.canvas.coords("fader_cap", hx, h / 2.0)
        self.canvas.coords("fill_line", px, h / 2.0, hx, h / 2.0)
        if self.is_sliding:
            txt = f"{val:.1f}" if val != int(val) else f"{int(val)}"
            self.canvas.itemconfig("floating_val", text=txt, state="normal")
            self.canvas.coords("floating_val", hx, h / 2.0 - 25.0)
        else: self.canvas.itemconfig("floating_val", state="hidden")

    def render(self):
        self._resize_timer = None
        if not self.winfo_exists(): return
        w, h = float(self.canvas.winfo_width()), float(self.canvas.winfo_height())
        if w <= 1: w, h = self.width, self.height
        
        # ⚡ INDUSTRIAL TRANSPARENCY: Don't delete everything, preserve the patina slice
        for item in self.canvas.find_all():
            tags = self.canvas.gettags(item)
            if "panel_bg_slice" not in tags:
                self.canvas.delete(item)
        
        # 0. Draw Industrial Background (Fallback if slice doesn't exist)
        if hasattr(self.canvas, 'panel_bg_image') and not self.canvas.find_withtag("panel_bg_slice"):
            self.canvas.create_image(0, 0, image=self.canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")
        
        cy = h / 2.0
        label_text = self.config_data.get("label_active", "")
        if label_text: 
            f_size = int(float(self.config_data.get("layout", {}).get("font", 9)))
            # ⚡ TIGHT TITLE: Position relative to cy instead of hardcoded 12
            # cy - 22 puts it just above the 3D cap
            self.canvas.create_text(w/2.0, cy - 22, text=label_text, fill="white", font=("Helvetica", f_size, "bold"), anchor="s", tags="static")
        scale = float(self.config_data.get("fader_cap_scale", 1.0))
        cap_w = int(float(self.config_data.get("cap_width", 50)) * scale)
        cap_h = int(float(self.config_data.get("cap_height", 55)) * scale)
        px = cap_w / 2.0 + 10.0
        self.canvas.create_rectangle(px - 5, cy - 4, w - px + 5, cy + 4, fill="#050505", outline="#222", width=1, tags=("static", "track_slot"))
        self.canvas.create_line(px, cy, w - px, cy, fill="#222", width=2, tags="static")
        accent = THEMES.get(DEFAULT_THEME, THEMES["dark"]).get("accent", "#f4902c")
        val_h_col = self.config_data.get("value_highlight_color", accent)
        self.canvas.create_line(px, cy, px, cy, fill=val_h_col, width=2, tags="fill_line")
        
        val_range = self.max_val - self.min_val
        tick_values = []
        
        # ⚡ SMART TICK LOGIC: Prioritize config, fallback to auto
        ti = self.config_data.get("tick_interval")
        if ti is not None:
            ti = float(ti)
        else:
            target_ticks = 10
            if val_range > 0:
                raw_interval = val_range / target_ticks
                exponent = math.floor(math.log10(raw_interval))
                fraction = raw_interval / (10**exponent)
                if fraction < 1.5: snapped = 1
                elif fraction < 3.5: snapped = 2
                elif fraction < 7.5: snapped = 5
                else: snapped = 10
                ti = snapped * (10**exponent)
            else:
                ti = 10

        if ti > 0:
            curr = math.ceil(self.min_val / ti) * ti
            while curr <= self.max_val: 
                tick_values.append(curr)
                curr += ti
        
        # --- ⚡ SMART SCALE LOGIC (From ScaleDrawer) ---
        num_ticks = len(tick_values)
        label_every = 1
        if num_ticks > 20: label_every = 2
        if num_ticks > 50: label_every = 5
        if num_ticks > 100: label_every = 10
        if num_ticks > 250: label_every = 20
        if num_ticks > 500: label_every = 50
        if num_ticks > 1000: label_every = 200
        if num_ticks > 5000: label_every = 500

        draw_every = 1
        if label_every >= 500: draw_every = 100
        elif label_every >= 200: draw_every = 50
        elif label_every >= 50: draw_every = 10
        elif label_every >= 20: draw_every = 5
        elif label_every >= 10: draw_every = 2
        elif label_every >= 5: draw_every = 1

        usable_w = w - (px * 2.0)
        # 🎨 ACCENT: Use light grey by default for better visibility
        t_col = self.config_data.get("tick_color", "light grey")
        sub_t_col = self.config_data.get("sub_tick_color", "#555555")
        
        for i, tv in enumerate(tick_values):
            norm = (tv - self.min_val) / val_range if val_range else 0
            disp_norm = max(0.0, min(1.0, norm)) ** (1.0 / self.log_exponent)
            tx = usable_w * disp_norm + px
            
            is_main_tick = (i % label_every == 0)
            is_drawn = (i % draw_every == 0)
            
            # --- ⚡ TIGHT LAYOUT: Ticks closer to the track ---
            if is_drawn:
                # Ticks now live between +8 and +14 from center
                self.canvas.create_line(tx, cy + 8, tx, cy + 14, fill=t_col if is_main_tick else sub_t_col, tags="static")
            
            # ⚡ ALWAYS DRAW LABELS FOR MAIN TICKS
            if is_main_tick:
                if tv == int(tv):
                    lbl = str(int(tv))
                else:
                    lbl = f"{tv:.1f}"
                # Labels now live at +20 from center (down from +35)
                self.canvas.create_text(tx, cy + 20, text=lbl, fill=t_col, font=("Helvetica", 7), anchor="n", tags="static")
        self.cap_img = get_3d_horizontal_fader_cap(cap_w, cap_h, self.config_data.get("cap_color", "#dcdcdc"), "#111", highlight_color=self.config_data.get("cap_highlight_color"))
        self.canvas.create_image(px, cy, image=self.cap_img, tags="fader_cap")
        self.canvas.cap_img = self.cap_img
        self.canvas.create_text(px, cy - 25, text="", fill="white", font=("Helvetica", 7, "bold"), tags="floating_val", state="hidden")
        self._update_positions()

    def _start_sliding(self, event):
        self.is_sliding = True
        self.is_locked = True # ⚡ LOCK: Human has touched the fader. Block network updates.
        self._on_drag(event)

    def _on_drag(self, event):
        ex = float(event.x)
        w = float(self.canvas.winfo_width())
        if w <= 1: w = self.width
        scale = float(self.config_data.get("fader_cap_scale", 1.0))
        cap_w = int(float(self.config_data.get("cap_width", 50)) * scale)
        px = cap_w / 2.0 + 10.0
        if w <= (px * 2.0): return
        norm = max(0.0, min(1.0, (ex - px) / (w - (px * 2.0))))
        val = self.min_val + (norm ** self.log_exponent) * (self.max_val - self.min_val)
        self.variable.set(val)
        if self.path and self.state_mirror_engine: 
            self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _stop_sliding(self, event):
        # ⚡ RELEASE: Human has let go.
        # 1. Fire one final broadcast to ensure software has the absolute latest value.
        if self.path and self.state_mirror_engine:
            self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)
            
        self.is_sliding = False
        self.is_locked = False # ⚡ UNLOCK: Widget is now permitted to listen to the network again.
        self._update_positions()

    def _jump_to_reff_point(self, event):
        self.variable.set(self.reff_point)
        if self.state_mirror_engine: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _open_manual_entry(self, event):
        if self.temp_entry: return
        self.temp_entry = tk.Entry(self, width=8, justify="center")
        self.temp_entry.place(x=event.x, y=event.y)
        self.temp_entry.insert(0, str(self.variable.get()))
        self.temp_entry.focus_set()
        self.temp_entry.bind("<Return>", lambda e: self._submit_manual_entry())
        self.temp_entry.bind("<FocusOut>", lambda e: self._destroy_manual_entry())

    def _submit_manual_entry(self):
        try:
            val = float(self.temp_entry.get())
            self.variable.set(max(self.min_val, min(self.max_val, val)))
            if self.state_mirror_engine: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)
        except: pass
        self._destroy_manual_entry()

    def _destroy_manual_entry(self):
        if self.temp_entry: self.temp_entry.destroy(); self.temp_entry = None


class BuilderFaderHorizontalCreator(TransparencyMixin):
    def make_fader_horizontal(self, parent_widget, config_data, context=None, **kwargs):
        """Creates a horizontal fader widget."""
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🎚️ [BUILDER] Entering make_fader_horizontal")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {orjson.dumps(config_data, default=str).decode()}")
        path = config_data.get("path")
        
        # ⚡ HARDENED INTERFACE: Extract from context if available
        if BUILDER_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
            if BUILDER_DEBUG: builder_logger.debug("✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.")
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self
            if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to self/kwargs.")

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️🎚️ [BUILDER] Spawning horizontal fader for '{config_data.get('label_active')}' at path '{path}'.")

        val_default = float(config_data.get("value_default", config_data.get("value", 50.0)))
        val_var = tk.DoubleVar(value=val_default)
        if BUILDER_DEBUG: builder_logger.debug(f"🔋🎚️✨ [STATE] Initial value: {val_default}")
        
        frame = CustomHorizontalFaderFrame(parent_widget, val_var, config_data, path, state_mirror_engine, None)
        
        # ⚡ USE CENTRALIZED TRANSPARENCY ENGINE
        if hasattr(builder_instance, '_apply_transparency'):
            if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to horizontal fader.")
            TransparencyManager.apply_transparency(frame, frame.canvas, config_data, builder_instance)
            TransparencyManager.apply_transparency(frame, frame, config_data, builder_instance)
        
        if path and state_mirror_engine:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering horizontal fader at path '{path}'")
            # ⚡ LOCK REGISTRATION: Pass 'frame' as instance for sync_incoming_mqtt_to_gui checking
            topic = state_mirror_engine.register_widget(path, val_var, base_mqtt_topic_from_path, config_data, instance=frame)
            if subscriber_router and topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing to topic: {topic}")
                subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
            
            if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing state from cache/broker for '{path}'")
            state_mirror_engine.initialize_widget_state(path)

        if BUILDER_DEBUG: builder_logger.success(f"✅🆗🎚️ [SUCCESS] The horizontal fader '{config_data.get('label_active')}' has materialized!")
        return frame
