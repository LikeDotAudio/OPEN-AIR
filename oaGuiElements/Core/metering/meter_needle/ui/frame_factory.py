# ui/frame_factory.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk
import math
from oaGuiElements.Core.metering.meter_needle.constants import (
    NUMBER_FONT_FAMILY, 
    LAYOUT_PADDING_DEFAULT, LAYOUT_LABEL_PADDING_X, LAYOUT_LABEL_PAD_Y_TOP, LAYOUT_LABEL_PAD_Y_BOTTOM,
    LAYOUT_CANVAS_MARGIN_W, LAYOUT_CANVAS_MARGIN_H,
    LAYOUT_OFFSET_X, LAYOUT_OFFSET_Y, LAYOUT_PIVOT_CROP_MIN_H
)

class FrameFactory:
    @staticmethod
    def create_frame(parent, config):
        # ⚡ HIGH-FIDELITY: Use tk.Canvas for the root frame to support background slicing
        frame = tk.Canvas(parent, bd=0, highlightthickness=0, relief="flat")
        return frame

    @staticmethod
    def calculate_dimensions(config):
        # Dynamic Geometry Calculation
        padding = LAYOUT_PADDING_DEFAULT
        main_arc_radius = (config.size - padding) / 2
        
        # Calculate the extremes of the arc to determine bounding box
        half_angle = config.meter_viewable_angle / 2.0
        a1 = math.radians(config.meter_center_angle + half_angle)
        a2 = math.radians(config.meter_center_angle - half_angle)
        
        # Points to check: pivot(0,0), arc start, arc end, and any cardinal directions in between
        pts = [(0, 0), 
               (main_arc_radius * math.cos(a1), -main_arc_radius * math.sin(a1)),
               (main_arc_radius * math.cos(a2), -main_arc_radius * math.sin(a2))]
        
        # Check for cardinal directions within the arc sweep
        for angle_deg in [0, 90, 180, 270]:
            # Normalize angle to be relative to center
            diff = (angle_deg - config.meter_center_angle + 180) % 360 - 180
            if abs(diff) <= half_angle:
                ar = math.radians(angle_deg)
                pts.append((main_arc_radius * math.cos(ar), -main_arc_radius * math.sin(ar)))

        min_x = min(p[0] for p in pts)
        max_x = max(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        max_y = max(p[1] for p in pts)
        
        # Add padding for labels
        if config.scale_numbers:
            min_x -= LAYOUT_LABEL_PADDING_X; max_x += LAYOUT_LABEL_PADDING_X
            min_y -= 5; max_y += 15 # Kept some internal ones as they seem specific to text bounding box logic

        bb_width = max_x - min_x
        bb_height = max_y - min_y
        
        requested_w = config.width
        requested_h = config.height
        
        total_width = max(int(bb_width + LAYOUT_CANVAS_MARGIN_W), requested_w)
        total_height = max(int(bb_height + LAYOUT_CANVAS_MARGIN_H), requested_h)
        
        # Calculate pivot offset from top-left of canvas, centering the arc
        offset_x = -min_x + (LAYOUT_CANVAS_MARGIN_W / 2)
        offset_y = -min_y + (LAYOUT_CANVAS_MARGIN_H / 5) # Heuristic from original code (10 -> 2 ratio)
        
        # Original code used: offset_x = -min_x + 10; offset_y = -min_y + 2
        offset_x = -min_x + LAYOUT_OFFSET_X
        offset_y = -min_y + LAYOUT_OFFSET_Y
        
        if requested_w > bb_width + LAYOUT_CANVAS_MARGIN_W:
            offset_x += (requested_w - (bb_width + LAYOUT_CANVAS_MARGIN_W)) / 2
        if requested_h > bb_height + LAYOUT_CANVAS_MARGIN_H:
            offset_y += (requested_h - (bb_height + LAYOUT_CANVAS_MARGIN_H)) / 2

        # Apply Pivot Crop (Layout)
        if config.pivot_crop > 0:
            crop_pixels = main_arc_radius * (config.pivot_crop / 100.0)
            total_height = max(LAYOUT_PIVOT_CROP_MIN_H, int(total_height - crop_pixels))
            
        return total_width, total_height, offset_x, offset_y

    @staticmethod
    def create_canvas(frame, total_width, total_height, bg_color):
        canvas = tk.Canvas(
            frame,
            width=total_width,
            height=total_height,
            bg=bg_color,
            highlightthickness=0,
        )
        canvas.pack(side=tk.TOP, fill=tk.NONE, expand=False)
        return canvas