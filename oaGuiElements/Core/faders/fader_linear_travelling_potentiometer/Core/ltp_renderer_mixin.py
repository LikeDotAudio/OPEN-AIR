# Core/ltp_renderer_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk

from oaGuiElements.Core.Knobs.knob.Core.knob_renderer import _draw_pointer

from ...fader.Core.scale import ScaleDrawer
from ...fader.Core.track import TrackDrawer
from .ltp_asset_generator import LTPAssetGenerator


class LTPRendererMixin:
    """Handles the rendering logic for the combined Linear/Rotary Potentiometer."""

    def _get_handle_pos(self, length):
        norm = max(0.0, min(1.0, (self.linear_var.get() - self.min_val) / (self.max_val - self.min_val))) if (self.max_val - self.min_val) != 0 else 0
        d_norm = norm ** (1.0 / self.log_exponent)
        padding_edge = 25
        return (length - 50) * (1.0 - d_norm if self.orientation == "vertical" else d_norm) + padding_edge

    def redraw(self, canvas, args=None):
        cw, ch = canvas.winfo_width(), canvas.winfo_height()
        if cw <= 1: return
        self.orientation = "horizontal" if cw > ch else "vertical"

        for item in canvas.find_all():
            if "panel_bg_slice" not in canvas.gettags(item): canvas.delete(item)

        if hasattr(canvas, 'panel_bg_image') and not canvas.find_withtag("panel_bg_slice"):
            canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")

        cx, cy = cw / 2.0, ch / 2.0
        top_res, bot_res = 25.0, 25.0

        if self.orientation == "vertical":
            TrackDrawer.draw(canvas, self, cx, top_res, ch, 10, hover_color=self.track_hover_color if self.is_hovered else None)

            layout = {
                'cx': cx,
                'available_height': ch - top_res - bot_res,
                'padding': top_res,
                'tick_length_half': cw * self.tick_size,
                'slot_w': 10,
                'cap_width': self.cap_radius * 2
            }
            ScaleDrawer.draw(canvas, self, cw, ch, layout)

            h_pos = self._get_handle_pos(ch)
            canvas.create_line(cx, ch - bot_res, cx, h_pos, fill=self.value_highlight_color, width=2, capstyle=tk.ROUND, tags="fill_line")
            self._draw_knob_on_handle(canvas, cx, h_pos)
        else:
            TrackDrawer.draw_horizontal(canvas, self, cy, top_res, cw, 10, hover_color=self.track_hover_color if self.is_hovered else None)
            geo = {
                'width': cw, 'height': ch, 'cy': cy,
                'available_width': cw - top_res - bot_res,
                'padding': top_res, 'tick_length_half': ch * self.tick_size,
                'slot_height': 10, 'cap_width': self.cap_radius*2
            }
            ScaleDrawer.draw_horizontal(canvas, self, geo)
            h_pos = self._get_handle_pos(cw)
            canvas.create_line(top_res, cy, h_pos, cy, fill=self.value_highlight_color, width=2, capstyle=tk.ROUND, tags="fill_line")
            self._draw_knob_on_handle(canvas, h_pos, cy)

    def _draw_knob_on_handle(self, canvas, x, y):
        img = LTPAssetGenerator.get_3d_knob(self.cap_radius, self.cap_color, self.cap_outline_color, shape=self.knob_shape, teeth=self.knob_teeth)
        canvas.create_image(x, y, image=img, tags="handle")
        canvas.handle_img = img

        norm_rot = (self.rotation_var.get() - self.rotation_min) / (self.rotation_max - self.rotation_min) if (self.rotation_max - self.rotation_min) else 0.5
        angle = 225 - (norm_rot * 270)
        _draw_pointer(canvas, x, y, self.cap_radius, self.arc_width, angle, self.pointer_style, self.accent_color, self.pointer_length, self.pointer_offset, self.no_center)

        if self.show_value:
            txt = f"{self.linear_var.get():.1f}"
            if self.show_units: txt += f" {self.unit_text}"
            canvas.create_text(x, y + self.cap_radius + 15, text=txt, fill=self.value_color, font=("Arial", 8, "bold"), tags="value")
