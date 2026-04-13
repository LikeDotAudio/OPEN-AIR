# Core/fader_bar_renderer_mixin.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from .fader_bar_asset_generator import FaderBarAssetGenerator
from oaGuiBuilder.Core.ui_geometry_math import UIGeometryMath

class FaderBarRendererMixin:
    """Handles static and dynamic rendering for the Fader with dual Bar Graphs."""

    def _draw_static(self):
        self.canvas.delete("static")
        w, h = self.width, self.height
        
        if hasattr(self.canvas, 'panel_bg_image') and self.canvas.panel_bg_image:
            self.canvas.create_image(0, 0, image=self.canvas.panel_bg_image, anchor="nw", tags="static")

        meter_w, pad = self.meter_width, self.bar_padding
        self.top_m, self.bot_m = 25, 25
        self.draw_h = h - (self.top_m + self.bot_m)
        
        f_w = int(self.widget_config.get("fader_width", w - (meter_w * 2) - (pad * 2) if self.enable_meters else w - (pad * 2)))
        f_w = max(10, f_w)
        
        if self.enable_meters:
            total_w = (meter_w * 2) + (pad * 2) + f_w
            self.x_left = (w - total_w) / 2
            self.x_fader = self.x_left + meter_w + pad
            self.x_right = self.x_fader + f_w + pad
            
            for x in [self.x_left, self.x_right]:
                self.canvas.create_rectangle(x, self.top_m, x+meter_w, self.top_m+self.draw_h, fill="#0a0a0a", outline="#333", tags="static")
                self.canvas.create_line(x+1, self.top_m+1, x+meter_w-1, self.top_m+1, fill="#000", tags="static")
                self.canvas.create_line(x+1, self.top_m+1, x+1, self.top_m+self.draw_h-1, fill="#000", tags="static")
        else:
            self.x_fader = (w - f_w) / 2

        self.cx = self.x_fader + f_w/2
        self.canvas.create_rectangle(self.cx-5, self.top_m-5, self.cx+5, self.top_m+self.draw_h+5, fill="#0a0a0a", outline="#333", tags="static")
        self.canvas.create_line(self.cx-4, self.top_m-4, self.cx-4, self.top_m+self.draw_h+4, fill="#000", tags="static")
        
        if self.show_ticks and self.enable_meters:
            for i in range(self.tick_steps + 1):
                norm = i/self.tick_steps; ty = self.top_m + (self.draw_h * (1.0 - norm))
                self.canvas.create_line(self.x_left, ty, self.x_left-5, ty, fill="gray", tags="static")
                self.canvas.create_line(self.x_right+meter_w, ty, self.x_right+meter_w+5, ty, fill="gray", tags="static")
                if i % 2 == 0: self.canvas.create_text(self.x_left-7, ty, text=f"{int(self.min_val+norm*(self.max_val-self.min_val))}", fill="gray", font=("Arial", 7), anchor="e", tags="static")

    def _draw_dynamic(self):
        self.canvas.delete("dynamic")
        if self.enable_meters:
            self._update_meter("left"); self._update_meter("right")
            
        cap_h = self.cap_height
        f_w = int(self.widget_config.get("fader_width", 40))
        cap_w = self.widget_config.get("cap_width", f_w + (self.meter_width * 2) + (self.bar_padding * 2) + 4)
        
        self.cap_img = FaderBarAssetGenerator.get_3d_cap(int(cap_w), int(cap_h), self.fader_grip_color, self.fader_track_color)
        value = self.fader_var.get()
        # Use centralized geometry math for value-to-pixel mapping
        y = self.top_m + UIGeometryMath.value_to_pixel(value, self.min_val, self.max_val, self.draw_h, reverse=True)
        self.canvas.create_image(self.cx, y, image=self.cap_img, tags=("dynamic", "cap"))
        
        text_col = "white" if self.fader_grip_color.lower() in ["black", "#000000", "#222222"] else "black"
        self.canvas.create_text(self.cx, y, text=f"{value:.1f}", fill=text_col, font=("Arial", 7, "bold"), tags=("dynamic", "cap_text"))

    def _update_meter(self, side):
        tag = f"fill_{side}"
        self.canvas.delete(tag)
        x = self.x_left if side == "left" else self.x_right
        value = self.left_var.get() if side == "left" else self.right_var.get()
        style = self.left_style if side == "left" else self.right_style
        
        meter_w = self.meter_width
        # Use centralized geometry math for value-to-pixel mapping
        val_h = UIGeometryMath.value_to_pixel(value, self.min_val, self.max_val, self.draw_h)
        fy = self.top_m + (self.draw_h - val_h)
        
        # Ranges
        s1, s2 = self.draw_h * 0.4, self.draw_h * 0.2
        ranges = [ (max(fy, self.top_m + s1), self.top_m + self.draw_h, style.get("lower_range_colour", "#00ff00")),
                   (max(fy, self.top_m + s2), min(self.top_m + s1, self.top_m + self.draw_h), style.get("middle_range_colour", "#ffff00")),
                   (max(fy, self.top_m), min(self.top_m + s2, self.top_m + self.draw_h), style.get("upper_range_colour", "#ff0000")) ]
        
        for g1, g2, col in ranges:
            if g2 > g1: self.canvas.create_rectangle(x+1, g1, x+meter_w-1, g2, fill=col, outline="", tags=("dynamic", tag))