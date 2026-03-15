import math
import tkinter as tk
from workers.builder.fader_ganged_controlled_array.core.gca_asset_generator import GCAAssetGenerator

class GCARendererMixin:
    """Handles the rendering engine for the GCA fader array."""

    def _get_y_from_val(self, val):
        norm = (val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) != 0 else 0
        draw_h = self.height - 40
        return 20 + draw_h * (1.0 - norm)

    def _draw_ticks(self, width, height, offset_x=0):
        if not self.show_ticks: return
        val_range = self.max_val - self.min_val
        if val_range == 0: return
        
        ti = float(self.tick_interval) if self.tick_interval else self._calculate_smart_interval(val_range)
        tick_values = []
        if ti > 0:
            curr = math.ceil(self.min_val / ti) * ti
            while curr <= self.max_val:
                tick_values.append(curr); curr += ti

        label_every = self._get_label_step(len(tick_values))
        draw_every = self._get_draw_step(label_every)

        for i, val in enumerate(tick_values):
            y = self._get_y_from_val(val)
            if i % draw_every == 0:
                self.canvas.create_line(offset_x, y, offset_x + width, y, fill=self.tick_color, width=self.tick_thickness)
            if i % label_every == 0:
                tick_text = str(int(val)) if val == int(val) else f"{val:.1f}"
                self.canvas.create_text(offset_x + 5, y - 5, text=tick_text, fill=self.tick_color, anchor="w", font=("Arial", 8))
                self.canvas.create_text(offset_x + width - 5, y - 5, text=tick_text, fill=self.tick_color, anchor="e", font=("Arial", 8))

    def _draw_channel_lines(self, width, height, offset_x=0):
        cap_w = width - 10
        sx1 = offset_x + width/2 - cap_w/2 + 8
        sx2 = offset_x + width/2 + cap_w/2 - 8
        strip_w = (sx2 - sx1) / self.num_channels
        
        for i in range(self.num_channels):
            x = sx1 + (i * strip_w) + (strip_w / 2)
            slot_w = 10
            self.canvas.create_rectangle(x - slot_w/2, 20, x + slot_w/2, height - 20, fill="#0a0a0a", outline="#333", width=1)
            self.canvas.create_line(x - slot_w/2 + 1, 21, x - slot_w/2 + 1, height - 21, fill="#000")
            self.canvas.create_line(x + slot_w/2, 20, x + slot_w/2, height - 20, fill="#444")
            if i > 0:
                bx = sx1 + (i * strip_w)
                self.canvas.create_line(bx, 20, bx, height - 20, fill="#1a1a1a", width=1, dash=(2, 4))

    def _draw_channel_values(self, width, offset_x=0):
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
            color = self._get_channel_color(i, norm_c)
            self.canvas.create_line(cx - marker_w/2, y, cx + marker_w/2, y, fill=color, width=3)

    def _draw_channel_labels(self, width, height, offset_x=0):
        if not self.show_channel_labels: return
        cap_w = width - 10
        sx1 = offset_x + width/2 - cap_w/2 + 8
        sx2 = offset_x + width/2 + cap_w/2 - 8
        strip_w = (sx2 - sx1) / self.num_channels
        y_pos = height - 10 if self.channel_labels_pos == "bottom" else 10
        anchor = "s" if self.channel_labels_pos == "bottom" else "n"
        
        for i, label in enumerate(self.channel_labels):
            x = sx1 + (i * strip_w) + (strip_w / 2)
            self.canvas.create_text(x, y_pos, text=label, fill="white", font=("Helvetica", 7, "bold"), anchor=anchor, angle=self.channel_labels_rotation)

    def _draw(self):
        if not hasattr(self, 'canvas'): return
        for item in self.canvas.find_all():
            if "panel_bg_slice" not in self.canvas.gettags(item): self.canvas.delete(item)
        
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
        
        bridge_img = GCAAssetGenerator.get_3d_bridge(int(cap_w), int(cap_h), "#333333", self.accent_col)
        self.canvas.create_image(offset_x + draw_w/2, cap_y, image=bridge_img)
        self.canvas.bridge_img = bridge_img
        
        sx1, sx2 = offset_x + draw_w/2 - cap_w/2 + 8, offset_x + draw_w/2 + cap_w/2 - 8
        sy1, sy2 = cap_y - cap_h/2 + 8, cap_y + cap_h/2 - 8
        
        if self.mode == "macro":
            self._draw_macro_view(sx1, sx2, sy1, sy2, m_val)
        else:
            self._draw_micro_view(sx1, sx2, sy1, sy2)

    def _draw_macro_view(self, sx1, sx2, sy1, sy2, m_val):
        norm_val = (m_val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
        bar_w, bar_h = (sx2 - sx1) * 0.9, 10
        bx1, bx2 = (sx1 + sx2)/2 - bar_w/2, (sx1 + sx2)/2 + bar_w/2
        by1, by2 = (sy1 + sy2)/2 - bar_h/2, (sy1 + sy2)/2 + bar_h/2
        color = self._get_rgb_mixed_color() if self.is_rgb else self._get_color(norm_val)
        self.canvas.create_rectangle(bx1, by1, bx2, by2, fill=color, outline="")
        text = f"{int(m_val)}" if m_val == int(m_val) else f"{m_val:.1f}"
        self.canvas.create_text((sx1+sx2)/2, (sy1+sy2)/2 + 15, text=text, fill="white", font=("Helvetica", 8, "bold"))
        self.canvas.create_text((sx1+sx2)/2, (sy1+sy2)/2 - 15, text="MIX" if self.is_rgb else "AVG", fill=self.accent_col, font=("Helvetica", 7, "bold"))

    def _draw_micro_view(self, sx1, sx2, sy1, sy2):
        strip_w = (sx2 - sx1) / self.num_channels
        for i in range(self.num_channels):
            c_val = self._safe_get(self.child_values[i])
            norm_c = (c_val - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
            x1, x2 = sx1 + i * strip_w + 1, sx1 + (i + 1) * strip_w - 1
            fill_h = norm_c * (sy2 - sy1)
            self.canvas.create_rectangle(x1, sy1, x2, sy2, fill="#111111", outline="")
            color = self._get_channel_color(i, norm_c)
            self.canvas.create_rectangle(x1, sy2 - fill_h, x2, sy2, fill=color, outline="")
            self.canvas.create_text((x1+x2)/2, sy2 - 5, text=f"{i+1}", fill="white", font=("Arial", 6), anchor="s")

    def _get_channel_color(self, i, norm_c):
        if self.is_rgb:
            intensity = int(max(50, norm_c * 255))
            if i == 0: return f"#{intensity:02x}0000"
            if i == 1: return f"#00{intensity:02x}00"
            if i == 2: return f"#0000{intensity:02x}"
        return self._get_color(norm_c)

    def _get_color(self, norm_val):
        if norm_val < 0.5: r, g, b = int(255 * (norm_val * 2)), 255, 0
        else: r, g, b = 255, int(255 * (1.0 - (norm_val - 0.5) * 2)), 0
        return f"#{r:02x}{g:02x}{b:02x}"

    def _get_rgb_mixed_color(self):
        if len(self.child_values) < 3: return "#888888"
        norm = lambda v: (self._safe_get(v) - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) else 0
        r, g, b = int(norm(self.child_values[0])*255), int(norm(self.child_values[1])*255), int(norm(self.child_values[2])*255)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _calculate_smart_interval(self, val_range):
        raw = val_range / 10
        exp = math.floor(math.log10(raw))
        frac = raw / (10**exp)
        if frac < 1.5: snap = 1
        elif frac < 3.5: snap = 2
        elif frac < 7.5: snap = 5
        else: snap = 10
        return snap * (10**exp)

    def _get_label_step(self, n):
        for limit, step in [(5000, 500), (1000, 200), (500, 50), (250, 20), (100, 10), (50, 5), (20, 2)]:
            if n > limit: return step
        return 1

    def _get_draw_step(self, label_step):
        for limit, step in [(500, 100), (200, 50), (50, 10), (20, 5), (10, 2), (5, 1)]:
            if label_step >= limit: return step
        return 1
