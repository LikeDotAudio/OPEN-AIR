# Core/scale.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import math
import logging
from oaGuiElements.Core.metering.meter_needle.Core.constants import (
    SCALE_DEFAULT_STEPS, SCALE_SUB_TICK_DOT_RADIUS, 
    SCALE_SUB_TICK_WIDTH, SCALE_MAIN_TICK_WIDTH
)

try:
    from oaRustCore.oa_procedural_art_rs import ProceduralArtEngine
    _rust_engine = ProceduralArtEngine()
    HAS_RUST = True
except Exception as e:
    logging.warning(f"oaGuiElements: ScaleDrawer fallback to Python: {e}")
    HAS_RUST = False

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class GeometryContext:
    """Encapsulates the geometric parameters for drawing."""
    center_x: float
    center_y: float
    min_val: float
    max_val: float
    start_angle_deg: float
    end_angle_deg: float
    extent_deg: float
    main_arc_radius: float
    arc_thickness: float
    tick_radius: Optional[float] = None

@dataclass
class TickStyle:
    """Encapsulates the styling and layout parameters for ticks."""
    tick_length: float
    sub_tick_length: float
    fg_color: str
    ticks_visible: bool
    custom_ticks: Optional[List[float]] = None
    tick_step: Optional[float] = None
    anchor_point: Optional[float] = None
    sub_ticks: int = 0
    sub_tick_style: str = 'line'
    counter_clockwise: bool = False

class ScaleDrawer:
    @staticmethod
    def draw_ticks(canvas, geom_ctx: GeometryContext, style: TickStyle):
        
        if geom_ctx.tick_radius is not None:
             tick_start_radius = geom_ctx.tick_radius
        else:
             tick_start_radius = geom_ctx.main_arc_radius - (geom_ctx.arc_thickness / 2)
        
        if style.custom_ticks:
            tick_values = style.custom_ticks
        elif style.tick_step is not None:
            # Generate based on step and anchor
            start = style.anchor_point if style.anchor_point is not None else geom_ctx.min_val
            generated_ticks = {start}
            
            # Go down from anchor
            curr = start - style.tick_step
            while curr >= geom_ctx.min_val:
                generated_ticks.add(curr)
                curr -= style.tick_step
            
            # Go up from anchor
            curr = start + style.tick_step
            while curr <= geom_ctx.max_val:
                generated_ticks.add(curr)
                curr += style.tick_step
                
            tick_values = sorted(list(generated_ticks))
        else:
            steps = SCALE_DEFAULT_STEPS
            tick_values = [geom_ctx.min_val + (i / (steps - 1.0) * (geom_ctx.max_val - geom_ctx.min_val)) for i in range(steps)]

        # ⚡ OPTIMIZATION: Offload Coordinate Math to Rust
        if HAS_RUST and style.ticks_visible:
            # 1. Main Ticks
            coords = _rust_engine.calculate_circular_ticks(
                geom_ctx.center_x, geom_ctx.center_y,
                tick_values,
                geom_ctx.min_val, geom_ctx.max_val,
                geom_ctx.start_angle_deg, geom_ctx.end_angle_deg, geom_ctx.extent_deg,
                tick_start_radius, style.tick_length,
                style.counter_clockwise
            )
            for x_start, y_start, x_end, y_end in coords:
                canvas.create_line(x_start, y_start, x_end, y_end, fill=style.fg_color, width=SCALE_MAIN_TICK_WIDTH, tags=("vu_element", "tick"))

            # 2. Sub-Ticks
            if style.sub_ticks > 0:
                all_sub_values = []
                for i in range(len(tick_values) - 1):
                    v1, v2 = tick_values[i], tick_values[i+1]
                    for j in range(1, style.sub_ticks + 1):
                        all_sub_values.append(v1 + (j * (v2 - v1) / (style.sub_ticks + 1)))
                
                sub_coords = _rust_engine.calculate_circular_ticks(
                    geom_ctx.center_x, geom_ctx.center_y,
                    all_sub_values,
                    geom_ctx.min_val, geom_ctx.max_val,
                    geom_ctx.start_angle_deg, geom_ctx.end_angle_deg, geom_ctx.extent_deg,
                    tick_start_radius, style.sub_tick_length,
                    style.counter_clockwise
                )
                
                for k, (sx_start, sy_start, sx_end, sy_end) in enumerate(sub_coords):
                    if style.sub_tick_style == "dot":
                        dot_r = SCALE_SUB_TICK_DOT_RADIUS
                        canvas.create_oval(
                            sx_start - dot_r, sy_start - dot_r,
                            sx_start + dot_r, sy_start + dot_r,
                            fill=style.fg_color, outline=style.fg_color, tags=("vu_element", "tick")
                        )
                    else:
                        canvas.create_line(sx_start, sy_start, sx_end, sy_end, fill=style.fg_color, width=SCALE_SUB_TICK_WIDTH, tags=("vu_element", "tick"))
            
            return tick_values

        # --- Python Fallback ---
        for i, tick_val in enumerate(tick_values):
            # Calculate normalized position (0.0 to 1.0)
            range_val = geom_ctx.max_val - geom_ctx.min_val
            percentage = (tick_val - geom_ctx.min_val) / range_val if range_val != 0 else 0
            
            # Map to angle
            if style.counter_clockwise:
                current_angle_deg = geom_ctx.end_angle_deg + (percentage * geom_ctx.extent_deg)
            else:
                current_angle_deg = geom_ctx.start_angle_deg - (percentage * geom_ctx.extent_deg)
                
            current_angle_rad = math.radians(current_angle_deg)

            # Draw Main Tick
            if style.ticks_visible:
                x_tick_start = geom_ctx.center_x + tick_start_radius * math.cos(current_angle_rad)
                y_tick_start = geom_ctx.center_y - tick_start_radius * math.sin(current_angle_rad)
                x_tick_end = geom_ctx.center_x + (tick_start_radius - style.tick_length) * math.cos(current_angle_rad)
                y_tick_end = geom_ctx.center_y - (tick_start_radius - style.tick_length) * math.sin(current_angle_rad)
                # ⚡ OPTIMIZATION: Use 'tick' tag for batch updates
                canvas.create_line(x_tick_start, y_tick_start, x_tick_end, y_tick_end, fill=style.fg_color, width=SCALE_MAIN_TICK_WIDTH, tags=("vu_element", "tick"))

            # Draw Sub-Ticks (between this tick and next)
            if style.sub_ticks > 0 and i < len(tick_values) - 1:
                next_val = tick_values[i+1]
                for j in range(1, style.sub_ticks + 1):
                    sub_val = tick_val + (j * (next_val - tick_val) / (style.sub_ticks + 1))
                    sub_perc = (sub_val - geom_ctx.min_val) / range_val if range_val != 0 else 0
                    
                    if style.counter_clockwise:
                        sub_angle_deg = geom_ctx.end_angle_deg + (sub_perc * geom_ctx.extent_deg)
                    else:
                        sub_angle_deg = geom_ctx.start_angle_deg - (sub_perc * geom_ctx.extent_deg)
                    
                    sub_angle_rad = math.radians(sub_angle_deg)
                    
                    sx_tick_start = geom_ctx.center_x + tick_start_radius * math.cos(sub_angle_rad)
                    sy_tick_start = geom_ctx.center_y - tick_start_radius * math.sin(sub_angle_rad)
                    
                    if style.sub_tick_style == "dot":
                        # Draw a small dot at the start position
                        dot_r = SCALE_SUB_TICK_DOT_RADIUS
                        # ⚡ OPTIMIZATION: Use 'tick' tag for batch updates
                        canvas.create_oval(
                            sx_tick_start - dot_r, sy_tick_start - dot_r,
                            sx_tick_start + dot_r, sy_tick_start + dot_r,
                            fill=style.fg_color, outline=style.fg_color, tags=("vu_element", "tick")
                        )
                    else:
                        # Standard Line
                        sx_tick_end = geom_ctx.center_x + (tick_start_radius - style.sub_tick_length) * math.cos(sub_angle_rad)
                        sy_tick_end = geom_ctx.center_y - (tick_start_radius - style.sub_tick_length) * math.sin(sub_angle_rad)
                        # ⚡ OPTIMIZATION: Use 'tick' tag for batch updates
                        canvas.create_line(sx_tick_start, sy_tick_start, sx_tick_end, sy_tick_end, fill=style.fg_color, width=SCALE_SUB_TICK_WIDTH, tags=("vu_element", "tick"))
        
        return tick_values

    @staticmethod
    def draw_arcs(canvas, center_x, center_y, min_val, max_val,
                  start_angle_deg, end_angle_deg, extent_deg,
                  main_arc_radius, arc_thickness,
                  lower_colour, middle_colour, upper_colour,
                  mid_range_start, red_zone_start,
                  counter_clockwise, arc_radius=None):
        
        # Use provided arc_radius override if available
        radius_to_use = arc_radius if arc_radius is not None else main_arc_radius

        range_val = max_val - min_val
        if range_val == 0: range_val = 1.0
        
        # Normalize boundaries
        mid_start_norm = (mid_range_start - min_val) / range_val
        red_start_norm = (red_zone_start - min_val) / range_val
        
        # Clamp norms
        mid_start_norm = max(0.0, min(1.0, mid_start_norm))
        red_start_norm = max(0.0, min(1.0, red_start_norm))
        
        # Ensure mid_start <= red_start for logic simplicity
        if mid_start_norm > red_start_norm:
            mid_start_norm = red_start_norm

        transition_angle_deg = 0

        if counter_clockwise:
            a_mid = end_angle_deg + (mid_start_norm * extent_deg)
            a_red = end_angle_deg + (red_start_norm * extent_deg)
            
            # Lower Arc
            canvas.create_arc(
                center_x - radius_to_use, center_y - radius_to_use,
                center_x + radius_to_use, center_y + radius_to_use,
                start=end_angle_deg, extent=(a_mid - end_angle_deg),
                style=tk.ARC, outline=lower_colour, width=arc_thickness, tags=("vu_element", "arc")
            )
            # Middle Arc
            canvas.create_arc(
                center_x - radius_to_use, center_y - radius_to_use,
                center_x + radius_to_use, center_y + radius_to_use,
                start=a_mid, extent=(a_red - a_mid),
                style=tk.ARC, outline=middle_colour, width=arc_thickness, tags=("vu_element", "arc")
            )
            # Upper Arc
            canvas.create_arc(
                center_x - radius_to_use, center_y - radius_to_use,
                center_x + radius_to_use, center_y + radius_to_use,
                start=a_red, extent=(start_angle_deg - a_red),
                style=tk.ARC, outline=upper_colour, width=arc_thickness, tags=("vu_element", "arc")
            )
            
            transition_angle_deg = a_red
        else:
            a_mid = start_angle_deg - (mid_start_norm * extent_deg)
            a_red = start_angle_deg - (red_start_norm * extent_deg)
            
            # Lower Arc
            canvas.create_arc(
                center_x - radius_to_use, center_y - radius_to_use,
                center_x + radius_to_use, center_y + radius_to_use,
                start=a_mid, extent=(start_angle_deg - a_mid),
                style=tk.ARC, outline=lower_colour, width=arc_thickness, tags=("vu_element", "arc")
            )
            # Middle Arc
            canvas.create_arc(
                center_x - radius_to_use, center_y - radius_to_use,
                center_x + radius_to_use, center_y + radius_to_use,
                start=a_red, extent=(a_mid - a_red),
                style=tk.ARC, outline=middle_colour, width=arc_thickness, tags=("vu_element", "arc")
            )
            # Upper Arc
            canvas.create_arc(
                center_x - radius_to_use, center_y - radius_to_use,
                center_x + radius_to_use, center_y + radius_to_use,
                start=end_angle_deg, extent=(a_red - end_angle_deg),
                style=tk.ARC, outline=upper_colour, width=arc_thickness, tags=("vu_element", "arc")
            )
            
            transition_angle_deg = a_red
            
        return transition_angle_deg
