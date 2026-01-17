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
        self.width = int(layout_config.get("width", config.get("width", 100)))
        self.height = int(layout_config.get("height", config.get("height", 400)))
        
        # Ticks
        self.show_ticks = config.get("show_ticks", True)
        self.tick_thickness = int(config.get("tick_thickness", 1))
        self.tick_color = config.get("tick_color", "light grey")
        self.tick_interval = float(config.get("tick_interval", (self.max_val - self.min_val) / 10.0))

        # State
        self.mode = "macro" # "macro" (closed) or "micro" (open)
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
            
            if self.path:
                child_path = f"{self.path}/ch_{i+1}"
                self.state_mirror_engine.register_widget(child_path, var, self.base_mqtt_topic, config)
                var.trace_add("write", self._request_redraw)

        self.master_value.set(self._calculate_master_average())
        self._recalculate_offsets()
        
        self.master_value.trace_add("write", self._request_redraw)

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
        self.canvas.bind("<Button-3>", self._toggle_mode) # Right click to toggle view
        self.canvas.bind("<Double-Button-1>", self._toggle_mode) # Double click too
        self.canvas.bind("<Configure>", self._on_resize)

        self._draw()

    def _calculate_master_average(self):
        total = sum([v.get() for v in self.child_values])
        return total / len(self.child_values) if self.child_values else self.min_val

    def _recalculate_offsets(self):
        m_val = self.master_value.get()
        for i in range(self.num_channels):
            self.child_offsets[i] = self.child_values[i].get() - m_val

    def _update_children_from_master(self):
        m_val = self.master_value.get()
        for i in range(self.num_channels):
            new_val = m_val + self.child_offsets[i]
            new_val = max(self.min_val, min(self.max_val, new_val))
            self.child_values[i].set(new_val)
            if self.path:
                self.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{self.path}/ch_{i+1}")

    def _update_master_from_children(self):
        new_master = self._calculate_master_average()
        self.master_value.set(new_master)
        self._recalculate_offsets()

    def _toggle_mode(self, event):
        self.mode = "micro" if self.mode == "macro" else "macro"
        self._draw()

    def _on_resize(self, event):
        self.width = event.width
        self.height = event.height
        self._draw()

    def _get_y_from_val(self, val):
        norm = (val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) != 0 else 0
        # Add padding for cap
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
        
        if (cap_y - cap_h/2) <= event.y <= (cap_y + cap_h/2):
            if self.mode == "micro":
                strip_w = self.width / self.num_channels
                col_idx = int(event.x / strip_w)
                if 0 <= col_idx < self.num_channels:
                    self.dragging_child = col_idx
                    self.start_val = self.child_values[col_idx].get()
                    return
            
            self.dragging_master = True
            self.start_val = m_val
        else:
            self.dragging_master = True
            self.start_val = self._get_val_from_y(event.y)
            self.master_value.set(max(self.min_val, min(self.max_val, self.start_val)))
            self._update_children_from_master()

    def _on_drag(self, event):
        if self.dragging_master:
            new_val = self._get_val_from_y(event.y)
            new_val = max(self.min_val, min(self.max_val, new_val))
            self.master_value.set(new_val)
            self._update_children_from_master()
            
        elif self.dragging_child >= 0:
            dy = self.start_y - event.y
            val_range = self.max_val - self.min_val
            pixel_range = self.height - 40
            
            delta_val = (dy / pixel_range) * val_range
            new_val = self.start_val + delta_val
            new_val = max(self.min_val, min(self.max_val, new_val))
            
            self.child_values[self.dragging_child].set(new_val)
            self._update_master_from_children()

    def _on_release(self, event):
        self.dragging_master = False
        self.dragging_child = -1

    def _request_redraw(self, *args):
        self._draw()

    def _draw_ticks(self, cx, h):
        if not self.show_ticks: return
        
        val_range = self.max_val - self.min_val
        if val_range == 0: return
        
        # Determine number of ticks
        steps = int(val_range / self.tick_interval)
        
        for i in range(steps + 1):
            val = self.min_val + (i * self.tick_interval)
            y = self._get_y_from_val(val)
            
            # Draw tick line
            # Check width to decide style. If wide, ticks on both sides?
            # Standard: Ticks on track.
            w = 20 # track width approx
            self.canvas.create_line(cx - 10, y, cx + 10, y, fill=self.tick_color, width=self.tick_thickness)
            
            # Label
            if i % 2 == 0: # Every other tick
                self.canvas.create_text(cx + 15, y, text=f"{int(val)}", fill=self.tick_color, anchor="w", font=("Arial", 8))

    def _draw(self):
        self.canvas.delete("all")
        w, h = self.width, self.height
        cx = w / 2
        
        # 1. Track
        self.canvas.create_line(cx, 20, cx, h-20, fill=self.track_col, width=4, capstyle=tk.ROUND)
        
        # 2. Ticks
        self._draw_ticks(cx, h)
        
        # 3. Master Cap Position
        m_val = self.master_value.get()
        cap_y = self._get_y_from_val(m_val)
        cap_h = 60 
        cap_w = w - 10 # Slightly smaller than full width
        
        # 4. Draw Cap Container (The "Smart" Screen)
        # Bezel / Housing
        self.canvas.create_rectangle(
            cx - cap_w/2, cap_y - cap_h/2, 
            cx + cap_w/2, cap_y + cap_h/2, 
            fill="#333333", outline=self.handle_col, width=2
        )
        
        # Screen Area
        screen_margin = 4
        sx1 = cx - cap_w/2 + screen_margin
        sx2 = cx + cap_w/2 - screen_margin
        sy1 = cap_y - cap_h/2 + screen_margin
        sy2 = cap_y + cap_h/2 - screen_margin
        
        self.canvas.create_rectangle(sx1, sy1, sx2, sy2, fill="black", outline="")
        
        # 5. Draw Cap Content
        if self.mode == "macro":
            # Waveform / Gradient Bar
            norm_val = (m_val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
            
            # Simple bar visualization
            bar_w = (sx2 - sx1) * 0.9
            bar_h = 10
            bx1 = (sx1 + sx2)/2 - bar_w/2
            bx2 = (sx1 + sx2)/2 + bar_w/2
            by1 = (sy1 + sy2)/2 - bar_h/2
            by2 = (sy1 + sy2)/2 + bar_h/2
            
            self.canvas.create_rectangle(bx1, by1, bx2, by2, fill=self._get_color(norm_val), outline="")
            self.canvas.create_text((sx1+sx2)/2, (sy1+sy2)/2 + 15, text=f"{m_val:.1f}", fill="white", font=("Arial", 8))
            self.canvas.create_text((sx1+sx2)/2, (sy1+sy2)/2 - 15, text="AVG", fill="#888888", font=("Arial", 6))
            
        elif self.mode == "micro":
            # Vertical Stripes for Children
            total_screen_w = sx2 - sx1
            strip_w = total_screen_w / self.num_channels
            
            for i in range(self.num_channels):
                c_val = self.child_values[i].get()
                norm_c = (c_val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
                
                x1 = sx1 + i * strip_w
                x2 = x1 + strip_w
                
                # Gap
                x1 += 1
                x2 -= 1
                
                # Visualizing Value inside the strip
                fill_h = norm_c * (sy2 - sy1)
                bar_top = sy2 - fill_h
                
                # Background
                self.canvas.create_rectangle(x1, sy1, x2, sy2, fill="#222222", outline="")
                # Value
                self.canvas.create_rectangle(x1, bar_top, x2, sy2, fill=self._get_color(norm_c), outline="")
                # Label
                self.canvas.create_text((x1+x2)/2, sy2 - 5, text=f"{i+1}", fill="white", font=("Arial", 6), anchor="s")

    def _get_color(self, norm_val):
        if norm_val < 0.5:
            r = int(255 * (norm_val * 2))
            g = 255
            b = 0
        else:
            r = 255
            g = int(255 * (1.0 - (norm_val - 0.5) * 2))
            b = 0
        return f"#{r:02x}{g:02x}{b:02x}"


class CompositeFaderCreatorMixin:
    def _create_composite_fader(self, parent_widget, config_data, **kwargs):
        path = config_data.get("path", "")
        base_mqtt_topic = kwargs.get("base_mqtt_topic_from_path", "")
        
        frame = CompositeFaderFrame(
            parent_widget, 
            config_data, 
            path, 
            self.state_mirror_engine, 
            self.subscriber_router,
            base_mqtt_topic
        )
        
        if path:
            self.state_mirror_engine.register_widget(path, frame.master_value, base_mqtt_topic, config_data)
            topic = get_topic(self.state_mirror_engine.base_topic, base_mqtt_topic, path)
            self.subscriber_router.subscribe_to_topic(topic, self.state_mirror_engine.sync_incoming_mqtt_to_gui)
            self.state_mirror_engine.initialize_widget_state(path)
            
        return frame