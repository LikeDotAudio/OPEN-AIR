# fader_bar_graph/Fader_with_Bar_Graph.py
import tkinter as tk
from tkinter import ttk
import math
import sys
import random
import os
import numpy as np
from PIL import Image, ImageDraw, ImageTk, ImageFilter, ImageChops

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from workers.styling.style import THEMES, DEFAULT_THEME
from workers.Command_Router.mqtt.mqtt_topic_utils import get_topic
from workers.handlers.widget_event_binder import bind_variable_trace

# Inherit from mixins to keep the class hierarchy happy in DynamicGuiBuilder
from workers.builder.fader.fader import BuilderFaderCreator
from workers.builder.meter_bar.meter_bar import BuilderMeterBarCreator
from managers.Display.transparency.transparency_mixin import TransparencyMixin
from managers.Display.factory.widget_registry import WidgetRegistry

# --- Module Level Cache for 3D Assets ---
_FADER_BAR_ASSET_CACHE = {}

def get_3d_fader_bar_cap_asset(w, h, body_color, outline_color):
    """
    Generates a photorealistic wide 'Next Gen' Concave Saddle fader cap with 3D perspective.
    OPTIMIZED: Uses NumPy vectorization with 1D profiles to avoid indexing errors.
    """
    cache_key = (w, h, body_color, outline_color, "next_gen_fader_bar_v7_vectorized")
    if cache_key in _FADER_BAR_ASSET_CACHE:
        if BUILDER_DEBUG: builder_logger.trace(f"📦🖼️✨ [CACHE] Retaining 3D fader cap asset from cache: {w}x{h}")
        return _FADER_BAR_ASSET_CACHE[cache_key]

    if BUILDER_DEBUG: builder_logger.trace(f"🏗️🖼️🎨 [ASSET] Generating NEW 3D fader cap asset: {w}x{h} ({body_color})")
    upscale = 2 
    uw, uh = w * upscale, h * upscale
    
    def hex_to_rgb(hex_str):
        hex_str = hex_str.lstrip('#')
        return np.array([int(hex_str[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32)

    try: b_rgb = hex_to_rgb(body_color)
    except: b_rgb = np.array([40, 40, 40], dtype=np.float32)
    
    # 1. Dark Base Blending
    base_rgb = 0.7 * np.array([30, 30, 30], dtype=np.float32) + 0.3 * b_rgb
    light_dir = np.array([0.3, -0.6, 0.8], dtype=np.float32)
    light_dir /= np.linalg.norm(light_dir)
    
    roughness = 0.35
    spec_power = 1.0 / roughness
    ambient = 0.25
    
    # 2. Vectorized Math (1D Profiles for uh)
    ny = np.linspace(0, 1, uh, dtype=np.float32)
    
    # Normal Map Generation
    slope_y = np.zeros(uh, dtype=np.float32)
    slope_z = np.zeros(uh, dtype=np.float32)
    
    # Profile Logic (1D masks)
    m1 = ny < 0.10; slope_y[m1], slope_z[m1] = -1.0, 0.0
    m2 = (ny >= 0.10) & (ny < 0.20); slope_y[m2], slope_z[m2] = -0.707, 0.707
    m3 = (ny >= 0.20) & (ny < 0.25); slope_y[m3], slope_z[m3] = 0.0, 1.0
    
    m4 = (ny >= 0.25) & (ny < 0.75)
    t = (ny[m4] - 0.25) / 0.5
    local_t = (t - 0.5) * 2.0
    sy = local_t * 0.55
    slope_y[m4] = sy
    slope_z[m4] = np.sqrt(np.maximum(0, 1.0 - slope_y[m4]**2))
    
    m5 = (ny >= 0.75) & (ny < 0.80); slope_y[m5], slope_z[m5] = 0.0, 1.0
    m6 = (ny >= 0.80) & (ny < 0.90); slope_y[m6], slope_z[m6] = 0.707, 0.707
    m7 = (ny >= 0.90); slope_y[m7], slope_z[m7] = 1.0, 0.0

    # Ambient Occlusion Profile
    ao = np.ones(uh, dtype=np.float32)
    dist = 1.0 - (np.abs(ny - 0.5) / 0.25)
    ao[m4] = 1.0 - (np.maximum(0, dist[m4]) * 0.4)

    # Grooves Profile
    groove_val = np.zeros(uh, dtype=np.float32)
    m_groove = (ny > 0.22) & (ny < 0.78)
    tg = (ny[m_groove] - 0.22) / 0.56
    gv = np.sin(tg * np.pi * 14 - np.pi/2) * 0.12
    groove_val[m_groove] = gv
    
    # Shading Profiles
    diff = np.maximum(ambient, slope_y * light_dir[1] + slope_z * light_dir[2])
    h_vec = light_dir + np.array([0, 0, 1], dtype=np.float32)
    h_vec /= np.linalg.norm(h_vec)
    spec_dot = np.maximum(0, slope_y * h_vec[1] + slope_z * h_vec[2])
    spec = (spec_dot ** spec_power) * 0.8

    # Expand profiles to 2D (uh, 1) for column broadcasting
    diff_2d = diff[:, np.newaxis]
    ao_2d = ao[:, np.newaxis]
    spec_2d = spec[:, np.newaxis]
    groove_2d = groove_val[:, np.newaxis]
    slope_z_2d = slope_z[:, np.newaxis]

    # Final RGB Assembly
    top_split_x = int(uw * 0.92)
    rgb_final = np.zeros((uh, uw, 3), dtype=np.float32)
    
    # Shading top
    curr_diff = diff_2d + groove_2d
    curr_ao = ao_2d * (1.0 + groove_2d * 0.66)
    
    # Top face pixels (Broadcast across width)
    top_shading = base_rgb * curr_diff * curr_ao + 255 * spec_2d
    rgb_final[:, :top_split_x, :] = top_shading[:, np.newaxis, :]
    
    # Side face pixels (Broadcast across width)
    side_diff = np.maximum(ambient + 0.1, 0.8 * light_dir[0] + 0.2 * slope_z_2d * light_dir[2])
    side_shading = base_rgb * side_diff * (ao_2d * 0.9)
    rgb_final[:, top_split_x:, :] = side_shading[:, np.newaxis, :]

    # Indicator Line Mask
    line_h = max(2, 3 * upscale)
    cy = uh // 2
    is_line = (np.arange(uh) >= (cy - line_h//2)) & (np.arange(uh) <= (cy + line_h//2))
    rgb_final[is_line, :, :] = np.minimum(255, 255 * (curr_diff[is_line, :, np.newaxis] * 0.8 + 0.4))

    # Clamp and convert
    rgb_uint8 = np.clip(rgb_final, 0, 255).astype(np.uint8)
    surface = Image.fromarray(rgb_uint8, 'RGB').convert("RGBA")
    
    # 3. Final Assembly
    mask = Image.new("L", (uw, uh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, uw, uh), radius=3*upscale, fill=255)
    
    final_body = Image.new("RGBA", (uw, uh), (0,0,0,0))
    final_body.paste(surface, (0,0), mask)
    final_body = final_body.resize((w, h), Image.Resampling.LANCZOS)
    
    # Shadow Canvas
    pad = 8
    canvas_img = Image.new("RGBA", (w + pad*2, h + pad*2), (0,0,0,0))
    ImageDraw.Draw(canvas_img).rounded_rectangle((pad+2, pad+4, pad+w+2, pad+h+4), radius=4, fill=(0,0,0,140))
    canvas_img = canvas_img.filter(ImageFilter.GaussianBlur(radius=4))
    canvas_img.paste(final_body, (pad, pad), final_body)
    
    photo = ImageTk.PhotoImage(canvas_img)
    _FADER_BAR_ASSET_CACHE[cache_key] = photo
    return photo


class FaderWithBarGraphFrame(tk.Frame, TransparencyMixin):
    def __init__(self, master, config, path, state_mirror_engine, subscriber_router, base_mqtt_topic, builder_instance=None):
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        super().__init__(master, bd=0, highlightthickness=0)
        
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🎚️ [BUILDER] Initializing FaderWithBarGraphFrame")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config}")

        self.widget_config = config
        self.path = path
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = subscriber_router
        self.base_mqtt_topic = base_mqtt_topic
        self.instance = builder_instance
        
        # --- Configuration ---
        self.min_val = float(config.get("value_min", -100.0))
        self.max_val = float(config.get("value_max", 0.0))
        self.log_exponent = float(config.get("log_exponent", 1.0))
        self.bar_padding = int(config.get("bar_padding", 0))
        self.meter_width = int(config.get("meter_width", 15))
        self.enable_meters = config.get("bar_enable", config.get("bea_enable", True))
        self.cap_height = int(config.get("cap_height", 40))
        self.show_ticks = config.get("show_ticks", True)
        self.tick_steps = int(config.get("tick_steps", 10))
        if BUILDER_DEBUG: builder_logger.debug(f"📐📏🔢 [RANGE] Fader range: {self.min_val} to {self.max_val}, Meters: {self.enable_meters}")
        
        # Layout Width/Height
        layout = config.get("layout", {})
        self.width = int(layout.get("width", 100))
        self.height = int(layout.get("height", 300))
        
        # Styles & Colors
        self.left_style = config.get("left_meter_style", {})
        self.right_style = config.get("right_meter_style", {})
        self.fader_track_color = config.get("fader_track_color", colors.get("secondary", "#444444"))
        self.fader_grip_color = config.get("cap_colour", config.get("fader_grip_color", colors.get("fg", "#dcdcdc")))
        
        # Variables
        self.fader_var = tk.DoubleVar(value=float(config.get("value_default", self.min_val)))
        self.left_var = tk.DoubleVar(value=self.min_val)
        self.right_var = tk.DoubleVar(value=self.min_val)
        if BUILDER_DEBUG: builder_logger.debug(f"🔋🎚️✨ [STATE] Initial fader value: {self.fader_var.get()}")
        
        # State Registration
        if self.path:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering multi-variable state for path '{self.path}'")
            self._register_var(self.fader_var, f"{self.path}/fader")
            self._register_var(self.left_var, f"{self.path}/left_meter")
            self._register_var(self.right_var, f"{self.path}/right_meter")
            
        # UI Components
        if BUILDER_DEBUG: builder_logger.trace("🏗️🪟🎨 [CONSTRUCT] Creating main canvas for composite fader.")
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Apply Industrial Transparency
        if builder_instance and hasattr(builder_instance, '_apply_transparency'):
            if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to composite fader.")
            builder_instance._apply_transparency(self, self.canvas, config, builder_instance)

        # Optimization: Trace variable changes to move components without redraw
        self.fader_var.trace_add("write", self._update_fader_pos)
        self.left_var.trace_add("write", lambda *a: self._update_meter("left"))
        self.right_var.trace_add("write", lambda *a: self._update_meter("right"))
        
        # Bindings
        if BUILDER_DEBUG: builder_logger.trace("🖱️👆🔗 [EVENTS] Binding input protocols for composite fader.")
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-2>", self._generate_random_value)
        
        # Initial complete draw
        self.canvas.after(10, self._draw_static)
        self.canvas.after(20, self._draw_dynamic)

    def _register_var(self, var, path):
        if self.state_mirror_engine:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering variable for component at path '{path}'")
            topic = self.state_mirror_engine.register_widget(path, var, self.base_mqtt_topic, self.widget_config)
            if self.subscriber_router and topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing component to topic: {topic}")
                self.subscriber_router.subscribe_to_topic(topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui)
            
            if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing component state for '{path}'")
            self.state_mirror_engine.initialize_widget_state(path)
            
            def on_gui_change(*args):
                if BUILDER_DEBUG: builder_logger.debug(f"⚡🔴📡 [EVENT] GUI change for fader component '{path}'. Broadcasting.")
                self.state_mirror_engine.broadcast_gui_change_to_mqtt(path)
            
            var.trace_add("write", on_gui_change)

    def _on_resize(self, event):
        if event.width > 5: self.width = event.width
        if event.height > 5: self.height = event.height
        if BUILDER_DEBUG: builder_logger.trace(f"📐📏🔄 [LAYOUT] FaderBarGraph resizing to {self.width}x{self.height}")
        self._draw_static()
        self._draw_dynamic()

    def _get_pos_from_val(self, val, height):
        range_v = self.max_val - self.min_val
        norm = (val - self.min_val) / range_v if range_v != 0 else 0
        norm = max(0.0, min(1.0, norm))
        if self.log_exponent != 1.0: norm = norm ** (1.0 / self.log_exponent)
        return height - (norm * height)

    def _get_val_from_y(self, y, draw_h, y_offset=0):
        rel_y = y - y_offset
        norm = 1.0 - (rel_y / draw_h)
        norm = max(0.0, min(1.0, norm))
        if self.log_exponent != 1.0: norm = norm ** self.log_exponent
        return self.min_val + (norm * (self.max_val - self.min_val))

    def _draw_static(self):
        """Draws components that only change on resize (Tracks, Wells, Ticks)."""
        if BUILDER_DEBUG: builder_logger.trace("🔄✨🎨 [REDRAW] Rendering static fader/meter tracks.")
        self.canvas.delete("static")
        w, h = self.width, self.height
        
        # Background
        if hasattr(self.canvas, 'panel_bg_image') and self.canvas.panel_bg_image:
            self.canvas.create_image(0, 0, image=self.canvas.panel_bg_image, anchor="nw", tags="static")

        meter_w, pad = self.meter_width, self.bar_padding
        self.top_m, self.bot_m = 25, 25
        self.draw_h = h - (self.top_m + self.bot_m)
        
        # Calculate X positions
        fader_w_req = self.widget_config.get("fader_width", None)
        f_w = int(fader_w_req) if fader_w_req else (w - (meter_w * 2) - (pad * 2) if self.enable_meters else w - (pad * 2))
        f_w = max(10, f_w)
        
        if self.enable_meters:
            total_w = (meter_w * 2) + (pad * 2) + f_w
            self.x_left = (w - total_w) / 2
            self.x_fader = self.x_left + meter_w + pad
            self.x_right = self.x_fader + f_w + pad
            
            # Meter Wells
            for x in [self.x_left, self.x_right]:
                self.canvas.create_rectangle(x, self.top_m, x+meter_w, self.top_m+self.draw_h, fill="#0a0a0a", outline="#333", tags="static")
                self.canvas.create_line(x+1, self.top_m+1, x+meter_w-1, self.top_m+1, fill="#000", tags="static")
                self.canvas.create_line(x+1, self.top_m+1, x+1, self.top_m+self.draw_h-1, fill="#000", tags="static")
        else:
            self.x_fader = (w - f_w) / 2

        # Fader Track Slot
        self.cx = self.x_fader + f_w/2
        sw = 10
        self.canvas.create_rectangle(self.cx - sw/2, self.top_m - 5, self.cx + sw/2, self.top_m + self.draw_h + 5, fill="#0a0a0a", outline="#333", tags="static")
        self.canvas.create_line(self.cx-sw/2+1, self.top_m-4, self.cx-sw/2+1, self.top_m+self.draw_h+4, fill="#000", tags="static")
        
        # Ticks
        if self.show_ticks and self.enable_meters:
            steps = self.tick_steps
            for i in range(steps+1):
                norm = i/steps
                ty = self.top_m + (self.draw_h * (1.0 - norm))
                tick_val = self.min_val + norm * (self.max_val - self.min_val)
                self.canvas.create_line(self.x_left, ty, self.x_left-5, ty, fill="gray", tags="static")
                self.canvas.create_line(self.x_right+meter_w, ty, self.x_right+meter_w+5, ty, fill="gray", tags="static")
                if i % 2 == 0:
                    self.canvas.create_text(self.x_left-7, ty, text=f"{int(tick_val)}", fill="gray", font=("Helvetica", 7), anchor="e", tags="static")

    def _draw_dynamic(self):
        """Draws components that move/change frequently (Fader Cap, Meter Fills)."""
        if BUILDER_DEBUG: builder_logger.trace("🔄✨🎚️ [REDRAW] Rendering dynamic fader cap and meter fills.")
        self.canvas.delete("dynamic")
        
        # 1. Meters
        if self.enable_meters:
            self._update_meter("left")
            self._update_meter("right")
            
        # 2. Fader Cap
        cap_h = self.cap_height
        f_w = int(self.widget_config.get("fader_width", 40))
        cap_w = self.widget_config.get("cap_width", f_w + (self.meter_width * 2) + (self.bar_padding * 2) + 4)
        
        self.cap_img = get_3d_fader_bar_cap_asset(int(cap_w), int(cap_h), self.fader_grip_color, self.fader_track_color)
        
        val = self.fader_var.get()
        y = self.top_m + self._get_pos_from_val(val, self.draw_h)
        self.canvas.create_image(self.cx, y, image=self.cap_img, tags=("dynamic", "cap"))
        
        # Value Label
        text_col = "white" if self.fader_grip_color.lower() in ["black", "#000000", "#222222"] else "black"
        self.canvas.create_text(self.cx, y, text=f"{val:.1f}", fill=text_col, font=("Helvetica", 7, "bold"), tags=("dynamic", "cap_text"))

    def _update_fader_pos(self, *args):
        if not hasattr(self, 'draw_h'): return # Guard: Wait for initial layout
        val = self.fader_var.get()
        if BUILDER_DEBUG: builder_logger.trace(f"✨🔄🎚️ [SYNC] Updating fader cap position to: {val:.1f}")
        y = self.top_m + self._get_pos_from_val(val, self.draw_h)
        self.canvas.coords("cap", self.cx, y)
        self.canvas.coords("cap_text", self.cx, y)
        self.canvas.itemconfig("cap_text", text=f"{val:.1f}")

    def _update_meter(self, side):
        tag = f"fill_{side}"
        self.canvas.delete(tag)
        
        x = self.x_left if side == "left" else self.x_right
        val = self.left_var.get() if side == "left" else self.right_var.get()
        style = self.left_style if side == "left" else self.right_style
        
        meter_w = self.meter_width
        val_h = self.draw_h - self._get_pos_from_val(val, self.draw_h)
        fy = self.top_m + (self.draw_h - val_h)
        
        # Color ranges
        low_c = style.get("lower_range_colour", "#00ff00")
        mid_c = style.get("middle_range_colour", "#ffff00")
        high_c = style.get("upper_range_colour", "#ff0000")
        
        s1, s2 = self.draw_h * 0.4, self.draw_h * 0.2
        # Green
        g1, g2 = max(fy, self.top_m + s1), self.top_m + self.draw_h
        if g2 > g1: self.canvas.create_rectangle(x+1, g1, x+meter_w-1, g2, fill=low_c, outline="", tags=("dynamic", tag))
        # Yellow
        y1, y2 = max(fy, self.top_m + s2), min(self.top_m + s1, self.top_m + self.draw_h)
        if y2 > y1: self.canvas.create_rectangle(x+1, y1, x+meter_w-1, y2, fill=mid_c, outline="", tags=("dynamic", tag))
        # Red
        r1, r2 = max(fy, self.top_m), min(self.top_m + s2, self.top_m + self.draw_h)
        if r2 > r1: self.canvas.create_rectangle(x+1, r1, x+meter_w-1, r2, fill=high_c, outline="", tags=("dynamic", tag))

    def render(self): self._draw_static(); self._draw_dynamic()

    def _generate_random_value(self, event):
        if BUILDER_DEBUG: builder_logger.debug("🎲✨🔢 [DEBUG] Generating random meter values.")
        self.left_var.set(random.uniform(self.min_val, self.max_val))
        self.right_var.set(random.uniform(self.min_val, self.max_val))

    def _on_press(self, event): self._on_drag(event)
    def _on_drag(self, event):
        val = self._get_val_from_y(event.y, self.draw_h, self.top_m)
        self.fader_var.set(max(self.min_val, min(self.max_val, val)))


@WidgetRegistry.register("_FaderWithBarGraph")
class BuilderFaderBarGraphCreator:
    
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """
        Static factory method for creating a fader-with-bar-graph widget.
        """
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🎚️ [BUILDER] Entering BuilderFaderBarGraphCreator.make")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        label = config_data.get("label_active", "")
        path = config_data.get("path", "")
        
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
            # Fallback for legacy calls
            state_mirror_engine = kwargs.get("state_mirror_engine")
            subscriber_router = kwargs.get("subscriber_router")
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path", "")
            builder_instance = kwargs.get("builder_instance")
            app_instance = kwargs.get("app_instance")
            if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to self/kwargs.")

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️🎚️ [BUILDER] Spawning composite fader-meter for '{label}' at path '{path}'.")

        base_mqtt_topic = base_mqtt_topic_from_path
        
        if label:
            if BUILDER_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [CONSTRUCT] Creating wrapper frame and label for '{label}'")
            wrapper = tk.Frame(parent_widget)
            lbl = tk.Label(wrapper, text=label, fg="#dcdcdc", font=("Helvetica", 10))
            lbl.pack(side=tk.TOP, fill=tk.X)
            if hasattr(builder_instance, '_apply_transparency'):
                if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying transparency to fader-meter wrapper.")
                builder_instance._apply_transparency(wrapper, None, config_data, builder_instance)
            
            frame = FaderWithBarGraphFrame(wrapper, config_data, path, state_mirror_engine, subscriber_router, base_mqtt_topic, builder_instance=builder_instance)
            frame.pack(fill=tk.BOTH, expand=True)
            
            wrapper.lbl = lbl
            wrapper.render = lambda: (lbl.config(bg=wrapper.cget("bg")), frame.render())
            return wrapper
            
        return FaderWithBarGraphFrame(parent_widget, config_data, path, state_mirror_engine, subscriber_router, base_mqtt_topic, builder_instance=builder_instance)

    def make_fader_bar_graph(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderFaderBarGraphCreator.make(parent_widget, config_data, context, builder_instance=self, **kwargs)
