import tkinter as tk
import math
from ..effects.knob_3d_effects import draw_knob_3d_effects

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
    if width <= 1: width = config["width"]
    if height <= 1: height = config["height"]
    cx, cy = width / 2, height / 2
    
    # Extract config
    arc_width = config["arc_width"]
    show_ticks = config["show_ticks"]
    tick_length = config["tick_length"]
    min_val, max_val = config["min"], config["max"]
    indicator_color = config["indicator_color"]
    secondary = state["secondary_current"]
    knob_style = config["knob_style"]
    
    # Reserve space for text if not inside
    # Using 15px instead of 20px to save space on small knobs
    label_font_size = 9
    label_padding = 12
    top_reserve = label_padding if config["text_pos"] == "top" and label_text and config["show_label"] else 0
    bottom_reserve = label_padding if (config["text_pos"] == "bottom" and label_text and config["show_label"]) or (not config["text_inside"] and not config["no_center"]) else 0
    
    # Calculate max radius
    # padding accounts for the arc stroke width, optional ticks, 3D depth, and soft shadows
    padding = (arc_width / 2) + 2
    if show_ticks:
        padding += tick_length + 4
    
    # ⚡ ADDITIONAL SAFETY: Add a fixed margin for 3D depth offsets and blur/shadows
    # Increased to 10 for maximum safety against clipping
    padding += 10

    # Use max available dimension but ensure we don't go negative
    usable_w = width - (padding * 2)
    usable_h = height - top_reserve - bottom_reserve - (padding * 2)
    
    radius = (min(usable_w, usable_h) / 2) * 0.8  # ⚡ 20% reduction for better framing
    if radius < 8: radius = 8 # Increased absolute minimum floor for safety
    
    # Adjusted Center for drawing knob (shift slightly to avoid overlapping labels)
    adj_cy = (top_reserve + (height - bottom_reserve)) / 2

    # 1. Math Prep
    norm_val = (value - min_val) / (max_val - min_val) if max_val > min_val else 0

    # Style-Specific Math
    start_angle = 240
    extent = -300
    val_extent = extent * norm_val
    pointer_angle_deg = start_angle + val_extent

    if knob_style == "panner":
        mid_val = (min_val + max_val) / 2
        norm_from_center = (value - mid_val) / ((max_val - min_val) / 2)
        panner_max_arc = 135
        start_angle = 90
        val_extent = -1 * norm_from_center * panner_max_arc if norm_from_center >= 0 else abs(norm_from_center) * panner_max_arc
        pointer_angle_deg = 90 + (-1 * norm_from_center * panner_max_arc)

    elif knob_style == "dial":
        start_angle = 90
        val_extent = -360 * norm_val
        if abs(val_extent) >= 360: val_extent = -359.9
        pointer_angle_deg = start_angle + val_extent

    # 2. Draw Track
    bg_start = 0 if knob_style == "dial" else 240
    bg_extent = 359.9 if knob_style == "dial" else -300
    if knob_style == "panner":
         bg_start, bg_extent = 225, -270
    
    _draw_track(canvas, cx, adj_cy, radius, bg_start, bg_extent, start_angle, val_extent, secondary, indicator_color, arc_width, knob_style)
    
    # 3. Draw Ticks
    if show_ticks:
        _draw_ticks(canvas, cx, adj_cy, radius, arc_width, tick_length, config["tick_style"], secondary, min_val, max_val)

    # 4. Draw Body with Depth Offset
    if knob_style != "dial":
        # 3D Depth Logic
        depth = 1.5 # Pixel offset for height
        side_color = "#111111"

        # 4.1 Draw the "Lower Ring" (Base/Side) - Offset SE
        _draw_body(canvas, cx + depth, adj_cy + depth, radius, config["shape"], side_color, 0, pointer_angle_deg, 0, side_color, config["teeth"])

        # 4.2 Draw the "Top Cap" - Offset NW
        cap_cx, cap_cy = cx - depth, adj_cy - depth
        _draw_body(canvas, cap_cx, cap_cy, radius, config["shape"], config["outline_color"], config["gradient_level"], pointer_angle_deg, config["outline_thickness"], config["fill_color"], config["teeth"])
        
        # 4.3 Apply Fixed 3D Lighting Effects (Glint/Shadow) on the shifted Cap
        if config["fill_color"] or config["knob_style"] == "standard":
            draw_knob_3d_effects(canvas, cap_cx, cap_cy, radius, config["shape"], config["fill_color"])
            
        # 5. Draw Pointer on the shifted Cap
        _draw_pointer(canvas, cap_cx, cap_cy, radius, arc_width, pointer_angle_deg, config["pointer_style"], indicator_color, config["pointer_length"], config["pointer_offset"], config["no_center"])
    else:
        # Dial style (no offset body)
        _draw_pointer(canvas, cx, adj_cy, radius, arc_width, pointer_angle_deg, config["pointer_style"], indicator_color, config["pointer_length"], config["pointer_offset"], config["no_center"])

    # 6. Text Updates
    fg = config["fg_color"]
    # 6.1 Widget Label
    if label_text and config["show_label"]:
        # Calculate dynamic text position relative to knob radius + padding
        # ⚡ TIGHT LAYOUT: Pad 4px from the visual elements
        text_padding = 4
        visual_radius = radius + (arc_width / 2)
        if show_ticks: visual_radius += tick_length + 2
        
        lx, ly, l_anchor = cx, adj_cy - visual_radius - text_padding, "s"
        if config["text_pos"] == "bottom": ly, l_anchor = adj_cy + visual_radius + text_padding, "n"
        elif config["text_pos"] == "left": lx, ly, l_anchor = cx - visual_radius - text_padding, adj_cy, "e"
        elif config["text_pos"] == "right": lx, ly, l_anchor = cx + visual_radius + text_padding, adj_cy, "w"
        
        canvas.create_text(lx, ly, text=label_text, fill=fg, font=("Helvetica", 9, "bold"), anchor=l_anchor, tags=("industrial_text", "vu_static"))

    # 6.2 Value Text
    val_str = f"{int(value)}"
    if config["text_inside"]:
        canvas.create_text(cx, adj_cy + (10 if not config["no_center"] else 0), text=val_str, fill=indicator_color, font=("Helvetica", 8, "bold"), tags=("industrial_text", "vu_static"))
    else:
        # ⚡ TIGHT VALUE: Center below the label or knob
        visual_radius = radius + (arc_width / 2)
        if show_ticks: visual_radius += tick_length + 2
        vy = adj_cy + visual_radius + 4
        # If label is already at bottom, push value further or stack them? 
        # Usually, if external value is on, label should be on top.
        if config["text_pos"] == "bottom": vy += 12 
        canvas.create_text(cx, vy, text=val_str, fill=fg, font=("Helvetica", 8), anchor="n", tags=("industrial_text", "vu_static"))

def _draw_body(canvas, cx, cy, radius, shape, color, gradient_level, rotation_angle=0, outline_thickness=0, fill_color="", teeth=8):
    steps = gradient_level + 1
    for i in range(steps):
        r = radius - (i * 2)
        if r <= 0: break
        current_thickness = outline_thickness if i == 0 else 1
        current_fill = fill_color if (i == 0 or steps == 1) else ""
        if current_thickness == 0 and i == 0 and gradient_level == 0 and not current_fill:
            continue

        if shape == "circle":
            if gradient_level > 0 or (i == 0 and (current_thickness > 0 or current_fill)):
                canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=color, width=current_thickness, fill=current_fill)
        elif shape == "octagon":
            points = _get_poly_points(cx, cy, r, sides=8, start_angle=rotation_angle)
            canvas.create_polygon(points, outline=color, fill=current_fill, width=current_thickness)
        elif shape == "gear":
            points = _get_gear_points(cx, cy, r, teeth=teeth, notch_depth=0.15, start_angle=rotation_angle)
            canvas.create_polygon(points, outline=color, fill=current_fill, width=current_thickness)

def _draw_track(canvas, cx, cy, radius, bg_start, bg_extent, start_angle, val_extent, bg_color, active_color, width, knob_style="standard"):
    # 0. Draw Background Slice if available (already handled in draw_knob_visuals)
    
    # 1. Background Arc
    canvas.create_arc(cx - radius, cy - radius, cx + radius, cy + radius, start=bg_start, extent=bg_extent, style=tk.ARC, outline=bg_color, width=width)
    
    # 2. Active Arc
    style = tk.ARC if knob_style != "dial" else tk.PIESLICE
    final_color = active_color
    if knob_style == "panner":
         final_color = "red" if val_extent < 0 else active_color

    if abs(val_extent) > 0.1:
        canvas.create_arc(cx - radius, cy - radius, cx + radius, cy + radius, start=start_angle, extent=val_extent, style=style, outline=final_color if style==tk.ARC else "", fill=final_color if style==tk.PIESLICE else "", width=width)
    elif knob_style == "panner": 
        canvas.create_line(cx, cy - radius + 2, cx, cy - radius + 12, fill=bg_color, width=2)

def _draw_ticks(canvas, cx, cy, radius, arc_width, tick_length, style, color, min_val, max_val):
    start_angle, end_angle, step = 240, 240 - 300, 30
    curr, val_step, curr_val = start_angle, (max_val - min_val) / 10.0, min_val
    
    while curr >= end_angle - 1:
        rad = math.radians(curr)
        ts_dist, te_dist = radius + (arc_width/2) + 2, radius + (arc_width/2) + 2 + tick_length
        ts_x, ts_y = cx + ts_dist * math.cos(rad), cy - ts_dist * math.sin(rad)
        te_x, te_y = cx + te_dist * math.cos(rad), cy - te_dist * math.sin(rad)
        
        if style == "dots":
            canvas.create_oval(te_x-1, te_y-1, te_x+1, te_y+1, fill=color, outline=color)
        elif style == "numeric":
            canvas.create_text(te_x, te_y, text=f"{int(curr_val)}", fill=color, font=("Arial", 6))
        else:
            canvas.create_line(ts_x, ts_y, te_x, te_y, fill=color, width=1)
        curr -= step
        curr_val += val_step

def _draw_pointer(canvas, cx, cy, radius, arc_width, angle_deg, style, color, length, offset, no_center):
    angle_rad = math.radians(angle_deg)
    p_start, p_end = offset, (radius - arc_width/2) if length is None else (offset + float(length))
    
    if style == "triangle":
        tip_x, tip_y = cx + p_end * math.cos(angle_rad), cy - p_end * math.sin(angle_rad)
        w, bx, by = 5, cx + p_start * math.cos(angle_rad), cy - p_start * math.sin(angle_rad)
        perp_ang = angle_rad + math.pi/2
        c1x, c1y = bx + w * math.cos(perp_ang), by - w * math.sin(perp_ang)
        c2x, c2y = bx - w * math.cos(perp_ang), by + w * math.sin(perp_ang)
        canvas.create_polygon(tip_x, tip_y, c1x, c1y, c2x, c2y, fill=color, outline=color)
    elif style == "notch":
        notch_len = 5
        sx, sy = cx + (radius - notch_len) * math.cos(angle_rad), cy - (radius - notch_len) * math.sin(angle_rad)
        ex, ey = cx + radius * math.cos(angle_rad), cy - radius * math.sin(angle_rad)
        canvas.create_line(sx, sy, ex, ey, fill=color, width=4, capstyle=tk.BUTT)
    else:
        sx, sy = cx + p_start * math.cos(angle_rad), cy - p_start * math.sin(angle_rad)
        ex, ey = cx + p_end * math.cos(angle_rad), cy - p_end * math.sin(angle_rad)
        canvas.create_line(sx, sy, ex, ey, fill=color, width=2, capstyle=tk.ROUND)

    if not no_center:
        canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=color, outline=color)

def _get_poly_points(cx, cy, radius, sides=8, start_angle=0):
    points = []
    angle_step = 360 / sides
    for i in range(sides):
        deg = i * angle_step + start_angle
        rad = math.radians(deg)
        points.extend([cx + radius * math.cos(rad), cy - radius * math.sin(rad)])
    return points

def _get_gear_points(cx, cy, radius, teeth=8, notch_depth=0.15, start_angle=0):
    """
    Generates points for a gear shape with rounded (trapezoidal) teeth.
    Each tooth consists of 4 segments to soften the points.
    """
    points = []
    num_segments = teeth * 4 # 4 points per tooth cycle
    inner_radius = radius * (1 - notch_depth)
    angle_step = 360 / num_segments
    
    for i in range(num_segments):
        deg = i * angle_step + start_angle
        rad = math.radians(deg)
        
        # Cycle through 4 states: Top-Left, Top-Right, Bottom-Right, Bottom-Left
        state = i % 4
        if state in [1, 2]: # "Top" of the tooth
            r = radius
        else: # "Bottom" of the notch
            r = inner_radius
            
        points.extend([cx + r * math.cos(rad), cy - r * math.sin(rad)])
    return points
