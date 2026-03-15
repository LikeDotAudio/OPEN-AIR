import tkinter as tk
from ...fader.core.scale import ScaleDrawer
from ...fader.core.track import TrackDrawer
from ...knob.core.knob_renderer import _draw_track, _draw_pointer
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
            ScaleDrawer.draw(canvas, self, cw, ch, cx, ch - top_res - bot_res, top_res, cw * self.tick_size, 10, cap_width=self.cap_radius*2)
            h_pos = self._get_handle_pos(ch)
            canvas.create_line(cx, ch - bot_res, cx, h_pos, fill=self.value_highlight_color, width=2, capstyle=tk.ROUND, tags="fill_line")
            self._draw_knob_on_handle(canvas, cx, h_pos)
        else:
            TrackDrawer.draw_horizontal(canvas, self, cy, top_res, cw, 10, hover_color=self.track_hover_color if self.is_hovered else None)
            ScaleDrawer.draw_horizontal(canvas, self, cw, ch, cy, cw - top_res - bot_res, top_res, ch * self.tick_size, 10, cap_width=self.cap_radius*2)
            h_pos = self._get_handle_pos(cw)
            canvas.create_line(top_res, cy, h_pos, cy, fill=self.value_highlight_color, width=2, capstyle=tk.ROUND, tags="fill_line")
            self._draw_knob_on_handle(canvas, h_pos, cy)

    def _draw_knob_on_handle(self, canvas, x, y):
        img = LTPAssetGenerator.get_3d_knob(self.cap_radius, self.cap_color, self.cap_outline_color, shape=self.knob_shape, teeth=self.knob_teeth)
        canvas.create_image(x, y, image=img, tags="handle")
        canvas.handle_img = img 
        
        norm_rot = (self.rotation_var.get() - self.rotation_min) / (self.rotation_max - self.rotation_min) if (self.rotation_max - self.rotation_min) else 0.5
        angle = 225 - (norm_rot * 270)
        _draw_pointer(canvas, x, y, self.cap_radius, angle, self.accent_color, self.pointer_style)
        
        if self.show_value:
            txt = f"{self.linear_var.get():.1f}"
            if self.show_units: txt += f" {self.unit_text}"
            canvas.create_text(x, y + self.cap_radius + 15, text=txt, fill=self.value_color, font=("Arial", 8, "bold"), tags="value")
