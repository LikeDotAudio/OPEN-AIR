# Core/mdp_ltp_component.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import math
import tkinter as tk

from .mdp_math import MDPMath


class MDPLTPComponent:
    """A stateful, renderable Linear Travelling Potentiometer vector object."""

    def __init__(self, canvas, widget_id, x, y, linear_var, rotation_var, config):
        self.canvas, self.widget_id, self.x, self.y = canvas, widget_id, x, y
        self.angle, self.track_len = 0.0, 200
        self.linear_var, self.rotation_var = linear_var, rotation_var

        self.val_min, self.val_max = float(config.get("value_min", 0.0)), float(config.get("value_max", 100.0))
        self.rot_min, self.rot_max = float(config.get("rotation_min", -130.0)), float(config.get("rotation_max", 130.0))
        self.cap_color, self.outline_normal, self.outline_hover = "#333", "#888", "#00ffff"
        self.highlight_color = "#00bfff"

        self.tag_root = f"mdp_ltp_{self.widget_id}"
        self.dragging = self.hovered = False
        self.start_x = self.start_y = self.start_val = self.start_rot = 0
        self.start_pos = (0, 0)

        self.linear_var.trace_add("write", lambda *a: self.render())
        self.rotation_var.trace_add("write", lambda *a: self.render())
        self.render()

    def render(self):
        self.canvas.delete(self.tag_root)
        cx, cy, ang, tl = self.x, self.y, self.angle, self.track_len
        try: v_curr, r_curr = float(self.linear_var.get()), float(self.rotation_var.get())
        except: v_curr, r_curr = self.val_min, self.rot_min

        # Hitbox
        hw = 60; hb = [MDPMath.rotate_point(cx-hw/2, cy-tl/2-20, cx, cy, ang), MDPMath.rotate_point(cx+hw/2, cy-tl/2-20, cx, cy, ang),
                       MDPMath.rotate_point(cx+hw/2, cy+tl/2+20, cx, cy, ang), MDPMath.rotate_point(cx-hw/2, cy+tl/2+20, cx, cy, ang)]
        self.canvas.create_polygon([c for p in hb for c in p], fill="", outline="", tags=(self.tag_root, "hitbox"))

        # Track
        p1, p2 = MDPMath.rotate_point(cx, cy-tl/2, cx, cy, ang), MDPMath.rotate_point(cx, cy+tl/2, cx, cy, ang)
        self.canvas.create_line(p1, p2, fill="#000", width=6, capstyle=tk.ROUND, tags=self.tag_root)
        self.canvas.create_line(p1, p2, fill="#222", width=2, capstyle=tk.ROUND, tags=self.tag_root)

        # Ticks
        for i in range(11):
            ly = (cy + tl/2) - (tl * (i/10.0)); leng = 10 if i % 5 == 0 else 5
            tp1, tp2 = MDPMath.rotate_point(cx-15, ly, cx, cy, ang), MDPMath.rotate_point(cx-15-leng, ly, cx, cy, ang)
            self.canvas.create_line(tp1, tp2, fill="#666", tags=self.tag_root)
            tp3, tp4 = MDPMath.rotate_point(cx+15, ly, cx, cy, ang), MDPMath.rotate_point(cx+15+leng, ly, cx, cy, ang)
            self.canvas.create_line(tp3, tp4, fill="#666", tags=self.tag_root)

        # Cap
        norm = (v_curr - self.val_min) / (self.val_max - self.val_min) if (self.val_max - self.val_min) else 0
        ccx, ccy = MDPMath.rotate_point(cx, (cy + tl/2) - (norm * tl), cx, cy, ang)
        r = 22; out = self.outline_hover if self.hovered else self.outline_normal
        self.canvas.create_oval(ccx-r, ccy-r, ccx+r, ccy+r, fill=self.cap_color, outline=out, width=3 if self.hovered else 2, tags=(self.tag_root, "cap"))

        # Pointer
        prad = math.radians(90 - r_curr - ang); px, py = ccx + (r-2)*math.cos(prad), ccy - (r-2)*math.sin(prad)
        self.canvas.create_line(ccx, ccy, px, py, fill=self.highlight_color, width=3, capstyle=tk.ROUND, tags=self.tag_root)
        self.canvas.create_text(ccx, ccy-35, text=f"{v_curr:.1f}", fill="white", font=("Arial", 8), tags=self.tag_root)
        self.canvas.create_text(ccx, ccy+35, text=f"R:{r_curr:.0f}", fill="#aaa", font=("Arial", 7), tags=self.tag_root)

    def set_hover(self, state):
        if self.hovered != state: self.hovered = state; self.render()

    def lift(self): self.canvas.tag_raise(self.tag_root)
