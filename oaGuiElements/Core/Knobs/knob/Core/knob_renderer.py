# Core/knob_renderer.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import math
from ..effects.knob_3d_effects import draw_knob_3d_effects
from oaGuiElements.Methods.rotary_core import RotaryCore

_rotary = RotaryCore()

def draw_knob_visuals(canvas, state, config, value, label_text=None):
    """Modular rendering pipeline with 3D depth."""
    # ⚡ INDUSTRIAL TRANSPARENCY: Don't delete everything, preserve the patina slice
    for item in canvas.find_all():
        tags = canvas.gettags(item)
        if "panel_bg_slice" not in tags:
            canvas.delete(item)
    
    # 0. Draw Industrial Background (Fallback if slice doesn't exist)
    if hasattr(canvas, 'panel_bg_image') and not canvas.find_withtag("panel_bg_slice"):
        canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")
            
    width, height = state["dims"]["w"], state["dims"]["h"]
    # ⚡ MOCK PROTECTION: Ensure we have actual integers before comparing
    if not isinstance(width, int) or width <= 1: 
        width = config["width"]
    if not isinstance(height, int) or height <= 1: 
        height = config["height"]
    center_x, center_y = width / 2, height / 2
    
    # Extract config
    arc_width = config["arc_width"]
    show_ticks = config["show_ticks"]
    tick_length = config["tick_length"]
    min_val, max_val = config["min"], config["max"]
    indicator_color = config["indicator_color"]
    secondary_color = state["secondary_current"]
    knob_style = config["knob_style"]
    
    # Reserve space for text if not inside
    # Using 15px instead of 20px to save space on small knobs
    DEFAULT_LABEL_FONT_SIZE = 9
    LABEL_RESERVE_PADDING = 12
    
    top_reserve = LABEL_RESERVE_PADDING if config["text_pos"] == "top" and label_text and config["show_label"] else 0
    bottom_reserve = LABEL_RESERVE_PADDING if (config["text_pos"] == "bottom" and label_text and config["show_label"]) or (not config["text_inside"] and not config["no_center"]) else 0
    
    # Calculate max radius
    # padding accounts for the arc stroke width, optional ticks, 3D depth, and soft shadows
    ARC_STROKE_PADDING = 2
    padding = (arc_width / 2) + ARC_STROKE_PADDING
    if show_ticks:
        TICK_BUFFER = 4
        padding += tick_length + TICK_BUFFER
    
    # ⚡ ADDITIONAL SAFETY: Add a fixed margin for 3D depth offsets and blur/shadows
    # Increased to 10 for maximum safety against clipping
    SAFETY_MARGIN = 10
    padding += SAFETY_MARGIN

    # Use max available dimension but ensure we don't go negative
    usable_width = width - (padding * 2)
    usable_height = height - top_reserve - bottom_reserve - (padding * 2)
    
    RADIUS_FRAME_RATIO = 0.8
    radius = (min(usable_width, usable_height) / 2) * RADIUS_FRAME_RATIO  # ⚡ 20% reduction for better framing
    
    ABSOLUTE_MIN_RADIUS = 8
    if radius < ABSOLUTE_MIN_RADIUS: 
        radius = ABSOLUTE_MIN_RADIUS # Increased absolute minimum floor for safety
    
    # Adjusted Center for drawing knob (shift slightly to avoid overlapping labels)
    adjusted_center_y = (top_reserve + (height - bottom_reserve)) / 2

    # 1. Math Prep (RUST OPTIMIZED)
    pointer_angle_deg = _rotary.calculate_angle(value, float(min_val), float(max_val), knob_style)

    # Legacy variables for track drawing
    norm_val = (value - min_val) / (max_val - min_val) if max_val > min_val else 0
    if knob_style == "panner":
        mid_val = (min_val + max_val) / 2
        norm_from_center = (value - mid_val) / ((max_val - min_val) / 2)
        val_extent = -1 * norm_from_center * 135 if norm_from_center >= 0 else abs(norm_from_center) * 135
        start_angle = 90
    elif knob_style == "dial":
        val_extent = -360 * norm_val
        if abs(val_extent) >= 360: val_extent = -359.9
        start_angle = 90
    else:
        val_extent = -300 * norm_val
        start_angle = 240

    # 2. Draw Track
    bg_start = 0 if knob_style == "dial" else 240
    bg_extent = 359.9 if knob_style == "dial" else -300
    if knob_style == "panner":
         bg_start, bg_extent = 225, -270
    
    _draw_track(canvas, center_x, adjusted_center_y, radius, bg_start, bg_extent, start_angle, val_extent, secondary_color, indicator_color, arc_width, knob_style)
    
    # 3. Draw Ticks
    if show_ticks:
        _draw_ticks(canvas, center_x, adjusted_center_y, radius, arc_width, tick_length, config["tick_style"], secondary_color, min_val, max_val)

    # 4. Draw Body with Depth Offset
    if knob_style != "dial":
        # 3D Depth Logic
        DEPTH_OFFSET = 1.5 # Pixel offset for height
        side_color = "#111111"

        # 4.1 Draw the "Lower Ring" (Base/Side) - Offset SE
        _draw_body(canvas, center_x + DEPTH_OFFSET, adjusted_center_y + DEPTH_OFFSET, radius, config["shape"], side_color, 0, pointer_angle_deg, 0, side_color, config["teeth"])

        # 4.2 Draw the "Top Cap" - Offset NW
        cap_center_x, cap_center_y = center_x - DEPTH_OFFSET, adjusted_center_y - DEPTH_OFFSET
        _draw_body(canvas, cap_center_x, cap_center_y, radius, config["shape"], config["outline_color"], config["gradient_level"], pointer_angle_deg, config["outline_thickness"], config["fill_color"], config["teeth"])
        
        # 4.3 Apply Fixed 3D Lighting Effects (Glint/Shadow) on the shifted Cap
        if config["fill_color"] or config["knob_style"] == "standard":
            draw_knob_3d_effects(canvas, cap_center_x, cap_center_y, radius, config["shape"], config["fill_color"])
            
        # 5. Draw Pointer on the shifted Cap
        _draw_pointer(canvas, cap_center_x, cap_center_y, radius, arc_width, pointer_angle_deg, config["pointer_style"], indicator_color, config["pointer_length"], config["pointer_offset"], config["no_center"])
    else:
        # Dial style (no offset body)
        _draw_pointer(canvas, center_x, adjusted_center_y, radius, arc_width, pointer_angle_deg, config["pointer_style"], indicator_color, config["pointer_length"], config["pointer_offset"], config["no_center"])

    # 6. Text Updates
    foreground_color = config["fg_color"]
    # 6.1 Widget Label
    if label_text and config["show_label"]:
        # Calculate dynamic text position relative to knob radius + padding
        # ⚡ TIGHT LAYOUT: Pad 4px from the visual elements
        TEXT_ELEMENT_PADDING = 4
        visual_radius = radius + (arc_width / 2)
        if show_ticks: 
            TICK_VISUAL_BUFFER = 2
            visual_radius += tick_length + TICK_VISUAL_BUFFER
        
        label_x, label_y, label_anchor = center_x, adjusted_center_y - visual_radius - TEXT_ELEMENT_PADDING, "s"
        if config["text_pos"] == "bottom": 
            label_y, label_anchor = adjusted_center_y + visual_radius + TEXT_ELEMENT_PADDING, "n"
        elif config["text_pos"] == "left": 
            label_x, label_y, label_anchor = center_x - visual_radius - TEXT_ELEMENT_PADDING, adjusted_center_y, "e"
        elif config["text_pos"] == "right": 
            label_x, label_y, label_anchor = center_x + visual_radius + TEXT_ELEMENT_PADDING, adjusted_center_y, "w"
        
        LABEL_FONT_SIZE = 9
        canvas.create_text(label_x, label_y, text=label_text, fill=foreground_color, font=("Helvetica", LABEL_FONT_SIZE, "bold"), anchor=label_anchor, tags=("industrial_text", "vu_static"))

    # 6.2 Value Text
    val_str = f"{int(value)}"
    VALUE_FONT_SIZE = 8
    if config["text_inside"]:
        TEXT_CENTER_OFFSET = 10
        val_y_off = TEXT_CENTER_OFFSET if not config["no_center"] else 0
        canvas.create_text(center_x, adjusted_center_y + val_y_off, text=val_str, fill=indicator_color, font=("Helvetica", VALUE_FONT_SIZE, "bold"), tags=("industrial_text", "vu_static"))
    else:
        # ⚡ TIGHT VALUE: Center below the label or knob
        visual_radius = radius + (arc_width / 2)
        if show_ticks: 
            visual_radius += tick_length + 2
        
        VALUE_PADDING = 4
        value_y = adjusted_center_y + visual_radius + VALUE_PADDING
        # If label is already at bottom, push value further or stack them? 
        # Usually, if external value is on, label should be on top.
        LABEL_BOTTOM_STACK_OFFSET = 12
        if config["text_pos"] == "bottom": 
            value_y += LABEL_BOTTOM_STACK_OFFSET 
        canvas.create_text(center_x, value_y, text=val_str, fill=foreground_color, font=("Helvetica", VALUE_FONT_SIZE), anchor="n", tags=("industrial_text", "vu_static"))

def _draw_body(canvas, center_x, center_y, radius, shape, color, gradient_level, rotation_angle=0, outline_thickness=0, fill_color="", teeth=8):
    steps = gradient_level + 1
    for index in range(steps):
        current_radius = radius - (index * 2)
        if current_radius <= 0: break
        current_thickness = outline_thickness if index == 0 else 1
        current_fill = fill_color if (index == 0 or steps == 1) else ""
        if current_thickness == 0 and index == 0 and gradient_level == 0 and not current_fill:
            continue

        if shape == "circle":
            if gradient_level > 0 or (index == 0 and (current_thickness > 0 or current_fill)):
                canvas.create_oval(center_x-current_radius, center_y-current_radius, center_x+current_radius, center_y+current_radius, outline=color, width=current_thickness, fill=current_fill)
        elif shape == "octagon":
            OCTAGON_SIDES = 8
            points = _get_poly_points(center_x, center_y, current_radius, sides=OCTAGON_SIDES, start_angle=rotation_angle)
            canvas.create_polygon(points, outline=color, fill=current_fill, width=current_thickness)
        elif shape == "gear":
            GEAR_NOTCH_DEPTH = 0.15
            points = _get_gear_points(center_x, center_y, current_radius, teeth=teeth, notch_depth=GEAR_NOTCH_DEPTH, start_angle=rotation_angle)
            canvas.create_polygon(points, outline=color, fill=current_fill, width=current_thickness)

def _draw_track(canvas, center_x, center_y, radius, bg_start, bg_extent, start_angle, val_extent, bg_color, active_color, width, knob_style="standard"):
    # 0. Draw Background Slice if available (already handled in draw_knob_visuals)
    
    # 1. Background Arc
    canvas.create_arc(center_x - radius, center_y - radius, center_x + radius, center_y + radius, start=bg_start, extent=bg_extent, style=tk.ARC, outline=bg_color, width=width)
    
    # 2. Active Arc
    arc_style = tk.ARC if knob_style != "dial" else tk.PIESLICE
    final_color = active_color
    if knob_style == "panner":
         final_color = "red" if val_extent < 0 else active_color

    MIN_VISIBLE_EXTENT = 0.1
    if abs(val_extent) > MIN_VISIBLE_EXTENT:
        canvas.create_arc(center_x - radius, center_y - radius, center_x + radius, center_y + radius, start=start_angle, extent=val_extent, style=arc_style, 
                          outline=final_color if arc_style==tk.ARC else "", fill=final_color if arc_style==tk.PIESLICE else "", width=width)
    elif knob_style == "panner": 
        LINE_INDICATOR_OFFSET_TOP = 2
        LINE_INDICATOR_OFFSET_BOTTOM = 12
        LINE_INDICATOR_WIDTH = 2
        canvas.create_line(center_x, center_y - radius + LINE_INDICATOR_OFFSET_TOP, center_x, center_y - radius + LINE_INDICATOR_OFFSET_BOTTOM, fill=bg_color, width=LINE_INDICATOR_WIDTH)

def _draw_ticks(canvas, center_x, center_y, radius, arc_width, tick_length, style, color, min_val, max_val):
    TICK_START_ANGLE = 240
    TICK_TOTAL_EXTENT = 300
    TICK_STEP_DEG = 30
    end_angle = TICK_START_ANGLE - TICK_TOTAL_EXTENT
    
    TICKS_PER_SPAN = 10.0
    value_step = (max_val - min_val) / TICKS_PER_SPAN
    current_angle, current_value = TICK_START_ANGLE, min_val
    
    while current_angle >= end_angle - 1:
        radians = math.radians(current_angle)
        TICK_BASE_DIST = radius + (arc_width / 2) + 2
        ts_dist, te_dist = TICK_BASE_DIST, TICK_BASE_DIST + tick_length
        start_x, start_y = center_x + ts_dist * math.cos(radians), center_y - ts_dist * math.sin(radians)
        end_x, end_y = center_x + te_dist * math.cos(radians), center_y - te_dist * math.sin(radians)
        
        if style == "dots":
            DOT_RADIUS = 1
            canvas.create_oval(end_x - DOT_RADIUS, end_y - DOT_RADIUS, end_x + DOT_RADIUS, end_y + DOT_RADIUS, fill=color, outline=color)
        elif style == "numeric":
            NUMERIC_FONT_SIZE = 6
            canvas.create_text(end_x, end_y, text=f"{int(current_value)}", fill=color, font=("Arial", NUMERIC_FONT_SIZE))
        else:
            TICK_LINE_WIDTH = 1
            canvas.create_line(start_x, start_y, end_x, end_y, fill=color, width=TICK_LINE_WIDTH)
        
        current_angle -= TICK_STEP_DEG
        current_value += value_step

def _draw_pointer(canvas, center_x, center_y, radius, arc_width, angle_deg, style, color, length, offset, no_center):
    angle_rad = math.radians(angle_deg)
    pointer_start = offset
    pointer_end = (radius - arc_width / 2) if length is None else (offset + float(length))
    
    if style == "triangle":
        tip_x, tip_y = center_x + pointer_end * math.cos(angle_rad), center_y - pointer_end * math.sin(angle_rad)
        TRI_WIDTH = 5
        base_x, base_y = center_x + pointer_start * math.cos(angle_rad), center_y - pointer_start * math.sin(angle_rad)
        perp_angle = angle_rad + math.pi / 2
        c1x, c1y = base_x + TRI_WIDTH * math.cos(perp_angle), base_y - TRI_WIDTH * math.sin(perp_angle)
        c2x, c2y = base_x - TRI_WIDTH * math.cos(perp_angle), base_y + TRI_WIDTH * math.sin(perp_angle)
        canvas.create_polygon(tip_x, tip_y, c1x, c1y, c2x, c2y, fill=color, outline=color)
    elif style == "notch":
        NOTCH_LEN = 5
        NOTCH_WIDTH = 4
        start_x, start_y = center_x + (radius - NOTCH_LEN) * math.cos(angle_rad), center_y - (radius - NOTCH_LEN) * math.sin(angle_rad)
        end_x, end_y = center_x + radius * math.cos(angle_rad), center_y - radius * math.sin(angle_rad)
        canvas.create_line(start_x, start_y, end_x, end_y, fill=color, width=NOTCH_WIDTH, capstyle=tk.BUTT)
    else:
        POINTER_LINE_WIDTH = 2
        start_x, start_y = center_x + pointer_start * math.cos(angle_rad), center_y - pointer_start * math.sin(angle_rad)
        end_x, end_y = center_x + pointer_end * math.cos(angle_rad), center_y - pointer_end * math.sin(angle_rad)
        canvas.create_line(start_x, start_y, end_x, end_y, fill=color, width=POINTER_LINE_WIDTH, capstyle=tk.ROUND)

    if not no_center:
        CENTER_DOT_RADIUS = 3
        canvas.create_oval(center_x - CENTER_DOT_RADIUS, center_y - CENTER_DOT_RADIUS, center_x + CENTER_DOT_RADIUS, center_y + CENTER_DOT_RADIUS, fill=color, outline=color)

def _get_poly_points(center_x, center_y, radius, sides=8, start_angle=0):
    return _rotary.get_poly_points(float(center_x), float(center_y), float(radius), sides, float(start_angle))

def _get_gear_points(center_x, center_y, radius, teeth=8, notch_depth=0.15, start_angle=0):
    """
    Generates points for a gear shape with rounded (trapezoidal) teeth.
    Each tooth consists of 4 segments to soften the points.
    """
    return _rotary.get_gear_points(float(center_x), float(center_y), float(radius), teeth, float(notch_depth), float(start_angle))
