# workers/builder/builder_composite/Composite_fader_multichannel.py

import tkinter as tk
from tkinter import ttk
import math
import sys
from managers.configini.config_reader import Config
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.styling.style import THEMES, DEFAULT_THEME
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.handlers.widget_event_binder import bind_variable_trace

app_constants = Config.get_instance()

MIN_CHANNEL_WIDTH = 30

class CompositeFaderFrame(tk.Frame):
    def __init__(self, master, config, path, state_mirror_engine, subscriber_router, base_mqtt_topic):
        colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        self.bg_color = colors.get("bg", "#2b2b2b")
        self.track_col = colors.get("secondary", "#444444")
        self.handle_col = colors.get("fg", "#dcdcdc")
        
        super().__init__(master, bg=self.bg_color, bd=0, highlightthickness=0)
        
        self.config = config
        self.path = path
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = subscriber_router
        self.base_mqtt_topic = base_mqtt_topic
        
        # Configuration
        self.min_val = float(config.get("value_min", 0.0))
        self.max_val = float(config.get("value_max", 100.0))
        self.num_channels = int(config.get("num_channels", 4))
        self.label = config.get("label_active", "Composite")
        
        # Visual Config
        layout_config = config.get("layout", {})
        
        # Calculate Width Requirements
        requested_w = int(layout_config.get("width", config.get("width", 100)))
        min_required_w = self.num_channels * MIN_CHANNEL_WIDTH
        self.req_width = max(requested_w, min_required_w)
        
        self.req_height = int(layout_config.get("height", config.get("height", 400)))
        self.width = self.req_width
        self.height = self.req_height
        
        self.show_ticks = config.get("show_ticks", True)
        self.tick_thickness = int(config.get("tick_thickness", 1))
        self.tick_color = config.get("tick_color", "light grey")
        self.tick_interval = float(config.get("tick_interval", (self.max_val - self.min_val) / 10.0))

        # State
        self.mode = "macro" 
        self._lock_sync = False # Prevents circular updates
        
        self.master_value = tk.DoubleVar(value=self.min_val)
        self.child_values = []
        self.child_offsets = []
        
        # Initialize Children
        channel_config = config.get("channels", [])
        for i in range(self.num_channels):
            val = self.min_val
            if i < len(channel_config):
                val = float(channel_config[i].get("default", self.min_val))
            
            var = tk.DoubleVar(value=val)
            self.child_values.append(var)
            self.child_offsets.append(0.0)
            
            # Register with State Engine
            if self.path:
                child_path = f"{self.path}/ch_{i+1}"
                self.state_mirror_engine.register_widget(child_path, var, self.base_mqtt_topic, config)
                
            # Internal trace for logic
            var.trace_add("write", lambda *args, idx=i: self._on_child_var_change(idx))

        # Master trace for logic
        self.master_value.trace_add("write", self._on_master_var_change)

        # Initial Sync
        self._update_master_from_children(broadcast=False)
        self._recalculate_offsets()

        # UI Setup
        self.canvas = tk.Canvas(self, width=self.width, height=self.height, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Interaction State
        self.dragging_master = False
        self.dragging_child = -1
        self.start_y = 0
        self.start_val = 0
        
        # Bindings
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
        total = sum([v.get() for v in self.child_values])
        return total / len(self.child_values) if self.child_values else self.min_val

    def _recalculate_offsets(self):
        m_val = self.master_value.get()
        for i in range(self.num_channels):
            self.child_offsets[i] = self.child_values[i].get() - m_val

    def _update_children_from_master(self, broadcast=True):
        m_val = self.master_value.get()
        for i in range(self.num_channels):
            new_val = m_val + self.child_offsets[i]
            new_val = max(self.min_val, min(self.max_val, new_val))
            if abs(self.child_values[i].get() - new_val) > 0.001:
                self.child_values[i].set(new_val)
                if broadcast and self.path:
                    self.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{self.path}/ch_{i+1}")

    def _update_master_from_children(self, broadcast=True):
        new_master = self._calculate_master_average()
        if abs(self.master_value.get() - new_master) > 0.001:
            self.master_value.set(new_master)
            if broadcast and self.path:
                self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _on_master_var_change(self, *args):
        if self._lock_sync: return
        self._lock_sync = True
        self._update_children_from_master(broadcast=False) # Variable trace handles broadcast? No, StateMirror does.
        # However, we might want explicit control here if we are sliding.
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
        if event.width > 1: self.width = event.width
        if event.height > 1: self.height = event.height
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
        m_val = self.master_value.get()
        cap_y = self._get_y_from_val(m_val)
        cap_h = 60
        
        # Calculate active area same as draw
        draw_w = self.req_width
        offset_x = (self.width - draw_w) / 2 if self.width > draw_w else 0
        
        if (cap_y - cap_h/2) <= event.y <= (cap_y + cap_h/2):
            if self.mode == "micro":
                # Check bounds horizontally
                if offset_x <= event.x <= (offset_x + draw_w):
                    strip_w = draw_w / self.num_channels
                    col_idx = int((event.x - offset_x) / strip_w)
                    if 0 <= col_idx < self.num_channels:
                        self.dragging_child = col_idx
                        self.start_val = self.child_values[col_idx].get()
                        return
            self.dragging_master = True
            self.start_val = m_val
        else:
            self.dragging_master = True
            self.start_val = self._get_val_from_y(event.y)
            new_v = max(self.min_val, min(self.max_val, self.start_val))
            self.master_value.set(new_v)
            if self.path:
                self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _on_drag(self, event):
        if self.dragging_master:
            new_val = self._get_val_from_y(event.y)
            new_val = max(self.min_val, min(self.max_val, new_val))
            self.master_value.set(new_val)
            if self.path:
                self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)
            
        elif self.dragging_child >= 0:
            dy = self.start_y - event.y
            val_range = self.max_val - self.min_val
            pixel_range = self.height - 40
            delta_val = (dy / pixel_range) * val_range
            new_val = max(self.min_val, min(self.max_val, self.start_val + delta_val))
            
            self.child_values[self.dragging_child].set(new_val)
            if self.path:
                self.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{self.path}/ch_{self.dragging_child+1}")

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

        current_val = self.master_value.get()
        val_range = self.max_val - self.min_val
        step = val_range * 0.05 
        new_val = max(self.min_val, min(self.max_val, current_val + (delta * step)))
        
        self.master_value.set(new_val)
        if self.path:
            self.state_mirror_engine.broadcast_gui_change_to_mqtt(self.path)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _request_redraw(self, *args):
        self._draw()

    def _draw_ticks(self, width, height, offset_x=0):
        if not self.show_ticks: return
        val_range = self.max_val - self.min_val
        if val_range == 0: return
        steps = int(val_range / self.tick_interval)
        for i in range(steps + 1):
            val = self.min_val + (i * self.tick_interval)
            y = self._get_y_from_val(val)
            # Ticks span the active drawing area
            self.canvas.create_line(offset_x, y, offset_x + width, y, fill=self.tick_color, width=self.tick_thickness)
            if i % 2 == 0:
                # Numbers on both left and right
                self.canvas.create_text(offset_x + 5, y - 5, text=f"{int(val)}", fill=self.tick_color, anchor="w", font=("Arial", 8))
                self.canvas.create_text(offset_x + width - 5, y - 5, text=f"{int(val)}", fill=self.tick_color, anchor="e", font=("Arial", 8))

    def _draw_channel_lines(self, width, height, offset_x=0):
        strip_w = width / self.num_channels
        for i in range(self.num_channels):
            # Center line for each channel track
            x = offset_x + (i * strip_w) + (strip_w / 2)
            self.canvas.create_line(x, 20, x, height - 20, fill=self.track_col, width=4, capstyle=tk.ROUND)
            
            # Subtle boundary line between channels
            if i > 0:
                bx = offset_x + (i * strip_w)
                self.canvas.create_line(bx, 20, bx, height - 20, fill="#333333", width=1, dash=(2, 4))

    def _draw_channel_values(self, width, offset_x=0):
        # Draw a small marker on each channel track for its current value
        strip_w = width / self.num_channels
        for i in range(self.num_channels):
            c_val = self.child_values[i].get()
            y = self._get_y_from_val(c_val)
            norm_c = (c_val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
            
            cx = offset_x + (i * strip_w) + (strip_w / 2)
            
            # Draw marker line
            marker_w = strip_w * 0.6
            color = self._get_color(norm_c)
            self.canvas.create_line(cx - marker_w/2, y, cx + marker_w/2, y, fill=color, width=3)

    def _draw_rounded_rectangle(self, x1, y1, x2, y2, radius=10, **kwargs):
        points = [
            x1 + radius, y1, x1 + radius, y1, x2 - radius, y1, x2 - radius, y1,
            x2, y1, x2, y1 + radius, x2, y1 + radius, x2, y2 - radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x2 - radius, y2,
            x1 + radius, y2, x1 + radius, y2, x1, y2, x1, y2 - radius,
            x1, y2 - radius, x1, y1 + radius, x1, y1 + radius, x1, y1,
        ]
        return self.canvas.create_polygon(points, **kwargs, smooth=True)

    def _draw(self):
        self.canvas.delete("all")
        
        # Calculate active drawing area
        draw_w = self.req_width
        offset_x = (self.width - draw_w) / 2 if self.width > draw_w else 0
        h = self.height
        
        # 1. Background / Tracks (Draw one solid line per channel)
        self._draw_channel_lines(draw_w, h, offset_x)
        
        # 2. Draw Channel Value Markers
        self._draw_channel_values(draw_w, offset_x)
        
        # 3. Ticks (End to End with numbers on both sides)
        self._draw_ticks(draw_w, h, offset_x)
        
        m_val = self.master_value.get()
        cap_y = self._get_y_from_val(m_val)
        cap_h, cap_w = 60, draw_w - 10 
        
        # 4. Draw Cap
        self._draw_rounded_rectangle(offset_x + draw_w/2 - cap_w/2, cap_y - cap_h/2, offset_x + draw_w/2 + cap_w/2, cap_y + cap_h/2, radius=8, fill="#333333", outline=self.handle_col, width=2)
        
        screen_margin = 4
        sx1, sx2 = offset_x + draw_w/2 - cap_w/2 + screen_margin, offset_x + draw_w/2 + cap_w/2 - screen_margin
        sy1, sy2 = cap_y - cap_h/2 + screen_margin, cap_y + cap_h/2 - screen_margin
        self.canvas.create_rectangle(sx1, sy1, sx2, sy2, fill="black", outline="")
        
        if self.mode == "macro":
            norm_val = (m_val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
            bar_w, bar_h = (sx2 - sx1) * 0.9, 10
            bx1, bx2 = (sx1 + sx2)/2 - bar_w/2, (sx1 + sx2)/2 + bar_w/2
            by1, by2 = (sy1 + sy2)/2 - bar_h/2, (sy1 + sy2)/2 + bar_h/2
            self.canvas.create_rectangle(bx1, by1, bx2, by2, fill=self._get_color(norm_val), outline="")
            self.canvas.create_text((sx1+sx2)/2, (sy1+sy2)/2 + 15, text=f"{m_val:.1f}", fill="white", font=("Arial", 8))
            self.canvas.create_text((sx1+sx2)/2, (sy1+sy2)/2 - 15, text="AVG", fill="#888888", font=("Arial", 6))
        elif self.mode == "micro":
            strip_w = (sx2 - sx1) / self.num_channels
            for i in range(self.num_channels):
                c_val = self.child_values[i].get()
                norm_c = (c_val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
                x1, x2 = sx1 + i * strip_w + 1, sx1 + (i + 1) * strip_w - 1
                fill_h = norm_c * (sy2 - sy1)
                self.canvas.create_rectangle(x1, sy1, x2, sy2, fill="#222222", outline="")
                self.canvas.create_rectangle(x1, sy2 - fill_h, x2, sy2, fill=self._get_color(norm_c), outline="")
                self.canvas.create_text((x1+x2)/2, sy2 - 5, text=f"{i+1}", fill="white", font=("Arial", 6), anchor="s")

    def _get_color(self, norm_val):
        if norm_val < 0.5:
            r, g, b = int(255 * (norm_val * 2)), 255, 0
        else:
            r, g, b = 255, int(255 * (1.0 - (norm_val - 0.5) * 2)), 0
        return f"#{r:02x}{g:02x}{b:02x}"


class CompositeFaderCreatorMixin:
    def _create_composite_fader(self, parent_widget, config_data, **kwargs):
        path = config_data.get("path", "")
        base_mqtt_topic = kwargs.get("base_mqtt_topic_from_path", "")
        
        frame = CompositeFaderFrame(parent_widget, config_data, path, self.state_mirror_engine, self.subscriber_router, base_mqtt_topic)
        
        if path:
            # Register master
            self.state_mirror_engine.register_widget(path, frame.master_value, base_mqtt_topic, config_data)
            topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic, path)
            self.subscriber_router.subscribe_to_topic(topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui)
            self.state_mirror_engine.initialize_widget_state(path)
            
            # Register and subscribe each child
            for i in range(frame.num_channels):
                child_path = f"{path}/ch_{i+1}"
                # Registration already happened in __init__ for variables
                child_topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic, child_path)
                self.subscriber_router.subscribe_to_topic(child_topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui)
                self.state_mirror_engine.initialize_widget_state(child_path)
            
        return frame