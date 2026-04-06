# Core/ltp_fader.py
from oaGuiFramework.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import math
import tkinter as tk
import random
from .cmdp_math import CircularMath

# Radius and Distance Constants
NEAR_RADIUS = 120
FAR_RADIUS = 380
RADIUS_DIVISOR = 2
CENTER_DIVISOR = 2
TRACK_OFFSET_RADIUS = NEAR_RADIUS

# Color and Style Constants
ACCENT_COLOR = "#f4902c"
TRACK_BACKGROUND_COLOR = "#000"
TRACK_FOREGROUND_COLOR = "#222"
TICK_COLOR = "#888"
CAP_HOVER_COLOR = "#555"
CAP_NORMAL_COLOR = "#333"
CAP_HOVER_OUTLINE = ACCENT_COLOR
CAP_NORMAL_OUTLINE = "#888"
VALUE_TEXT_COLOR = "#CCC"

# Geometry and Math Constants
ANGLE_90_DEGREES = 90
TICK_COUNT = 11
TICK_INTERVAL_NORMALIZER = 10.0
MAJOR_TICK_INTERVAL = 5
MAJOR_TICK_LENGTH = 10
MINOR_TICK_LENGTH = 5
TICK_HORIZONTAL_OFFSET = 15
CAP_RADIUS = 22
CAP_HOVER_WIDTH = 4
CAP_NORMAL_WIDTH = 2
CAP_INNER_PADDING = 5
SWEEP_START_ANGLE = 225
SWEEP_EXTENT_DEGREES = 270
POINTER_LENGTH_ADJUSTMENT = 2
POINTER_WIDTH = 3
ROTATION_VALUE_Y_OFFSET = 12
CURRENT_VALUE_Y_OFFSET = 32

# Active State Positioning
ACTIVE_LABEL_X = 600
ACTIVE_LABEL_Y = 450
LABEL_FAR_RADIUS_OFFSET = 25
LABEL_STAGGER_OFFSET = 25

class LTPFader:
    """Represents a single fader in the circular array with self-rendering capabilities."""

    def __init__(self, canvas, widget_id, length, angle_deg, color, group_index, label):
        self.canvas = canvas
        self.widget_id = widget_id
        self.track_length = length
        self.angle = angle_deg
        self.color_highlight = color
        self.group_index = group_index
        self.label = label
        
        self.center_x, self.center_y = 0, 0 
        self.is_visible = True
        self.value_min, self.value_max = 0.0, 100.0
        self.value_current = 20 + (random.random() * 70)
        self.rotation_min, self.rotation_max = 0.0, 100.0
        self.rotation_current = 70 + (random.random() * 20)
        
        self.tag_root = f"fader_{self.widget_id}"
        self.is_dragging = False
        self.is_hovered = False
        
        self.start_mouse_x, self.start_mouse_y = 0, 0
        self.start_value, self.start_rotation = 0, 0
        
        self.update_fader_position()
        self.render_fader()

    def update_fader_position(self):
        """Calculates the fader's center position in the circular array."""
        distance = NEAR_RADIUS + (self.track_length / RADIUS_DIVISOR)
        self.center_x, self.center_y = CircularMath.get_position(self.angle, distance)

    def render_fader(self):
        """Draws all fader components (track, ticks, cap, pointer) on the canvas."""
        self.canvas.delete(self.tag_root)
        if not self.is_visible: 
            return

        base_x, base_y = self.center_x, self.center_y
        track_angle = self.angle + ANGLE_90_DEGREES
        half_length = self.track_length / RADIUS_DIVISOR
        
        # Track
        start_point = CircularMath.rotate_point(base_x, base_y - half_length, base_x, base_y, track_angle)
        end_point = CircularMath.rotate_point(base_x, base_y + half_length, base_x, base_y, track_angle)
        self.canvas.create_line(start_point, end_point, fill=TRACK_BACKGROUND_COLOR, width=6, capstyle=tk.ROUND, tags=self.tag_root)
        self.canvas.create_line(start_point, end_point, fill=TRACK_FOREGROUND_COLOR, width=2, capstyle=tk.ROUND, tags=self.tag_root)
        
        # Ticks
        for i in range(TICK_COUNT):
            normalization_factor = i / TICK_INTERVAL_NORMALIZER
            local_y = (-half_length) + (normalization_factor * self.track_length)
            tick_length = MAJOR_TICK_LENGTH if i % MAJOR_TICK_INTERVAL == 0 else MINOR_TICK_LENGTH
            
            left_tick_p1 = CircularMath.rotate_point(base_x - TICK_HORIZONTAL_OFFSET, base_y + local_y, base_x, base_y, track_angle)
            left_tick_p2 = CircularMath.rotate_point(base_x - TICK_HORIZONTAL_OFFSET - tick_length, base_y + local_y, base_x, base_y, track_angle)
            self.canvas.create_line(left_tick_p1, left_tick_p2, fill=TICK_COLOR, width=2, tags=self.tag_root)
            
            right_tick_p1 = CircularMath.rotate_point(base_x + TICK_HORIZONTAL_OFFSET, base_y + local_y, base_x, base_y, track_angle)
            right_tick_p2 = CircularMath.rotate_point(base_x + TICK_HORIZONTAL_OFFSET + tick_length, base_y + local_y, base_x, base_y, track_angle)
            self.canvas.create_line(right_tick_p1, right_tick_p2, fill=TICK_COLOR, width=2, tags=self.tag_root)

        # Cap
        value_normalization = (self.value_current - self.value_min) / (self.value_max - self.value_min)
        cap_center_x, cap_center_y = CircularMath.rotate_point(base_x, base_y + (-half_length + value_normalization * self.track_length), base_x, base_y, track_angle)
        
        cap_fill = CAP_HOVER_COLOR if self.is_hovered else CAP_NORMAL_COLOR
        cap_outline = CAP_HOVER_OUTLINE if self.is_hovered else CAP_NORMAL_OUTLINE
        cap_outline_width = CAP_HOVER_WIDTH if self.is_hovered else CAP_NORMAL_WIDTH
        self.canvas.create_oval(cap_center_x - CAP_RADIUS, cap_center_y - CAP_RADIUS, cap_center_x + CAP_RADIUS, cap_center_y + CAP_RADIUS, 
                                fill=cap_fill, outline=cap_outline, width=cap_outline_width, tags=(self.tag_root, "cap"))
        
        # Sweep & Pointer
        pointer_angle_degrees = SWEEP_START_ANGLE - (self.rotation_current / 100.0) * SWEEP_EXTENT_DEGREES
        self.canvas.create_arc(cap_center_x - CAP_RADIUS + CAP_INNER_PADDING, cap_center_y - CAP_RADIUS + CAP_INNER_PADDING, 
                               cap_center_x + CAP_RADIUS - CAP_INNER_PADDING, cap_center_y + CAP_RADIUS - CAP_INNER_PADDING, 
                               start=SWEEP_START_ANGLE, extent=-(SWEEP_START_ANGLE - pointer_angle_degrees), 
                               style=tk.ARC, outline=self.color_highlight, width=4, tags=self.tag_root)
        
        pointer_radians = math.radians(pointer_angle_degrees)
        pointer_end_x = cap_center_x + (CAP_RADIUS - POINTER_LENGTH_ADJUSTMENT) * math.cos(pointer_radians)
        pointer_end_y = cap_center_y - (CAP_RADIUS - POINTER_LENGTH_ADJUSTMENT) * math.sin(pointer_radians)
        self.canvas.create_line(cap_center_x, cap_center_y, pointer_end_x, pointer_end_y, fill=self.color_highlight, width=POINTER_WIDTH, tags=self.tag_root)
        
        # Values & Label
        self.canvas.create_text(cap_center_x, cap_center_y + ROTATION_VALUE_Y_OFFSET, text=str(int(self.rotation_current)), fill=self.color_highlight, font=("Arial", 9, "bold"), tags=self.tag_root)
        self.canvas.create_text(cap_center_x, cap_center_y - CURRENT_VALUE_Y_OFFSET, text=str(int(self.value_current)), fill=VALUE_TEXT_COLOR, font=("Arial", 8), tags=self.tag_root)
        
        is_interaction_active = self.is_dragging or self.is_hovered
        if is_interaction_active:
            label_x, label_y = ACTIVE_LABEL_X, ACTIVE_LABEL_Y
        else:
            stagger_distance = FAR_RADIUS + LABEL_FAR_RADIUS_OFFSET + (self.widget_id % 2) * LABEL_STAGGER_OFFSET
            label_x, label_y = CircularMath.get_position(self.angle, stagger_distance)
            
        label_font = ("Arial", 12 if is_interaction_active else 10, "bold" if is_interaction_active else "normal")
        self.canvas.create_text(label_x, label_y, text=self.label, fill=self.color_highlight, font=label_font, tags=self.tag_root)

    def update_hover_state(self, is_hovered):
        """Updates the hover state and re-renders if the state has changed."""
        if self.is_visible and self.is_hovered != is_hovered:
            self.is_hovered = is_hovered
            self.render_fader()

    def bring_to_front(self):
        """Moves the fader elements to the top of the canvas stack."""
        self.canvas.tag_raise(self.tag_root)