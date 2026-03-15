# workers/builder/fader_ganged_controlled_array/Composite_fader_multichannel.py

import tkinter as tk
from tkinter import ttk
import math
import sys
import inspect
import os
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
from managers.Display.transparency.transparency_mixin import TransparencyMixin
from managers.Display.transparency.transparency_manager import TransparencyManager
from managers.Display.factory.widget_registry import WidgetRegistry

MIN_CHANNEL_WIDTH = 40

# --- Module Level Cache for 3D Assets ---
_GCA_ASSET_CACHE = {}

def get_3d_gca_bridge_asset(w, h, body_color, outline_color):
    """Generates a photorealistic 3D 'Bridge' cap for GCA arrays."""
    cache_key = (w, h, body_color, outline_color)
    if cache_key in _GCA_ASSET_CACHE:
        if BUILDER_DEBUG: builder_logger.trace(f"📦🖼️✨ [CACHE] Retaining GCA bridge asset from cache: {w}x{h}")
        return _GCA_ASSET_CACHE[cache_key]

    if BUILDER_DEBUG: builder_logger.trace(f"🏗️🖼️🎨 [ASSET] Generating NEW 3D GCA bridge asset: {w}x{h}")
    pad = 15
    full_w, full_h = w + pad*2, h + pad*2
    base = Image.new("RGBA", (full_w, full_h), (0,0,0,0))
    
    # 1. Drop Shadow (Wide bridge needs soft shadow)
    shadow = Image.new("RGBA", (full_w, full_h), (0,0,0,0))
    s_draw = ImageDraw.Draw(shadow)
    s_draw.rounded_rectangle((pad+2, pad+4, pad+w+2, pad+h+4), radius=8, fill=(0,0,0,120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=6))
    base = Image.alpha_composite(base, shadow)
    
    # 2. Main Body (Bridge)
    body = Image.new("RGBA", (full_w, full_h), (0,0,0,0))
    b_draw = ImageDraw.Draw(body)
    b_draw.rounded_rectangle((pad, pad, pad+w, pad+h), radius=8, fill=body_color, outline=outline_color, width=1)
    
    # Metallic Glint / Bevel
    b_draw.line((pad+6, pad+1, pad+w-6, pad+1), fill=(255,255,255,100), width=1) # Top
    b_draw.line((pad+1, pad+6, pad+1, pad+h-6), fill=(255,255,255,50), width=1) # Left
    b_draw.line((pad+6, pad+h-1, pad+w-6, pad+h-1), fill=(0,0,0,80), width=1) # Bottom
    
    # 3. Inner Screen Area (Bezels)
    screen_pad = 4
    b_draw.rounded_rectangle((pad+screen_pad, pad+screen_pad, pad+w-screen_pad, pad+h-screen_pad), radius=4, fill="#000000")
    # Inner screen shadow
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


class CompositeFaderFrame(tk.Frame):
    def __init__(self, master, config, path, state_mirror_engine, subscriber_router, base_mqtt_topic):
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        self.bg_color = colors.get("bg", "#2b2b2b")
        self.track_col = colors.get("secondary", "#444444")
        self.handle_col = colors.get("fg", "#dcdcdc")
        self.accent_col = colors.get("accent", "#f4902c")
        
        super().__init__(master, bg=self.bg_color, bd=0, highlightthickness=0)
        
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🎚️ [BUILDER] Initializing CompositeFaderFrame")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config}")

        self.widget_config = config
        self.path = path
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = subscriber_router
        self.base_mqtt_topic = base_mqtt_topic
        
        # Configuration
        self.min_val = float(config.get("value_min", 0.0))
        self.max_val = float(config.get("value_max", 100.0))
        self.num_channels = int(config.get("num_channels", 4))
        self.label = config.get("label_active", "Composite")
        self.is_rgb = config.get("is_rgb", False)
        if BUILDER_DEBUG: builder_logger.debug(f"📐📏🔢 [RANGE] Channels: {self.num_channels}, Range: {self.min_val} to {self.max_val}")
        
        # Visual Config
        layout_config = config.get("layout", {})
        
        # Calculate Width Requirements
        requested_w = int(layout_config.get("width", config.get("width", 100)))
        min_required_w = self.num_channels * MIN_CHANNEL_WIDTH
        self.req_width = max(requested_w, min_required_w)
        
        self.req_height = int(layout_config.get("height", config.get("height", 400)))
        self.width = self.req_width
        self.height = self.req_height
        if BUILDER_DEBUG: builder_logger.debug(f"📏📐🔳 [DIM] GCA dimensions: {self.width}x{self.height}")
        
        self.show_ticks = config.get("show_ticks", True)
        self.tick_thickness = int(config.get("tick_thickness", 1))
        self.tick_color = config.get("tick_color", "light grey")
        self.tick_interval = config.get("tick_interval", None)

        # Channel Labels Config
        self.show_channel_labels = config.get("channel_labels_visible", True)
        self.channel_labels_pos = config.get("channel_labels_position", "bottom").lower() # "top" or "bottom"
        self.channel_labels_rotation = config.get("channel_labels_rotation", 0) # 0 or 90

        # State
        self.mode = "macro" 
        self._lock_sync = False # Prevents circular updates
        
        self.master_value = tk.DoubleVar(value=self.min_val)
        self.child_values = []
        self.child_offsets = []
        self.channel_labels = []
        
        # Initialize Children
        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🔳🕹️ [CONSTRUCT] Iterating through {self.num_channels} channels for state initialization.")
        channel_config = config.get("channels", [])
        for i in range(self.num_channels):
            val = self.min_val
            label = f"{i+1}"
            if i < len(channel_config):
                val = float(channel_config[i].get("default", self.min_val))
                label = channel_config[i].get("label", label)
            
            var = tk.DoubleVar(value=val)
            self.child_values.append(var)
            self.child_offsets.append(0.0)
            self.channel_labels.append(label)
            
            # Register with State Engine
            if self.path:
                child_path = f"{self.path}/ch_{i+1}"
                if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering channel {i+1} at path '{child_path}'")
                self.state_mirror_engine.register_widget(child_path, var, self.base_mqtt_topic, config)
                
            # Internal trace for logic
            var.trace_add("write", lambda *args, idx=i: self._on_child_var_change(idx))

        # Master trace for logic
        self.master_value.trace_add("write", self._on_master_var_change)

        # Initial Sync
        self._update_master_from_children(broadcast=False)
        self._recalculate_offsets()

        # UI Setup
        if BUILDER_DEBUG: builder_logger.trace("🏗️🪟🎨 [CONSTRUCT] Creating main composite canvas.")
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Interaction State
        self.dragging_master = False
        self.dragging_child = -1
        self.start_y = 0
        self.start_val = 0
        
        # Bindings
        if BUILDER_DEBUG: builder_logger.trace("🖱️👆🔗 [EVENTS] Binding input protocols for composite array.")
        self.canvas.bind("<Button-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._toggle_mode) 
        self.canvas.bind("<Double-Button-1>", self._toggle_mode) 
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

        self._draw()

    def _calculate_master_average(self):
        total = sum([self._safe_get(v) for v in self.child_values])
        return total / len(self.child_values) if self.child_values else self.min_val

    def _recalculate_offsets(self):
        m_val = self._safe_get(self.master_value)
        for i in range(self.num_channels):
            self.child_offsets[i] = self._safe_get(self.child_values[i]) - m_val

    def _update_children_from_master(self, broadcast=True):
        m_val = self._safe_get(self.master_value)
        for i in range(self.num_channels):
            new_val = m_val + self.child_offsets[i]
            new_val = max(self.min_val, min(self.max_val, new_val))
            if abs(self._safe_get(self.child_values[i]) - new_val) > 0.001:
                self.child_values[i].set(new_val)
                if broadcast and self.path:
                    self.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{self.path}/ch_{i+1}")

    def _update_master_from_children(self, broadcast=True):
        new_master = self._calculate_master_average()
        if abs(self._safe_get(self.master_value) - new_master) > 0.001:
            self.master_value.set(new_master)
            if broadcast and self.path:
                self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _on_master_var_change(self, *args):
        if self._lock_sync: return
        self._lock_sync = True
        self._update_children_from_master(broadcast=False) 
        self._lock_sync = False
        self._draw()

    def _on_child_var_change(self, idx, *args):
        if self._lock_sync: return
        self._lock_sync = True
        self._update_master_from_children(broadcast=False)
        self._recalculate_offsets()
        self._lock_sync = False
        self._draw()

    def _toggle_mode(self, event):
        self.mode = "micro" if self.mode == "macro" else "macro"
        self._draw()

    def _on_resize(self, event):
        if not hasattr(self, "_resize_timer"): self._resize_timer = None
        if self._resize_timer: self.after_cancel(self._resize_timer)
        w, h = event.width, event.height
        self._resize_timer = self.after(100, lambda: self._perform_resize(w, h))

    def _perform_resize(self, w, h):
        self._resize_timer = None
        if w > 1: self.width = w
        if h > 1: self.height = h
        self._draw()

    def _get_y_from_val(self, val):
        norm = (val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) != 0 else 0
        draw_h = self.height - 40
        return 20 + draw_h * (1.0 - norm)

    def _get_val_from_y(self, y):
        draw_h = self.height - 40
        norm = (draw_h - (y - 20)) / draw_h
        return self.min_val + (norm * (self.max_val - self.min_val))

    def _on_press(self, event):
        self.start_y = event.y
        m_val = self._safe_get(self.master_value)
        cap_y = self._get_y_from_val(m_val)
        cap_h = 60
        
        draw_w = self.req_width
        offset_x = (self.width - draw_w) / 2 if self.width > draw_w else 0
        
        if (cap_y - cap_h/2) <= event.y <= (cap_y + cap_h/2):
            if self.mode == "micro":
                if offset_x <= event.x <= (offset_x + draw_w):
                    strip_w = draw_w / self.num_channels
                    col_idx = int((event.x - offset_x) / strip_w)
                    if 0 <= col_idx < self.num_channels:
                        self.dragging_child = col_idx
                        self.start_val = self._safe_get(self.child_values[col_idx])
                        return
            self.dragging_master = True
            self.start_val = m_val
        else:
            self.dragging_master = True
            self.start_val = self._get_val_from_y(event.y)
            new_v = max(self.min_val, min(self.max_val, self.start_val))
            self.master_value.set(new_v)
            if self.path: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _on_drag(self, event):
        if self.dragging_master:
            new_val = self._get_val_from_y(event.y)
            new_val = max(self.min_val, min(self.max_val, new_val))
            self.master_value.set(new_val)
            if self.path: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)
        elif self.dragging_child >= 0:
            dy = self.start_y - event.y
            val_range = self.max_val - self.min_val
            pixel_range = self.height - 40
            delta_val = (dy / pixel_range) * val_range
            new_val = max(self.min_val, min(self.max_val, self.start_val + delta_val))
            self.child_values[self.dragging_child].set(new_val)
            if self.path: self.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{self.path}/ch_{self.dragging_child+1}")

    def _on_release(self, event):
        self.dragging_master = False
        self.dragging_child = -1
        
    def _on_mousewheel(self, event):
        delta = 0
        if sys.platform == "linux":
            if event.num == 4: delta = 1
            elif event.num == 5: delta = -1
        else:
            delta = 1 if event.delta > 0 else -1
        if delta == 0: return
        current_val = self._safe_get(self.master_value)
        val_range = self.max_val - self.min_val
        step = val_range * 0.05 
        new_val = max(self.min_val, min(self.max_val, current_val + (delta * step)))
        self.master_value.set(new_val)
        if self.path: self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _draw_ticks(self, width, height, offset_x=0):
        if not self.show_ticks: return
        val_range = self.max_val - self.min_val
        if val_range == 0: return
        
        # Smart tick logic
        if self.tick_interval is not None:
            ti = float(self.tick_interval)
        else:
            target_ticks = 10
            raw_interval = val_range / target_ticks
            exponent = math.floor(math.log10(raw_interval))
            fraction = raw_interval / (10**exponent)
            if fraction < 1.5: snapped = 1
            elif fraction < 3.5: snapped = 2
            elif fraction < 7.5: snapped = 5
            else: snapped = 10
            ti = snapped * (10**exponent)

        tick_values = []
        if ti > 0:
            curr = math.ceil(self.min_val / ti) * ti
            while curr <= self.max_val:
                tick_values.append(curr); curr += ti

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

        for i, val in enumerate(tick_values):
            y = self._get_y_from_val(val)
            if i % draw_every == 0:
                self.canvas.create_line(offset_x, y, offset_x + width, y, fill=self.tick_color, width=self.tick_thickness)
            if i % label_every == 0:
                # Format whole numbers without decimal points
                tick_text = str(int(val)) if val == int(val) else f"{val:.1f}"
                self.canvas.create_text(offset_x + 5, y - 5, text=tick_text, fill=self.tick_color, anchor="w", font=("Arial", 8))
                self.canvas.create_text(offset_x + width - 5, y - 5, text=tick_text, fill=self.tick_color, anchor="e", font=("Arial", 8))

    def _draw_channel_lines(self, width, height, offset_x=0):
        # ⚡ ALIGNMENT: Use same inner boundaries as the bridge bars
        cap_w = width - 10
        sx1 = offset_x + width/2 - cap_w/2 + 8
        sx2 = offset_x + width/2 + cap_w/2 - 8
        strip_w = (sx2 - sx1) / self.num_channels
        
        for i in range(self.num_channels):
            x = sx1 + (i * strip_w) + (strip_w / 2)
            # 3D Recessed Slot for each channel
            slot_w = 10
            self.canvas.create_rectangle(x - slot_w/2, 20, x + slot_w/2, height - 20, fill="#0a0a0a", outline="#333", width=1)
            self.canvas.create_line(x - slot_w/2 + 1, 21, x - slot_w/2 + 1, height - 21, fill="#000")
            self.canvas.create_line(x + slot_w/2, 20, x + slot_w/2, height - 20, fill="#444")
            
            if i > 0:
                bx = sx1 + (i * strip_w)
                self.canvas.create_line(bx, 20, bx, height - 20, fill="#1a1a1a", width=1, dash=(2, 4))

    def _draw_channel_values(self, width, offset_x=0):
        # ⚡ ALIGNMENT: Use same inner boundaries as the bridge bars
        cap_w = width - 10
        sx1 = offset_x + width/2 - cap_w/2 + 8
        sx2 = offset_x + width/2 + cap_w/2 - 8
        strip_w = (sx2 - sx1) / self.num_channels
        
        for i in range(self.num_channels):
            c_val = self._safe_get(self.child_values[i])
            y = self._get_y_from_val(c_val)
            norm_c = (c_val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
            cx = sx1 + (i * strip_w) + (strip_w / 2)
            marker_w = strip_w * 0.6
            if self.is_rgb:
                intensity = int(max(50, norm_c * 255))
                if i == 0: color = f"#{intensity:02x}0000"
                elif i == 1: color = f"#00{intensity:02x}00"
                elif i == 2: color = f"#0000{intensity:02x}"
                else: color = self._get_color(norm_c)
            else: color = self._get_color(norm_c)
            self.canvas.create_line(cx - marker_w/2, y, cx + marker_w/2, y, fill=color, width=3)

    def _draw_channel_labels(self, width, height, offset_x=0):
        if not self.show_channel_labels: return
        # ⚡ ALIGNMENT: Use same inner boundaries as the bridge bars
        cap_w = width - 10
        sx1 = offset_x + width/2 - cap_w/2 + 8
        sx2 = offset_x + width/2 + cap_w/2 - 8
        strip_w = (sx2 - sx1) / self.num_channels
        
        y_pos = height - 10 if self.channel_labels_pos == "bottom" else 10
        anchor = "s" if self.channel_labels_pos == "bottom" else "n"
        angle = self.channel_labels_rotation
        
        for i, label in enumerate(self.channel_labels):
            x = sx1 + (i * strip_w) + (strip_w / 2)
            self.canvas.create_text(x, y_pos, text=label, fill="white", font=("Helvetica", 7, "bold"), anchor=anchor, angle=angle)

    def _draw(self):
        if not hasattr(self, 'canvas'): return
        # ⚡ INDUSTRIAL TRANSPARENCY: Don't delete everything, preserve the patina slice
        for item in self.canvas.find_all():
            tags = self.canvas.gettags(item)
            if "panel_bg_slice" not in tags:
                self.canvas.delete(item)
        
        # 0. Draw Industrial Background (Fallback if slice doesn't exist)
        if hasattr(self.canvas, 'panel_bg_image') and not self.canvas.find_withtag("panel_bg_slice"):
            self.canvas.create_image(0, 0, image=self.canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")
            
        draw_w = self.req_width
        offset_x = (self.width - draw_w) / 2 if self.width > draw_w else 0
        h = self.height
        
        self._draw_channel_lines(draw_w, h, offset_x)
        self._draw_channel_values(draw_w, offset_x)
        self._draw_ticks(draw_w, h, offset_x)
        self._draw_channel_labels(draw_w, h, offset_x)
        
        m_val = self._safe_get(self.master_value)
        cap_y = self._get_y_from_val(m_val)
        cap_h, cap_w = 60, draw_w - 10 
        
        # 4. Draw 3D Bridge Cap
        bridge_img = get_3d_gca_bridge_asset(int(cap_w), int(cap_h), "#333333", self.accent_col)
        self.canvas.create_image(offset_x + draw_w/2, cap_y, image=bridge_img)
        self.canvas.bridge_img = bridge_img # Ref
        
        # Inner Content
        sx1, sx2 = offset_x + draw_w/2 - cap_w/2 + 8, offset_x + draw_w/2 + cap_w/2 - 8
        sy1, sy2 = cap_y - cap_h/2 + 8, cap_y + cap_h/2 - 8
        
        if self.mode == "macro":
            norm_val = (m_val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
            bar_w, bar_h = (sx2 - sx1) * 0.9, 10
            bx1, bx2 = (sx1 + sx2)/2 - bar_w/2, (sx1 + sx2)/2 + bar_w/2
            by1, by2 = (sy1 + sy2)/2 - bar_h/2, (sy1 + sy2)/2 + bar_h/2
            color = self._get_rgb_mixed_color() if self.is_rgb else self._get_color(norm_val)
            self.canvas.create_rectangle(bx1, by1, bx2, by2, fill=color, outline="")
            # Format whole numbers without decimal points
            readout_text = f"{int(m_val)}" if m_val == int(m_val) else f"{m_val:.1f}"
            self.canvas.create_text((sx1+sx2)/2, (sy1+sy2)/2 + 15, text=readout_text, fill="white", font=("Helvetica", 8, "bold"))
            self.canvas.create_text((sx1+sx2)/2, (sy1+sy2)/2 - 15, text="MIX" if self.is_rgb else "AVG", fill=self.accent_col, font=("Helvetica", 7, "bold"))
        elif self.mode == "micro":
            strip_w = (sx2 - sx1) / self.num_channels
            for i in range(self.num_channels):
                c_val = self._safe_get(self.child_values[i])
                norm_c = (c_val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
                x1, x2 = sx1 + i * strip_w + 1, sx1 + (i + 1) * strip_w - 1
                fill_h = norm_c * (sy2 - sy1)
                self.canvas.create_rectangle(x1, sy1, x2, sy2, fill="#111111", outline="")
                if self.is_rgb:
                    intensity = int(max(50, norm_c * 255))
                    if i == 0: color = f"#{intensity:02x}0000"
                    elif i == 1: color = f"#00{intensity:02x}00"
                    elif i == 2: color = f"#0000{intensity:02x}"
                    else: color = self._get_color(norm_c)
                else: color = self._get_color(norm_c)
                self.canvas.create_rectangle(x1, sy2 - fill_h, x2, sy2, fill=color, outline="")
                self.canvas.create_text((x1+x2)/2, sy2 - 5, text=f"{i+1}", fill="white", font=("Arial", 6), anchor="s")

    def _get_rgb_mixed_color(self):
        if len(self.child_values) < 3: return "#888888"
        r_val, g_val, b_val = self._safe_get(self.child_values[0]), self._safe_get(self.child_values[1]), self._safe_get(self.child_values[2])
        r = int(max(0, min(255, (r_val - self.min_val) / (self.max_val - self.min_val) * 255)))
        g = int(max(0, min(255, (g_val - self.min_val) / (self.max_val - self.min_val) * 255)))
        b = int(max(0, min(255, (b_val - self.min_val) / (self.max_val - self.min_val) * 255)))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _safe_get(self, var):
        try:
            val = var.get()
            if isinstance(val, str) and val.strip() == "": return self.min_val
            return float(val)
        except (tk.TclError, ValueError, TypeError): return self.min_val

    def _get_color(self, norm_val):
        if norm_val < 0.5: r, g, b = int(255 * (norm_val * 2)), 255, 0
        else: r, g, b = 255, int(255 * (1.0 - (norm_val - 0.5) * 2)), 0
        return f"#{r:02x}{g:02x}{b:02x}"


@WidgetRegistry.register("_CompositeFader")
class BuilderFaderGangedControlledArrayCreator(TransparencyMixin):
    
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """
        Static factory method for creating a ganged fader array.
        """
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🎚️ [BUILDER] Entering BuilderFaderGangedControlledArrayCreator.make")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        current_function_name = "make"
        label = config_data.get("label_active", "Composite")
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
            if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to kwargs.")

        if BUILDER_DEBUG: builder_logger.debug(f"🔬⚡️🎚️ [BUILDER] Spawning ganged fader array for '{label}' at path '{path}'.")

        base_mqtt_topic = base_mqtt_topic_from_path
        frame = CompositeFaderFrame(parent_widget, config_data, path, state_mirror_engine, subscriber_router, base_mqtt_topic)
        
        # ⚡ USE CENTRALIZED TRANSPARENCY ENGINE
        if hasattr(builder_instance, '_apply_transparency'):
            if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to ganged array.")
            TransparencyManager.apply_transparency(frame, frame.canvas, config_data, builder_instance)
        
        if path and state_mirror_engine:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering composite master and channel variables for path '{path}'")
            topic = state_mirror_engine.register_widget(path, frame.master_value, base_mqtt_topic, config_data)
            if subscriber_router and topic:
                if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing MASTER to topic: {topic}")
                subscriber_router.subscribe_to_topic(topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
            
            if BUILDER_DEBUG: builder_logger.trace(f"🔄⏳🔋 [STATE] Initializing MASTER state from cache/broker.")
            state_mirror_engine.initialize_widget_state(path)
            
            for i in range(frame.num_channels):
                child_path = f"{path}/ch_{i+1}"
                child_topic = state_mirror_engine.register_widget(child_path, frame.child_values[i], base_mqtt_topic, config_data)
                if subscriber_router and child_topic:
                    if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing channel {i+1} to topic: {child_topic}")
                    subscriber_router.subscribe_to_topic(child_topic, state_mirror_engine.sync_incoming_mqtt_to_gui)
                state_mirror_engine.initialize_widget_state(child_path)

        if BUILDER_DEBUG: builder_logger.success(f"✅🆗🎚️ [SUCCESS] The ganged fader array '{label}' has materialized!")
        return frame

    def make_fader_ganged_controlled_array(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderFaderGangedControlledArrayCreator.make(parent_widget, config_data, context, builder_instance=self, **kwargs)
