# workers/builder/circular_motion_displacement_potentiometer/cmdp_channel_handler.py
import tkinter as tk
import math
from loguru import logger

# --- Constants ---
PERCENT_MAX = 100.0
HITBOX_WIDTH = 60
HITBOX_PADDING = 20
TICK_COUNT = 11
TICK_DIVISOR = 10.0
TICK_INNER_OFFSET = 15
TICK_OUTER_OFFSET = 25
CAP_RADIUS = 22
TRACK_WIDTH_OUTER = 6
TRACK_WIDTH_INNER = 2
POTENTIOMETER_START_ANGLE = 225
POTENTIOMETER_EXTENT_MAX = 270
LABEL_OFFSET_BASE = 25
LABEL_OFFSET_STEP = 25
DEFAULT_TRACK_LENGTH = 260

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
        self.x, self.y, self.track_len = 0, 0, DEFAULT_TRACK_LENGTH
        self.visible, self.val_min, self.val_max, self.rot_min, self.rot_max = True, 0.0, PERCENT_MAX, 0.0, PERCENT_MAX
        self.cap_color, self.cap_outline_normal, self.cap_outline_hover = "#333333", "#888888", "#f4902c"
        self.tag_root = f"cmdp_fader_{self.widget_id}"
        self.dragging, self.hovered = False, False
        self.start_x, self.start_y, self.start_val, self.start_rot = 0, 0, 0, 0
        
        # Local traces for visual updates
        self.val_var.trace_add("write", lambda *a: self.render_fader_visuals())
        self.rot_var.trace_add("write", lambda *a: self.render_fader_visuals())
        self.angle_var.trace_add("write", lambda *a: self.update_position_and_render())
        self.mute_var.trace_add("write", lambda *a: self.render_fader_visuals())
        
        self.update_position()
        self.render_fader_visuals()

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
        center_x, center_y = self.widget_ref.center_x, self.widget_ref.center_y
        self.x = center_x + dist * math.cos(rad)
        self.y = center_y + dist * math.sin(rad)

    def update_position_and_render(self):
        """
        ⚡ ORCHESTRATOR: Recomputes coordinates and then pushes state to canvas.
        Refactored for Modular SRP.
        """
        # SRP REFACTOR: Step 1 - Recompute geometry
        self.update_position()
        
        # SRP REFACTOR: Step 2 - Push to canvas
        self.render_fader_visuals()

    def calculate_rotated_point(self, px, py, cx, cy, cos_a, sin_a):
        """Vectorized point rotation using pre-calculated trig values."""
        delta_x, delta_y = px - cx, py - cy
        return cos_a * delta_x - sin_a * delta_y + cx, sin_a * delta_x + cos_a * delta_y + cy

    def render_fader_visuals(self):
        """
        ⚡ RENDER ONLY: Strictly pushes the current state to the canvas.
        No state computation or coordinate logic should live here.
        """
        self.canvas.delete(self.tag_root)
        if not self.visible or self.mute_var.get(): return
        
        center_x, center_y = self.x, self.y
        try:
            ang, val_curr, rot_curr = float(self.angle_var.get()), float(self.val_var.get()), float(self.rot_var.get())
        except Exception as e:
            logger.error(f"Failed to get float values for rendering: {e}")
            ang, val_curr, rot_curr = 0.0, 0.0, 0.0
            
        track_length, t_ang_rad = self.track_len, math.radians(ang + 90)
        cos_t, sin_t = math.cos(t_ang_rad), math.sin(t_ang_rad)
        
        # Hitbox (for click detection)
        hitbox_width = HITBOX_WIDTH
        hitbox_points = [self.calculate_rotated_point(center_x - hitbox_width/2, center_y - track_length/2 - HITBOX_PADDING, center_x, center_y, cos_t, sin_t),
               self.calculate_rotated_point(center_x + hitbox_width/2, center_y - track_length/2 - HITBOX_PADDING, center_x, center_y, cos_t, sin_t),
               self.calculate_rotated_point(center_x + hitbox_width/2, center_y + track_length/2 + HITBOX_PADDING, center_x, center_y, cos_t, sin_t),
               self.calculate_rotated_point(center_x - hitbox_width/2, center_y + track_length/2 + HITBOX_PADDING, center_x, center_y, cos_t, sin_t)]
        
        flat_hitbox_points = [coord for point in hitbox_points for coord in point]
        self.canvas.create_polygon(flat_hitbox_points, fill="", outline="", tags=(self.tag_root, "hitbox"))

        # Track & Ticks
        track_start = self.calculate_rotated_point(center_x, center_y - track_length/2, center_x, center_y, cos_t, sin_t)
        track_end = self.calculate_rotated_point(center_x, center_y + track_length/2, center_x, center_y, cos_t, sin_t)
        self.canvas.create_line(track_start, track_end, fill="#000000", width=TRACK_WIDTH_OUTER, capstyle=tk.ROUND, tags=self.tag_root)
        self.canvas.create_line(track_start, track_end, fill="#222222", width=TRACK_WIDTH_INNER, capstyle=tk.ROUND, tags=self.tag_root)
        
        # Batch draw ticks (Reduced complexity)
        for i in range(TICK_COUNT):
            local_y = (-track_length/2) + ((i/TICK_DIVISOR) * track_length)
            tick_start = self.calculate_rotated_point(center_x - TICK_INNER_OFFSET, center_y + local_y, center_x, center_y, cos_t, sin_t)
            tick_end = self.calculate_rotated_point(center_x - TICK_OUTER_OFFSET, center_y + local_y, center_x, center_y, cos_t, sin_t)
            self.canvas.create_line(tick_start, tick_end, fill="#888888", width=TRACK_WIDTH_INNER, tags=self.tag_root)

        # Cap & Potentiometer
        denom = (self.val_max - self.val_min)
        v_norm = (val_curr - self.val_min) / denom if denom != 0 else 0
        cap_center_x, cap_center_y = self.calculate_rotated_point(center_x, center_y + (-track_length/2) + (v_norm * track_length), center_x, center_y, cos_t, sin_t)
        radius = CAP_RADIUS
        
        is_active = self.dragging or self.hovered
        outline_color, fill_color = (self.cap_outline_hover if is_active else self.cap_outline_normal), ("#555555" if is_active else self.cap_color)
        self.canvas.create_oval(cap_center_x-radius, cap_center_y-radius, cap_center_x+radius, cap_center_y+radius, fill=fill_color, outline=outline_color, width=2, tags=(self.tag_root, "cap"))
        
        # Fixed South orientation for pot gap
        pot_degree = POTENTIOMETER_START_ANGLE - (rot_curr / PERCENT_MAX) * POTENTIOMETER_EXTENT_MAX
        self.canvas.create_arc(cap_center_x-radius+5, cap_center_y-radius+5, cap_center_x+radius-5, cap_center_y+radius-5, start=POTENTIOMETER_START_ANGLE, extent=-(POTENTIOMETER_START_ANGLE-pot_degree), style=tk.ARC, outline=self.color_highlight, width=4, tags=self.tag_root)
        
        pot_rad = math.radians(pot_degree)
        pointer_x, pointer_y = cap_center_x + (radius-2) * math.cos(pot_rad), cap_center_y - (radius-2) * math.sin(pot_rad) 
        self.canvas.create_line(cap_center_x, cap_center_y, pointer_x, pointer_y, fill=self.color_highlight, width=3, tags=self.tag_root)
        
        # Label logic
        global_center_x, global_center_y = self.widget_ref.center_x, self.widget_ref.center_y
        if is_active:
            label_x, label_y, font_spec = global_center_x, global_center_y, ("Arial", 12, "bold")
        else:
            label_dist = self.widget_ref.far_radius + LABEL_OFFSET_BASE + (self.widget_id % 2) * LABEL_OFFSET_STEP
            label_rad = math.radians(ang)
            label_x, label_y, font_spec = global_center_x + label_dist * math.cos(label_rad), global_center_y + label_dist * math.sin(label_rad), ("Arial", 10)
            
        self.canvas.create_text(label_x, label_y, text=self.label, fill=self.color_highlight, font=font_spec, tags=self.tag_root)

    def set_hover(self, state):
        if self.visible and self.hovered != state:
            self.hovered = state
            self.render_fader_visuals()

    def raise_fader_to_top(self):
        self.canvas.tag_raise(self.tag_root)
