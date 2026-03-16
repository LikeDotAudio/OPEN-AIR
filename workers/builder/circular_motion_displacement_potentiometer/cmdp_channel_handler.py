# workers/builder/circular_motion_displacement_potentiometer/cmdp_channel_handler.py
import tkinter as tk
import math
from loguru import logger

class CMDP_LTPObject:
    """
    Circular/Composite Motion Draggable Potentiometer Object.
    Handles rendering and interaction for a single fader in the CMDP array.
    Refactored for Modular SRP: Separates Coordinate Math from Canvas Rendering.
    """
    def __init__(self, canvas, widget_id, color, group_idx, label, 
                 val_var, rot_var, angle_var, mute_var, on_change_cb, widget_ref):
        self.canvas, self.widget_id, self.color_highlight, self.group_index, self.label = canvas, widget_id, color, group_idx, label
        self.on_change_cb, self.widget_ref = on_change_cb, widget_ref
        self.val_var, self.rot_var, self.angle_var, self.mute_var = val_var, rot_var, angle_var, mute_var
        
        self.group_name = "Default"
        self.x, self.y, self.track_len = 0, 0, 260
        self.visible, self.val_min, self.val_max, self.rot_min, self.rot_max = True, 0.0, 100.0, 0.0, 100.0
        self.cap_color, self.cap_outline_normal, self.cap_outline_hover = "#333333", "#888888", "#f4902c"
        self.tag_root = f"cmdp_fader_{self.widget_id}"
        self.dragging, self.hovered = False, False
        self.start_x, self.start_y, self.start_val, self.start_rot = 0, 0, 0, 0
        
        # Local traces for visual updates
        self.val_var.trace_add("write", lambda *a: self.render())
        self.rot_var.trace_add("write", lambda *a: self.render())
        self.angle_var.trace_add("write", lambda *a: self.update_position_and_render())
        self.mute_var.trace_add("write", lambda *a: self.render())
        
        self.update_position()
        self.render()

    def update_position(self):
        """
        ⚡ MATH ONLY: Calculates new physical coordinates based on state variables.
        """
        try: angle = float(self.angle_var.get())
        except Exception as e:
            logger.error(f"Failed to get float angle from {self.angle_var}: {e}")
            angle = 0.0
        rad = math.radians(angle)
        near, far = self.widget_ref.near_radius, self.widget_ref.far_radius
        self.track_len = far - near
        dist = near + (self.track_len / 2)
        cx, cy = self.widget_ref.center_x, self.widget_ref.center_y
        self.x = cx + dist * math.cos(rad)
        self.y = cy + dist * math.sin(rad)

    def update_position_and_render(self):
        """
        ⚡ ORCHESTRATOR: Recomputes coordinates and then pushes state to canvas.
        Refactored for Modular SRP.
        """
        # SRP REFACTOR: Step 1 - Recompute geometry
        self.update_position()
        
        # SRP REFACTOR: Step 2 - Push to canvas
        self.render()

    def rotate_point(self, px, py, cx, cy, cos_a, sin_a):
        """Vectorized point rotation using pre-calculated trig values."""
        dx, dy = px - cx, py - cy
        return cos_a * dx - sin_a * dy + cx, sin_a * dx + cos_a * dy + cy

    def render(self):
        """
        ⚡ RENDER ONLY: Strictly pushes the current state to the canvas.
        No state computation or coordinate logic should live here.
        """
        self.canvas.delete(self.tag_root)
        if not self.visible or self.mute_var.get(): return
        
        cx, cy = self.x, self.y
        try:
            ang, val_curr, rot_curr = float(self.angle_var.get()), float(self.val_var.get()), float(self.rot_var.get())
        except Exception as e:
            logger.error(f"Failed to get float values for rendering: {e}")
            ang, val_curr, rot_curr = 0.0, 0.0, 0.0
            
        tl, t_ang_rad = self.track_len, math.radians(ang + 90)
        cos_t, sin_t = math.cos(t_ang_rad), math.sin(t_ang_rad)
        
        # Hitbox (for click detection)
        hb_w = 60
        hbp = [self.rotate_point(cx - hb_w/2, cy - tl/2 - 20, cx, cy, cos_t, sin_t),
               self.rotate_point(cx + hb_w/2, cy - tl/2 - 20, cx, cy, cos_t, sin_t),
               self.rotate_point(cx + hb_w/2, cy + tl/2 + 20, cx, cy, cos_t, sin_t),
               self.rotate_point(cx - hb_w/2, cy + tl/2 + 20, cx, cy, cos_t, sin_t)]
        
        flat_hbp = [c for pt in hbp for c in pt]
        self.canvas.create_polygon(flat_hbp, fill="", outline="", tags=(self.tag_root, "hitbox"))

        # Track & Ticks
        p1 = self.rotate_point(cx, cy - tl/2, cx, cy, cos_t, sin_t)
        p2 = self.rotate_point(cx, cy + tl/2, cx, cy, cos_t, sin_t)
        self.canvas.create_line(p1, p2, fill="#000000", width=6, capstyle=tk.ROUND, tags=self.tag_root)
        self.canvas.create_line(p1, p2, fill="#222222", width=2, capstyle=tk.ROUND, tags=self.tag_root)
        
        # Batch draw ticks (Reduced complexity)
        for i in range(11):
            ly = (-tl/2) + ((i/10.0) * tl)
            tp1 = self.rotate_point(cx - 15, cy + ly, cx, cy, cos_t, sin_t)
            tp2 = self.rotate_point(cx - 25, cy + ly, cx, cy, cos_t, sin_t)
            self.canvas.create_line(tp1, tp2, fill="#888888", width=2, tags=self.tag_root)

        # Cap & Potentiometer
        denom = (self.val_max - self.val_min)
        v_norm = (val_curr - self.val_min) / denom if denom != 0 else 0
        ccx, ccy = self.rotate_point(cx, cy + (-tl/2) + (v_norm * tl), cx, cy, cos_t, sin_t)
        r = 22
        
        is_a = self.dragging or self.hovered
        oc, fc = (self.cap_outline_hover if is_a else self.cap_outline_normal), ("#555555" if is_a else self.cap_color)
        self.canvas.create_oval(ccx-r, ccy-r, ccx+r, ccy+r, fill=fc, outline=oc, width=2, tags=(self.tag_root, "cap"))
        
        # Fixed South orientation for pot gap
        ld = 225 - (rot_curr / 100.0) * 270
        self.canvas.create_arc(ccx-r+5, ccy-r+5, ccx+r-5, ccy+r-5, start=225, extent=-(225-ld), style=tk.ARC, outline=self.color_highlight, width=4, tags=self.tag_root)
        
        pr_rad = math.radians(ld)
        px, py = ccx + (r-2) * math.cos(pr_rad), ccy - (r-2) * math.sin(pr_rad) 
        self.canvas.create_line(ccx, ccy, px, py, fill=self.color_highlight, width=3, tags=self.tag_root)
        
        # Label logic
        gcx, gcy = self.widget_ref.center_x, self.widget_ref.center_y
        if is_a:
            lx, ly, fs = gcx, gcy, ("Arial", 12, "bold")
        else:
            ldist = self.widget_ref.far_radius + 25 + (self.widget_id % 2) * 25
            l_rad = math.radians(ang)
            lx, ly, fs = gcx + ldist * math.cos(l_rad), gcy + ldist * math.sin(l_rad), ("Arial", 10)
            
        self.canvas.create_text(lx, ly, text=self.label, fill=self.color_highlight, font=fs, tags=self.tag_root)

    def set_hover(self, state):
        if self.visible and self.hovered != state:
            self.hovered = state
            self.render()

    def lift(self):
        self.canvas.tag_raise(self.tag_root)
