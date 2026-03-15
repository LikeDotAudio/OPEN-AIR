# fader_dual/dynamic_guimake_fader_dual.py
#
# A high-performance, photorealistic dual fader widget.
# Refactored for zero-flicker tagged updates and debounced resizing.
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
from managers.Display.factory.widget_registry import WidgetRegistry

_DUAL_FADER_ASSET_CACHE = {}

def get_3d_dual_fader_cap(w, h, body_color, outline_color, is_vertical=True):
    cache_key = (w, h, body_color, outline_color, is_vertical, "next_gen_dual_v5_vectorized")
    if cache_key in _DUAL_FADER_ASSET_CACHE: 
        if BUILDER_DEBUG: builder_logger.trace(f"📦🖼️✨ [CACHE] Retaining 3D dual fader cap from cache: {w}x{h} (Vert: {is_vertical})")
        return _DUAL_FADER_ASSET_CACHE[cache_key]
    
    if BUILDER_DEBUG: builder_logger.trace(f"🏗️🖼️🎨 [ASSET] Generating NEW 3D dual fader cap: {w}x{h} ({body_color})")
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
    base_rgb = 0.7 * np.array([30, 30, 30], dtype=np.float32) + 0.3 * b_rgb
    light_dir = np.array([0.3, -0.6, 0.8], dtype=np.float32)
    light_dir /= np.linalg.norm(light_dir)
    trans_len = uw if is_vertical else uh
    prof_len = uh if is_vertical else uw
    nx = np.linspace(0, 1, prof_len, endpoint=False)
    slope_long = np.zeros(prof_len, dtype=np.float32)
    slope_z = np.zeros(prof_len, dtype=np.float32)
    m1 = nx < 0.10; slope_long[m1], slope_z[m1] = -1.0, 0.0
    m2 = (nx >= 0.10) & (nx < 0.20); slope_long[m2], slope_z[m2] = -0.707, 0.707
    m3 = (nx >= 0.20) & (nx < 0.25); slope_long[m3], slope_z[m3] = 0.0, 1.0
    m4 = (nx >= 0.25) & (nx < 0.75)
    t = (nx[m4] - 0.25) / 0.5
    slope_long[m4] = (t - 0.5) * 2.0 * 0.55
    slope_z[m4] = np.sqrt(np.maximum(0, 1.0 - slope_long[m4]**2))
    m5 = (nx >= 0.75) & (nx < 0.80); slope_long[m5], slope_z[m5] = 0.0, 1.0
    m6 = (nx >= 0.80) & (nx < 0.90); slope_long[m6], slope_z[m6] = 0.707, 0.707
    m7 = (nx >= 0.90); slope_long[m7], slope_z[m7] = 1.0, 0.0
    ao = np.ones(prof_len, dtype=np.float32)
    dist = 1.0 - (np.abs(nx - 0.5) / 0.25)
    ao[m4] = 1.0 - (np.maximum(0, dist[m4]) * 0.4)
    groove_val = np.zeros(prof_len, dtype=np.float32)
    m_gr = (nx > 0.22) & (nx < 0.78); tg = (nx[m_gr] - 0.22) / 0.56
    groove_val[m_gr] = np.sin(tg * np.pi * 14 - np.pi/2) * 0.12
    diff = np.maximum(0.25, slope_long * light_dir[1] + slope_z * light_dir[2])
    h_vec = light_dir + np.array([0, 0, 1], dtype=np.float32); h_vec /= np.linalg.norm(h_vec)
    spec = (np.maximum(0, slope_long * h_vec[1] + slope_z * h_vec[2]) ** 2.8) * 0.8
    top_split = int(trans_len * 0.85)
    rgb_final = np.zeros((uh, uw, 3), dtype=np.float32)
    c_diff = diff + groove_val; c_ao = ao * (1.0 + groove_val * 0.66)
    for p in range(prof_len):
        p_d, p_a, p_s, p_sz = c_diff[p], c_ao[p], spec[p], slope_z[p]
        if is_vertical: row = rgb_final[p, :, :]
        else: row = rgb_final[:, p, :]
        row[:top_split, 0] = base_rgb[0] * p_d * p_a + 255 * p_s
        row[:top_split, 1] = base_rgb[1] * p_d * p_a + 255 * p_s
        row[:top_split, 2] = base_rgb[2] * p_d * p_a + 255 * p_s
        side_d = np.maximum(0.35, 0.8 * light_dir[0] + 0.2 * p_sz * light_dir[2])
        row[top_split:, 0] = base_rgb[0] * side_d * (p_a * 0.9)
        row[top_split:, 1] = base_rgb[1] * side_d * (p_a * 0.9)
        row[top_split:, 2] = base_rgb[2] * side_d * (p_a * 0.9)
    cp = prof_len // 2; line_w = max(2, 3 * upscale)
    is_line = (np.arange(prof_len) >= (cp - line_w//2)) & (np.arange(prof_len) <= (cp + line_w//2))
    if is_vertical: rgb_final[is_line, :, :] = np.minimum(255, 255 * (c_diff[is_line][:, np.newaxis, np.newaxis] * 0.8 + 0.4))
    else: rgb_final[:, is_line, :] = np.minimum(255, 255 * (c_diff[is_line][np.newaxis, :, np.newaxis] * 0.8 + 0.4))
    rgb_u8 = np.clip(rgb_final, 0, 255).astype(np.uint8)
    surface = Image.fromarray(rgb_u8, 'RGB').convert("RGBA")
    mask = Image.new("L", (uw, uh), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, uw, uh), radius=3*upscale, fill=255)
    final_body = Image.new("RGBA", (uw, uh), (0,0,0,0)); final_body.paste(surface, (0,0), mask)
    final_body = final_body.resize((int(w), int(h)), Image.Resampling.LANCZOS)
    pad = 8; canvas_img = Image.new("RGBA", (int(w) + pad*2, int(h) + pad*2), (0,0,0,0))
    ImageDraw.Draw(canvas_img).rounded_rectangle((pad+2, pad+4, pad+int(w)+2, pad+int(h)+4), radius=4, fill=(0,0,0,140))
    canvas_img = canvas_img.filter(ImageFilter.GaussianBlur(radius=4))
    canvas_img.paste(final_body, (pad, pad), final_body)
    photo = ImageTk.PhotoImage(canvas_img); _DUAL_FADER_ASSET_CACHE[cache_key] = photo
    return photo


class CustomDualFaderFrame(tk.Frame):
    def __init__(self, master, config, path, state_mirror_engine, base_mqtt_topic, subscriber_router, orientation="horizontal"):
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        super().__init__(master, bd=0, highlightthickness=0, bg=colors.get("bg", "#2b2b2b"))
        
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🎚️ [BUILDER] Initializing CustomDualFaderFrame ({orientation})")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config}")

        self.orientation = str(orientation).lower()
        self.min_val = float(config.get("value_min", 0.0))
        self.max_val = float(config.get("value_max", 100.0))
        self.log_exponent = float(config.get("log_exponent", 1.0))
        self.reff_point = float(config.get("reff_point", (self.min_val + self.max_val) / 2.0))
        self.label_active = config.get("label_active", "")
        self.value_highlight_color = colors.get("accent", "#f4902c")
        if BUILDER_DEBUG: builder_logger.debug(f"📐📏🔢 [RANGE] Fader range: {self.min_val} to {self.max_val}, Log: {self.log_exponent}")

        self.cap_width = int(float(config.get("cap_width", 30)))
        self.cap_height_ratio = float(config.get("cap_height_ratio", 0.6))
        self.cap_color = config.get("cap_color", colors.get("fg", "#dcdcdc"))
        self.path = path; self.state_mirror_engine = state_mirror_engine; self.config_data = config
        
        self.v1_var = tk.DoubleVar(value=float(config.get("value_default_v1", 50)))
        self.v2_var = tk.DoubleVar(value=float(config.get("value_default_v2", 50)))
        self.delta_var = tk.DoubleVar(value=0.0)
        if BUILDER_DEBUG: builder_logger.debug(f"🔋🎚️✨ [STATE] Initial values: V1={self.v1_var.get()}, V2={self.v2_var.get()}")

        l_cfg = config.get("layout", {})
        self.width = float(config.get("width", l_cfg.get("width", 100 if orientation == "vertical" else 250)))
        self.height = float(config.get("height", l_cfg.get("height", 250 if orientation == "vertical" else 100)))
        
        if BUILDER_DEBUG: builder_logger.trace("🏗️🪟🎨 [CONSTRUCT] Creating dual fader canvas.")
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=self.cget("bg"), width=int(self.width), height=int(self.height))
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.v1_var.trace_add("write", self._update_positions)
        self.v2_var.trace_add("write", self._update_positions)
        self._resize_timer = None
        self.canvas.bind("<Configure>", self._on_configure)
        self.active_fader = None; self.after(50, self.render)

    def _on_configure(self, event):
        if self._resize_timer: self.after_cancel(self._resize_timer)
        if self.canvas.winfo_width() <= 1: return
        if BUILDER_DEBUG: builder_logger.trace(f"📐📏🔄 [LAYOUT] Dual fader configured for '{self.label_active}'. Width: {event.width}. Debouncing.")
        self._resize_timer = self.after(100, self.render)

    def _update_positions(self, *args):
        if not self.winfo_exists() or not self.canvas.winfo_exists(): return
        try: 
            v1, v2 = self.v1_var.get(), self.v2_var.get()
            self.delta_var.set(v2 - v1)
            if BUILDER_DEBUG: builder_logger.trace(f"🔄✨🎚️ [SYNC] Updating dual fader '{self.label_active}' positions: V1={v1:.1f}, V2={v2:.1f}")
        except: return
        w, h = float(self.canvas.winfo_width()), float(self.canvas.winfo_height())
        if w <= 1: w, h = self.width, self.height
        is_vert = self.orientation == "vertical"; dim = h if is_vert else w
        def get_p(val):
            n = (val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
            dn = max(0.0, min(1.0, n)) ** (1.0 / self.log_exponent)
            return (dim - 40.0) * (1.0 - dn if is_vert else dn) + 20.0
        p1, p2 = get_p(v1), get_p(v2); cx, cy = w/2.0, h/2.0
        if is_vert:
            self.canvas.coords("delta_line", cx, p1, cx, p2)
            self.canvas.coords("cap1", cx, p1); self.canvas.coords("cap2", cx, p2)
            self.canvas.coords("v1_text", cx - 25, p1); self.canvas.coords("v2_text", cx + 25, p2)
        else:
            self.canvas.coords("delta_line", p1, cy, p2, cy)
            self.canvas.coords("cap1", p1, cy); self.canvas.coords("cap2", p2, cy)
            self.canvas.coords("v1_text", p1, cy - 25); self.canvas.coords("v2_text", p2, cy + 25)
        self.canvas.itemconfig("v1_text", text=f"{v1:.1f}"); self.canvas.itemconfig("v2_text", text=f"{v2:.1f}")
        self.canvas.itemconfig("delta_label", text=f"\u0394: {v2-v1:.2f}")

    def render(self):
        self._resize_timer = None
        if not self.winfo_exists(): return
        w, h = float(self.canvas.winfo_width()), float(self.canvas.winfo_height())
        if w <= 1: w, h = self.width, self.height
        
        if BUILDER_DEBUG: builder_logger.trace(f"🔄✨🎨 [REDRAW] Executing full render for dual fader '{self.label_active}' ({w}x{h})")
        # ⚡ INDUSTRIAL TRANSPARENCY: Don't delete everything, preserve the patina slice
        for item in self.canvas.find_all():
            tags = self.canvas.gettags(item)
            if "panel_bg_slice" not in tags:
                self.canvas.delete(item)
        
        # 0. Draw Industrial Background (Fallback if slice doesn't exist)
        if hasattr(self.canvas, 'panel_bg_image') and not self.canvas.find_withtag("panel_bg_slice"):
            self.canvas.create_image(0, 0, image=self.canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")
        is_vert = self.orientation == "vertical"; cx, cy = w/2.0, h/2.0
        if self.label_active: self.canvas.create_text(w/2.0, 10, text=self.label_active, fill="white", font=("Helvetica", 9, "bold"), tags="static")
        if is_vert: self.canvas.create_rectangle(cx-5, 15, cx+5, h-15, fill="#0a0a0a", outline="#333", tags="static")
        else: self.canvas.create_rectangle(15, cy-5, w-15, cy+5, fill="#0a0a0a", outline="#333", tags="static")
        self.canvas.create_line(0, 0, 0, 0, fill=self.value_highlight_color, width=4, capstyle=tk.ROUND, tags="delta_line")
        cw = self.cap_width; ch = int((h if not is_vert else w) * self.cap_height_ratio)
        self.img1 = get_3d_dual_fader_cap(ch if is_vert else cw, cw if is_vert else ch, self.cap_color, "#444", is_vert)
        self.img2 = get_3d_dual_fader_cap(ch if is_vert else cw, cw if is_vert else ch, self.cap_color, "#444", is_vert)
        self.canvas.create_image(0, 0, image=self.img1, tags="cap1"); self.canvas.create_image(0, 0, image=self.img2, tags="cap2")
        self.canvas.create_text(0, 0, text="", fill="white", font=("Helvetica", 7), tags="v1_text")
        self.canvas.create_text(0, 0, text="", fill="white", font=("Helvetica", 7), tags="v2_text")
        self.canvas.create_text(w-5, h-5, text="", fill="white", font=("Helvetica", 8, "bold"), anchor="se", tags="delta_label")
        self._update_positions()

    def _get_handle_under_mouse(self, x, y):
        w, h = float(self.canvas.winfo_width()), float(self.canvas.winfo_height())
        if w <= 1: w, h = self.width, self.height
        is_vert = self.orientation == "vertical"
        def get_dist(val):
            n = (val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
            dn = n ** (1.0 / self.log_exponent); pos = (h if is_vert else w - 40.0) * (1.0 - dn if is_vert else dn) + 20.0
            return abs(y - pos) if is_vert else abs(x - pos)
        d1, d2 = get_dist(self.v1_var.get()), get_dist(self.v2_var.get())
        if d1 < 20 and d1 < d2: return "V1"
        if d2 < 20: return "V2"
        return None

@WidgetRegistry.register("_CustomDualHorizontalFader", "_CustomDualVerticalFader")
class BuilderFaderDualCreator(TransparencyMixin):
    
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """
        Static factory method for creating a dual fader widget.
        """
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🎚️ [BUILDER] Entering BuilderFaderDualCreator.make")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {orjson.dumps(config_data, default=str).decode()}")
        path = config_data.get("path")
        
        # ⚡ HARDENED INTERFACE: Extract from context if available
        if BUILDER_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            app_instance = context.app_instance
            builder_instance = context.builder_instance or app_instance
            if BUILDER_DEBUG: builder_logger.debug("✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.")
        else:
            state_mirror_engine = kwargs.get("state_mirror_engine")
            subscriber_router = kwargs.get("subscriber_router")
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance")
            app_instance = kwargs.get("app_instance")
            if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to kwargs.")

        orientation = "vertical" if "_CustomDualVerticalFader" in config_data.get("type", "") else "horizontal"
        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️🎚️ [BUILDER] Spawning dual fader for '{config_data.get('label_active')}' at path '{path}'.")
        
        frame = CustomDualFaderFrame(parent_widget, config_data, path, state_mirror_engine, base_mqtt_topic_from_path, subscriber_router, orientation)
        
        # ⚡ USE CENTRALIZED TRANSPARENCY ENGINE
        if hasattr(builder_instance, '_apply_transparency'):
            if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to dual fader.")
            TransparencyManager.apply_transparency(frame, frame.canvas, config_data, builder_instance)
        
        # ⚡ MQTT Registration and Initialization
        if path and state_mirror_engine:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering dual-variable state for path '{path}'")
            # Register V1
            v1_path = f"{path}/V1"
            v1_topic = state_mirror_engine.register_widget(v1_path, frame.v1_var, base_mqtt_topic_from_path, config_data)
            if subscriber_router and v1_topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing V1 to topic: {v1_topic}")
                subscriber_router.subscribe_to_topic(v1_topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
            state_mirror_engine.initialize_widget_state(v1_path)
            
            # Register V2
            v2_path = f"{path}/V2"
            v2_topic = state_mirror_engine.register_widget(v2_path, frame.v2_var, base_mqtt_topic_from_path, config_data)
            if subscriber_router and v2_topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing V2 to topic: {v2_topic}")
                subscriber_router.subscribe_to_topic(v2_topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
            state_mirror_engine.initialize_widget_state(v2_path)

        def on_press(event): 
            frame.active_fader = frame._get_handle_under_mouse(event.x, event.y)
            if BUILDER_DEBUG and frame.active_fader: builder_logger.info(f"🖱️👆🎚️ [INPUT] Active handle selected: {frame.active_fader}")
            on_drag(event)
            
        def on_drag(event):
            if not frame.active_fader: return
            w, h = float(frame.canvas.winfo_width()), float(frame.canvas.winfo_height())
            if w <= 1: w, h = frame.width, frame.height
            is_v = frame.orientation == "vertical"
            norm = (event.y - 20.0) / (h - 40.0) if is_v else (event.x - 20.0) / (w - 40.0)
            if is_v: norm = 1.0 - norm
            val = frame.min_val + (max(0, min(1, norm)) ** frame.log_exponent) * (frame.max_val - frame.min_val)
            
            (frame.v1_var if frame.active_fader == "V1" else frame.v2_var).set(val)
            if state_mirror_engine:
                if BUILDER_DEBUG: builder_logger.trace(f"📡🔴📡 [MQTT] Broadcasting change for member: {path}/{frame.active_fader}")
                state_mirror_engine.broadcast_gui_change_to_mqtt(f"{path}/{frame.active_fader}")
        
        if BUILDER_DEBUG: builder_logger.trace("🖱️👆🔗 [EVENTS] Binding input protocols for dual fader.")
        frame.canvas.bind("<Button-1>", on_press)
        frame.canvas.bind("<B1-Motion>", on_drag)
        frame.canvas.bind("<ButtonRelease-1>", lambda e: setattr(frame, 'active_fader', None))
        return frame

    def make_fader_dual(self, parent_widget, config_data, context=None, **kwargs):
        # Backward compatibility for mixin usage
        return BuilderFaderDualCreator.make(parent_widget, config_data, context, builder_instance=self, **kwargs)
