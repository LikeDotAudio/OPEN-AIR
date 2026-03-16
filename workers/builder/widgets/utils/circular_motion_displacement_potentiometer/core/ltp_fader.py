import math
import tkinter as tk
import random
from .cmdp_math import CircularMath

NEAR_RADIUS = 120
FAR_RADIUS = 380
ACCENT_COLOR = "#f4902c"

class LTPFader:
    """Represents a single fader in the circular array with self-rendering capabilities."""

    def __init__(self, canvas, widget_id, length, angle_deg, color, group_idx, label):
        self.canvas = canvas
        self.widget_id = widget_id
        self.track_len = length
        self.angle = angle_deg
        self.color_highlight = color
        self.group_index = group_idx
        self.label = label
        
        self.x, self.y = 0, 0 
        self.visible = True
        self.val_min, self.val_max = 0.0, 100.0
        self.val_current = 20 + (random.random() * 70)
        self.rot_min, self.rot_max = 0.0, 100.0
        self.rot_current = 70 + (random.random() * 20)
        
        self.tag_root = f"fader_{self.widget_id}"
        self.dragging = False
        self.hovered = False
        
        self.start_x, self.start_y = 0, 0
        self.start_val, self.start_rot = 0, 0
        
        self.update_position()
        self.render()

    def update_position(self):
        dist = NEAR_RADIUS + (self.track_len / 2)
        self.x, self.y = CircularMath.get_position(self.angle, dist)

    def render(self):
        self.canvas.delete(self.tag_root)
        if not self.visible: return

        cx, cy, ang, tl = self.x, self.y, self.angle, self.track_len
        t_ang = ang + 90
        
        # Track
        p1 = CircularMath.rotate_point(cx, cy - tl/2, cx, cy, t_ang)
        p2 = CircularMath.rotate_point(cx, cy + tl/2, cx, cy, t_ang)
        self.canvas.create_line(p1, p2, fill="#000", width=6, capstyle=tk.ROUND, tags=self.tag_root)
        self.canvas.create_line(p1, p2, fill="#222", width=2, capstyle=tk.ROUND, tags=self.tag_root)
        
        # Ticks
        for i in range(11):
            norm = i / 10.0
            local_y = (-tl/2) + (norm * tl)
            leng = 10 if i % 5 == 0 else 5
            tp1 = CircularMath.rotate_point(cx - 15, cy + local_y, cx, cy, t_ang)
            tp2 = CircularMath.rotate_point(cx - 15 - leng, cy + local_y, cx, cy, t_ang)
            self.canvas.create_line(tp1, tp2, fill="#888", width=2, tags=self.tag_root)
            tp3 = CircularMath.rotate_point(cx + 15, cy + local_y, cx, cy, t_ang)
            tp4 = CircularMath.rotate_point(cx + 15 + leng, cy + local_y, cx, cy, t_ang)
            self.canvas.create_line(tp3, tp4, fill="#888", width=2, tags=self.tag_root)

        # Cap
        norm = (self.val_current - self.val_min) / (self.val_max - self.val_min)
        ccx, ccy = CircularMath.rotate_point(cx, cy + (-tl/2 + norm * tl), cx, cy, t_ang)
        r = 22
        fill = "#555" if self.hovered else "#333"
        out = ACCENT_COLOR if self.hovered else "#888"
        self.canvas.create_oval(ccx-r, ccy-r, ccx+r, ccy+r, fill=fill, outline=out, width=4 if self.hovered else 2, tags=(self.tag_root, "cap"))
        
        # Sweep & Pointer
        deg = 225 - (self.rot_current / 100.0) * 270
        self.canvas.create_arc(ccx-r+5, ccy-r+5, ccx+r-5, ccy+r-5, start=225, extent=-(225-deg), style=tk.ARC, outline=self.color_highlight, width=4, tags=self.tag_root)
        ptr_rad = math.radians(deg)
        self.canvas.create_line(ccx, ccy, ccx + (r-2)*math.cos(ptr_rad), ccy - (r-2)*math.sin(ptr_rad), fill=self.color_highlight, width=3, tags=self.tag_root)
        
        # Values & Label
        self.canvas.create_text(ccx, ccy + 12, text=str(int(self.rot_current)), fill=self.color_highlight, font=("Arial", 9, "bold"), tags=self.tag_root)
        self.canvas.create_text(ccx, ccy - 32, text=str(int(self.val_current)), fill="#CCC", font=("Arial", 8), tags=self.tag_root)
        
        is_active = self.dragging or self.hovered
        lx, ly = (600, 450) if is_active else CircularMath.get_position(self.angle, FAR_RADIUS + 25 + (self.widget_id%2)*25)
        self.canvas.create_text(lx, ly, text=self.label, fill=self.color_highlight, font=("Arial", 12 if is_active else 10, "bold" if is_active else "normal"), tags=self.tag_root)

    def set_hover(self, state):
        if self.visible and self.hovered != state:
            self.hovered = state; self.render()

    def lift(self):
        self.canvas.tag_raise(self.tag_root)
