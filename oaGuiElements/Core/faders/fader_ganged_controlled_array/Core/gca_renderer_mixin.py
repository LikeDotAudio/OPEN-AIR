import math
import tkinter as tk
from oaGuiElements.Core.faders.fader_ganged_controlled_array.Core.gca_asset_generator import GCAAssetGenerator

class GCARendererMixin:
    """Handles the rendering engine for the GCA fader array."""

    def _get_y_from_val(self, value):
        val_range = self.max_val - self.min_val
        normalized_value = (value - self.min_val) / val_range if val_range != 0 else 0
        
        BOTTOM_MARGIN = 40
        TOP_OFFSET = 20
        draw_height = self.height - BOTTOM_MARGIN
        return TOP_OFFSET + draw_height * (1.0 - normalized_value)

    def _draw_ticks(self, width, height, offset_x=0):
        if not self.show_ticks: return
        val_range = self.max_val - self.min_val
        if val_range == 0: return
        
        tick_interval = float(self.tick_interval) if self.tick_interval else self._calculate_smart_interval(val_range)
        tick_values = []
        if tick_interval > 0:
            current_tick = math.ceil(self.min_val / tick_interval) * tick_interval
            while current_tick <= self.max_val:
                tick_values.append(current_tick)
                current_tick += tick_interval

        label_every = self._get_label_step(len(tick_values))
        draw_every = self._get_draw_step(label_every)

        for index, value in enumerate(tick_values):
            y_pos = self._get_y_from_val(value)
            if index % draw_every == 0:
                self.canvas.create_line(offset_x, y_pos, offset_x + width, y_pos, fill=self.tick_color, width=self.tick_thickness)
            
            if index % label_every == 0:
                tick_text = str(int(value)) if value == int(value) else f"{value:.1f}"
                TICK_LABEL_OFFSET_X = 5
                TICK_LABEL_OFFSET_Y = 5
                TICK_FONT_SIZE = 8
                self.canvas.create_text(offset_x + TICK_LABEL_OFFSET_X, y_pos - TICK_LABEL_OFFSET_Y, text=tick_text, fill=self.tick_color, anchor="w", font=("Arial", TICK_FONT_SIZE))
                self.canvas.create_text(offset_x + width - TICK_LABEL_OFFSET_X, y_pos - TICK_LABEL_OFFSET_Y, text=tick_text, fill=self.tick_color, anchor="e", font=("Arial", TICK_FONT_SIZE))

    def _draw_channel_lines(self, width, height, offset_x=0):
        CAP_WIDTH_OFFSET = 10
        cap_width = width - CAP_WIDTH_OFFSET
        
        S_OFFSET_X = 8
        start_x1 = offset_x + width / 2 - cap_width / 2 + S_OFFSET_X
        start_x2 = offset_x + width / 2 + cap_width / 2 - S_OFFSET_X
        strip_width = (start_x2 - start_x1) / self.num_channels
        
        CHANNEL_SLOT_Y_MARGIN = 20
        CHANNEL_SLOT_WIDTH = 10
        for index in range(self.num_channels):
            x_pos = start_x1 + (index * strip_width) + (strip_width / 2)
            self.canvas.create_rectangle(x_pos - CHANNEL_SLOT_WIDTH / 2, CHANNEL_SLOT_Y_MARGIN, 
                                         x_pos + CHANNEL_SLOT_WIDTH / 2, height - CHANNEL_SLOT_Y_MARGIN, 
                                         fill="#0a0a0a", outline="#333", width=1)
            
            INNER_LINE_OFFSET = 1
            self.canvas.create_line(x_pos - CHANNEL_SLOT_WIDTH / 2 + INNER_LINE_OFFSET, CHANNEL_SLOT_Y_MARGIN + INNER_LINE_OFFSET, 
                                   x_pos - CHANNEL_SLOT_WIDTH / 2 + INNER_LINE_OFFSET, height - (CHANNEL_SLOT_Y_MARGIN + INNER_LINE_OFFSET), fill="#000")
            self.canvas.create_line(x_pos + CHANNEL_SLOT_WIDTH / 2, CHANNEL_SLOT_Y_MARGIN, 
                                   x_pos + CHANNEL_SLOT_WIDTH / 2, height - CHANNEL_SLOT_Y_MARGIN, fill="#444")
            
            if index > 0:
                boundary_x = start_x1 + (index * strip_width)
                DASH_PATTERN = (2, 4)
                self.canvas.create_line(boundary_x, CHANNEL_SLOT_Y_MARGIN, boundary_x, height - CHANNEL_SLOT_Y_MARGIN, fill="#1a1a1a", width=1, dash=DASH_PATTERN)

    def _draw_channel_values(self, width, offset_x=0):
        CAP_WIDTH_OFFSET = 10
        cap_width = width - CAP_WIDTH_OFFSET
        
        S_OFFSET_X = 8
        start_x1 = offset_x + width / 2 - cap_width / 2 + S_OFFSET_X
        start_x2 = offset_x + width / 2 + cap_width / 2 - S_OFFSET_X
        strip_width = (start_x2 - start_x1) / self.num_channels
        
        for index in range(self.num_channels):
            current_val = self._safe_get(self.child_values[index])
            y_pos = self._get_y_from_val(current_val)
            
            val_range = self.max_val - self.min_val
            norm_val = (current_val - self.min_val) / val_range if val_range else 0
            
            center_x = start_x1 + (index * strip_width) + (strip_width / 2)
            MARKER_WIDTH_RATIO = 0.6
            marker_width = strip_width * MARKER_WIDTH_RATIO
            color = self._get_channel_color(index, norm_val)
            
            MARKER_LINE_WIDTH = 3
            self.canvas.create_line(center_x - marker_width / 2, y_pos, center_x + marker_width / 2, y_pos, fill=color, width=MARKER_LINE_WIDTH)

    def _draw_channel_labels(self, width, height, offset_x=0):
        if not self.show_channel_labels: return
        
        CAP_WIDTH_OFFSET = 10
        cap_width = width - CAP_WIDTH_OFFSET
        
        S_OFFSET_X = 8
        start_x1 = offset_x + width / 2 - cap_width / 2 + S_OFFSET_X
        start_x2 = offset_x + width / 2 + cap_width / 2 - S_OFFSET_X
        strip_width = (start_x2 - start_x1) / self.num_channels
        
        LABEL_MARGIN_Y = 10
        y_pos = height - LABEL_MARGIN_Y if self.channel_labels_pos == "bottom" else LABEL_MARGIN_Y
        anchor = "s" if self.channel_labels_pos == "bottom" else "n"
        
        for index, label in enumerate(self.channel_labels):
            x_pos = start_x1 + (index * strip_width) + (strip_width / 2)
            LABEL_FONT_SIZE = 7
            self.canvas.create_text(x_pos, y_pos, text=label, fill="white", font=("Helvetica", LABEL_FONT_SIZE, "bold"), anchor=anchor, angle=self.channel_labels_rotation)

    def _draw(self):
        if not hasattr(self, 'canvas'): return
        for item in self.canvas.find_all():
            if "panel_bg_slice" not in self.canvas.gettags(item): 
                self.canvas.delete(item)
        
        if hasattr(self.canvas, 'panel_bg_image') and not self.canvas.find_withtag("panel_bg_slice"):
            self.canvas.create_image(0, 0, image=self.canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")
            
        draw_width = self.req_width
        offset_x = (self.width - draw_width) / 2 if self.width > draw_width else 0
        canvas_height = self.height
        
        self._draw_channel_lines(draw_width, canvas_height, offset_x)
        self._draw_channel_values(draw_width, offset_x)
        self._draw_ticks(draw_width, canvas_height, offset_x)
        self._draw_channel_labels(draw_width, canvas_height, offset_x)
        
        master_val = self._safe_get(self.master_value)
        cap_y_pos = self._get_y_from_val(master_val)
        
        DEFAULT_CAP_HEIGHT = 60
        CAP_WIDTH_DECREMENT = 10
        cap_height = DEFAULT_CAP_HEIGHT
        cap_width = draw_width - CAP_WIDTH_DECREMENT 
        
        bridge_img = GCAAssetGenerator.get_3d_bridge(int(cap_width), int(cap_height), "#333333", self.accent_col)
        self.canvas.create_image(offset_x + draw_width / 2, cap_y_pos, image=bridge_img)
        self.canvas.bridge_img = bridge_img
        
        INTERIOR_MARGIN = 8
        start_x1 = offset_x + draw_width / 2 - cap_width / 2 + INTERIOR_MARGIN
        start_x2 = offset_x + draw_width / 2 + cap_width / 2 - INTERIOR_MARGIN
        start_y1 = cap_y_pos - cap_height / 2 + INTERIOR_MARGIN
        start_y2 = cap_y_pos + cap_height / 2 - INTERIOR_MARGIN
        
        if self.mode == "macro":
            self._draw_macro_view(start_x1, start_x2, start_y1, start_y2, master_val)
        else:
            self._draw_micro_view(start_x1, start_x2, start_y1, start_y2)

    def _draw_macro_view(self, start_x1, start_x2, start_y1, start_y2, master_val):
        val_range = self.max_val - self.min_val
        norm_val = (master_val - self.min_val) / val_range if val_range else 0
        
        BAR_WIDTH_RATIO = 0.9
        BAR_HEIGHT = 10
        bar_width = (start_x2 - start_x1) * BAR_WIDTH_RATIO
        bar_height = BAR_HEIGHT
        
        bar_x1, bar_x2 = (start_x1 + start_x2) / 2 - bar_width / 2, (start_x1 + start_x2) / 2 + bar_width / 2
        bar_y1, bar_y2 = (start_y1 + start_y2) / 2 - bar_height / 2, (start_y1 + start_y2) / 2 + bar_height / 2
        
        fill_color = self._get_rgb_mixed_color() if self.is_rgb else self._get_color(norm_val)
        self.canvas.create_rectangle(bar_x1, bar_y1, bar_x2, bar_y2, fill=fill_color, outline="")
        
        display_text = f"{int(master_val)}" if master_val == int(master_val) else f"{master_val:.1f}"
        TEXT_OFFSET_Y = 15
        FONT_SIZE_MAIN = 8
        FONT_SIZE_SUB = 7
        self.canvas.create_text((start_x1 + start_x2) / 2, (start_y1 + start_y2) / 2 + TEXT_OFFSET_Y, text=display_text, fill="white", font=("Helvetica", FONT_SIZE_MAIN, "bold"))
        self.canvas.create_text((start_x1 + start_x2) / 2, (start_y1 + start_y2) / 2 - TEXT_OFFSET_Y, text="MIX" if self.is_rgb else "AVG", fill=self.accent_col, font=("Helvetica", FONT_SIZE_SUB, "bold"))

    def _draw_micro_view(self, start_x1, start_x2, start_y1, start_y2):
        strip_width = (start_x2 - start_x1) / self.num_channels
        for index in range(self.num_channels):
            child_val = self._safe_get(self.child_values[index])
            val_range = self.max_val - self.min_val
            norm_child = (child_val - self.min_val) / val_range if val_range else 0
            
            x1, x2 = start_x1 + index * strip_width + 1, start_x1 + (index + 1) * strip_width - 1
            fill_height = norm_child * (start_y2 - start_y1)
            
            self.canvas.create_rectangle(x1, start_y1, x2, start_y2, fill="#111111", outline="")
            
            channel_color = self._get_channel_color(index, norm_child)
            self.canvas.create_rectangle(x1, start_y2 - fill_height, x2, start_y2, fill=channel_color, outline="")
            
            LABEL_OFFSET_Y = 5
            MICRO_FONT_SIZE = 6
            self.canvas.create_text((x1 + x2) / 2, start_y2 - LABEL_OFFSET_Y, text=f"{index + 1}", fill="white", font=("Arial", MICRO_FONT_SIZE), anchor="s")

    def _get_channel_color(self, index, normalized_color):
        if self.is_rgb:
            MIN_RGB_INTENSITY = 50
            MAX_RGB_VAL = 255
            intensity = max(0, min(255, int(max(MIN_RGB_INTENSITY, normalized_color * MAX_RGB_VAL))))
            if index == 0: return f"#{intensity:02x}0000"
            if index == 1: return f"#00{intensity:02x}00"
            if index == 2: return f"#0000{intensity:02x}"
        return self._get_color(normalized_color)

    def _get_color(self, norm_val):
        MAX_RGB_VAL = 255
        COLOR_SPLIT_THRESHOLD = 0.5
        if norm_val < COLOR_SPLIT_THRESHOLD: 
            red = max(0, min(255, int(MAX_RGB_VAL * (norm_val * 2))))
            green, blue = MAX_RGB_VAL, 0
        else: 
            red = MAX_RGB_VAL
            green = max(0, min(255, int(MAX_RGB_VAL * (1.0 - (norm_val - COLOR_SPLIT_THRESHOLD) * 2))))
            blue = 0
        return f"#{red:02x}{green:02x}{blue:02x}"


    def _get_rgb_mixed_color(self):
        MIN_RGB_CHANNELS = 3
        if len(self.child_values) < MIN_RGB_CHANNELS: return "#888888"
        
        val_range = self.max_val - self.min_val
        normalize = lambda v: (self._safe_get(v) - self.min_val) / val_range if val_range else 0
        
        MAX_RGB_VAL = 255
        red = max(0, min(255, int(normalize(self.child_values[0]) * MAX_RGB_VAL)))
        green = max(0, min(255, int(normalize(self.child_values[1]) * MAX_RGB_VAL)))
        blue = max(0, min(255, int(normalize(self.child_values[2]) * MAX_RGB_VAL)))
        return f"#{red:02x}{green:02x}{blue:02x}"

    def _calculate_smart_interval(self, val_range):
        DIVISOR = 10
        raw_interval = val_range / DIVISOR
        exponent = math.floor(math.log10(raw_interval))
        fractional_part = raw_interval / (10**exponent)
        
        if fractional_part < 1.5: snap_val = 1
        elif fractional_part < 3.5: snap_val = 2
        elif fractional_part < 7.5: snap_val = 5
        else: snap_val = 10
        return snap_val * (10**exponent)

    def _get_label_step(self, num_ticks):
        # Configuration for label density
        STEPS_CONFIG = [
            (5000, 500), (1000, 200), (500, 50), 
            (250, 20), (100, 10), (50, 5), (20, 2)
        ]
        for limit, step in STEPS_CONFIG:
            if num_ticks > limit: return step
        return 1

    def _get_draw_step(self, label_step):
        # Configuration for sub-tick density
        DRAW_STEPS_CONFIG = [
            (500, 100), (200, 50), (50, 10), 
            (20, 5), (10, 2), (5, 1)
        ]
        for limit, step in DRAW_STEPS_CONFIG:
            if label_step >= limit: return step
        return 1
