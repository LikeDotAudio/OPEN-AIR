import tkinter as tk
from oaGuiElements.faders.fader.core.scale import ScaleDrawer
from oaGuiElements.faders.fader.core.track import TrackDrawer
from oaGuiElements.faders.fader.core.cap import CapDrawer

class FaderRendererMixin:
    """Handles static and dynamic drawing operations for the fader."""

    def _sync_fader_cap_position(self, width, height, value):
        if not self.canvas.find_withtag("fader_cap"): return
        
        scale = float(self.fader_cap_scale)
        cap_h = int((float(self.cap_height_override) if self.cap_height_override else 50.0) * scale)
        padding = cap_h / 2.0
        top_res, bot_res = 25.0, 20.0
        f_h = float(height) - top_res - bot_res - (2.0 * padding)
        
        norm = (value - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) != 0 else 0
        disp_norm = max(0.0, min(1.0, norm)) ** (1.0 / self.log_exponent) if self.log_exponent != 1.0 else norm
        hy = f_h * (1.0 - disp_norm) + top_res + padding
        cx = float(width) / 2.0
        
        self.canvas.coords("fader_cap", cx, hy)
        
        if self.is_sliding:
            txt = f"{value:.1f}" if value != int(value) else f"{int(value)}"
            self.canvas.itemconfig("floating_val", text=txt, state="normal")
            self.canvas.coords("floating_val", cx, hy - 10)
        else:
            self.canvas.itemconfig("floating_val", state="hidden")
            
        if self.show_value:
            val_str = f"{value:.1f}" if value != int(value) else f"{int(value)}"
            if self.show_units and self.unit_text:
                val_str = f"{val_str} {self.unit_text}" if self.unit_position == "right" else f"{self.unit_text} {val_str}"
            self.canvas.itemconfig("static_readout", text=val_str)

    def _draw_fader(self, width, height, value):
        if not self.canvas.winfo_exists(): return
        width, height = float(width), float(height)
        if width <= 1 or height <= 1: return
        
        # ⚡ INDUSTRIAL TRANSPARENCY: Preserve the patina slice
        for item in self.canvas.find_all():
            tags = self.canvas.gettags(item)
            if "panel_bg_slice" not in tags:
                self.canvas.delete(item)
        
        # 0. Draw Industrial Background (Fallback)
        if hasattr(self.canvas, 'panel_bg_image') and not self.canvas.find_withtag("panel_bg_slice"):
            self.canvas.create_image(0, 0, image=self.canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")
            
        cx = width / 2.0
        t_col = self.fader_track_color
        scale = float(self.fader_cap_scale)
        cap_w = int((float(self.cap_width_override) if self.cap_width_override else 40.0) * scale)
        cap_h = int((float(self.cap_height_override) if self.cap_height_override else 50.0) * scale)
        padding = cap_h / 2.0
        top_res, bot_res = 25.0, 20.0
        u_h = height - top_res - bot_res
        
        if self.label_text:
            self.canvas.create_text(cx, 12, text=self.label_text, fill=self.label_color, font=("Helvetica", 10, "bold"), anchor="n", tags="static")
            
        TrackDrawer.draw(self.canvas, self, cx, top_res + padding, height - bot_res, 10, hover_color=self.track_hover_color if self.is_hovered else None)
        
        f_h = u_h - (2.0 * padding)
        layout = {
            'cx': cx,
            'available_height': f_h,
            'padding': top_res + padding,
            'tick_length_half': width * self.tick_size,
            'slot_w': 10,
            'cap_width': cap_w
        }
        ScaleDrawer.draw(self.canvas, self, width, height - bot_res, layout)
        
        norm = (value - self.min_val) / (self.max_val - self.min_val) if (self.max_val - self.min_val) != 0 else 0
        disp_norm = max(0.0, min(1.0, norm)) ** (1.0 / self.log_exponent) if self.log_exponent != 1.0 else norm
        hy = f_h * (1.0 - disp_norm) + top_res + padding
        
        cap_img = CapDrawer.get_3d_fader_cap(cap_w, cap_h, self.cap_color, t_col, highlight_color=self.cap_highlight_color)
        self.canvas.create_image(cx, hy, image=cap_img, tags="fader_cap")
        self.canvas.cap_img = cap_img 
        
        self.canvas.create_text(cx, hy - 10, text="", fill="#FFFFFF", font=("Helvetica", 7, "bold"), tags="floating_val", anchor="s", state="hidden")
        
        if self.show_value:
            val_str = f"{value:.1f}" if value != int(value) else f"{int(value)}"
            if self.show_units and self.unit_text:
                val_str = f"{val_str} {self.unit_text}" if self.unit_position == "right" else f"{self.unit_text} {val_str}"
            self.canvas.create_text(cx, height - 10, text=val_str, fill=self.value_highlight_color, font=("Helvetica", 8), anchor="s", tags="static_readout")
