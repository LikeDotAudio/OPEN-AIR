# workers/builder/widgets/faders/fader/core/scale.py

import math
import tkinter as tk

DEFAULT_CAP_WIDTH = 40
DEFAULT_TICK_INTERVAL_LIMIT = 10.0
SMART_INTERVAL_BASE = 10.0
MIN_CANVAS_WIDTH_FOR_MARGIN = 100
MEDIUM_CANVAS_WIDTH_FOR_MARGIN = 80
LARGE_MARGIN = 5
MEDIUM_MARGIN = 2
SMALL_MARGIN = 0
CANVAS_BOUNDARY_OFFSET = 10
LABEL_ADJUSTMENT_OFFSET = 15
MIN_LABEL_DISTANCE = 5
TICK_LINE_GAP = 2

# Thresholds and intervals for labeling density
LABEL_THRESHOLDS = [(5000, 500), (1000, 200), (500, 50), (250, 20), (100, 10), (50, 5), (20, 2)]
DRAWING_THRESHOLDS = [(500, 100), (200, 50), (50, 10), (20, 5), (10, 2), (5, 1)]

class ScaleDrawer:
    @staticmethod
    def draw(canvas, frame, width, height, layout):
        """Draws the ticks and labels for the vertical fader."""
        center_x = layout['cx']
        available_height = layout['available_height']
        vertical_padding = layout['padding']
        tick_length_half = layout['tick_length_half']
        slot_width = layout['slot_w']
        cap_width = layout.get('cap_width', DEFAULT_CAP_WIDTH)

        tick_values = ScaleDrawer._get_tick_values(frame)
        label_interval, draw_interval = ScaleDrawer._calculate_tick_intervals(len(tick_values))
        
        config = ScaleDrawer._get_tick_configuration(frame)
        label_offset = ScaleDrawer._calculate_text_offset(width, center_x, tick_length_half, slot_width, cap_width, frame, config['label_position'])

        for index, value in enumerate(tick_values):
            y_coordinate = ScaleDrawer._calculate_tick_y_coordinate(value, frame, available_height, vertical_padding)
            is_main_tick = (index % label_interval == 0)
            
            if index % draw_interval == 0:
                ScaleDrawer._render_tick_line(canvas, center_x, y_coordinate, tick_length_half, slot_width, is_main_tick, frame, config)
            
            if is_main_tick:
                ScaleDrawer._render_tick_label(canvas, center_x, y_coordinate, value, label_offset, frame, config)

    @staticmethod
    def _get_tick_values(frame):
        """Retrieve custom ticks or generate smart ticks based on frame range."""
        if frame.custom_ticks is not None:
            return frame.custom_ticks
             
        value_range = frame.max_val - frame.min_val
        tick_interval = ScaleDrawer._calculate_smart_interval(frame, value_range)
        
        ticks = []
        if tick_interval > 0:
            current_value = math.ceil(frame.min_val / tick_interval) * tick_interval
            while current_value <= frame.max_val:
                ticks.append(current_value)
                current_value += tick_interval
        return ticks

    @staticmethod
    def _calculate_smart_interval(frame, value_range):
        """Calculate a human-friendly tick interval."""
        if hasattr(frame, "tick_interval") and frame.tick_interval is not None:
            return float(frame.tick_interval)
        if value_range <= 0:
            return SMART_INTERVAL_BASE
        
        raw_interval = value_range / 10.0
        exponent = math.floor(math.log10(raw_interval))
        fractional_part = raw_interval / (10**exponent)
        
        if fractional_part < 1.5:
            snap_value = 1
        elif fractional_part < 3.5:
            snap_value = 2
        elif fractional_part < 7.5:
            snap_value = 5
        else:
            snap_value = 10
        return snap_value * (10**exponent)

    @staticmethod
    def _calculate_tick_intervals(num_ticks):
        """Determine labeling and drawing density to avoid overcrowding."""
        label_interval = 1
        for threshold, interval in LABEL_THRESHOLDS:
            if num_ticks > threshold:
                label_interval = interval
                break
        
        draw_interval = 1
        for threshold, interval in DRAWING_THRESHOLDS:
            if label_interval >= threshold:
                draw_interval = interval
                break
        return label_interval, draw_interval

    @staticmethod
    def _get_tick_configuration(frame):
        """Extract aesthetic configuration for ticks from the frame."""
        tick_color = getattr(frame, "tick_color", "light grey")
        sub_tick_color = getattr(frame, "sub_tick_color", tick_color)
        return {
            'tick_color': tick_color,
            'sub_tick_color': sub_tick_color,
            'tick_text_color': getattr(frame, "tick_text_color", tick_color),
            'sub_tick_text_color': getattr(frame, "sub_tick_text_color", sub_tick_color),
            'label_position': getattr(frame, "tick_label_position", "right")
        }

    @staticmethod
    def _calculate_text_offset(width, center_x, tick_length_half, slot_width, cap_width, frame, label_position):
        """Calculate safe offset for labels to avoid overlap with the fader cap."""
        margin = LARGE_MARGIN
        if width < MIN_CANVAS_WIDTH_FOR_MARGIN:
            margin = MEDIUM_MARGIN
        if width < MEDIUM_CANVAS_WIDTH_FOR_MARGIN:
            margin = SMALL_MARGIN
        
        offset = max(tick_length_half, (cap_width / 2)) + margin
        
        # Prevent overflowing the canvas boundaries
        if label_position in ["right", "both"] and (center_x + offset > width - CANVAS_BOUNDARY_OFFSET):
            offset = max(width - center_x - LABEL_ADJUSTMENT_OFFSET, slot_width / 2 + MIN_LABEL_DISTANCE)
        if label_position in ["left", "both"] and (center_x - offset < CANVAS_BOUNDARY_OFFSET):
            offset = max(center_x - LABEL_ADJUSTMENT_OFFSET, slot_width / 2 + MIN_LABEL_DISTANCE)
        return offset

    @staticmethod
    def _calculate_tick_y_coordinate(value, frame, available_height, vertical_padding):
        """Convert a value to a vertical Y coordinate on the canvas."""
        value_range = frame.max_val - frame.min_val
        linear_normalization = max(0.0, min(1.0, (value - frame.min_val) / value_range if value_range != 0 else 0))
        display_normalization = max(1e-7, linear_normalization) ** (1.0 / frame.log_exponent) if frame.log_exponent != 1.0 else linear_normalization
        return available_height * (1 - display_normalization) + vertical_padding

    @staticmethod
    def _render_tick_line(canvas, center_x, y_coordinate, length_half, slot_width, is_main_tick, frame, config):
        """Draw segmented tick lines on both sides of the track slot."""
        color = config['tick_color'] if is_main_tick else config['sub_tick_color']
        canvas.create_line(center_x - length_half, y_coordinate, center_x - slot_width / 2 - TICK_LINE_GAP, y_coordinate, 
                           fill=color, width=frame.tick_thickness, tags="static")
        canvas.create_line(center_x + slot_width / 2 + TICK_LINE_GAP, y_coordinate, center_x + length_half, y_coordinate, 
                           fill=color, width=frame.tick_thickness, tags="static")

    @staticmethod
    def _render_tick_label(canvas, center_x, y_coordinate, value, offset, frame, config):
        """Render the numeric label at the specified offset."""
        label_text = str(int(value)) if value == int(value) else f"{value:.1f}"
        text_color = config['tick_text_color'] # In this refactor we assume only main ticks call this
        label_position = config['label_position']
        
        if label_position in ["right", "both"]:
            canvas.create_text(center_x + offset, y_coordinate, text=label_text, fill=text_color, font=frame.tick_font, anchor="w", tags="static")
        if label_position in ["left", "both"]:
            canvas.create_text(center_x - offset, y_coordinate, text=label_text, fill=text_color, font=frame.tick_font, anchor="e", tags="static")

    @staticmethod
    def draw_horizontal(canvas, frame, width, height, cy, available_width, padding, tick_length_half, slot_height, cap_width=DEFAULT_CAP_WIDTH):
        """Draws the ticks and labels for the horizontal fader."""
        tick_values = ScaleDrawer._get_tick_values(frame)
        label_interval, draw_interval = ScaleDrawer._calculate_tick_intervals(len(tick_values))
        config = ScaleDrawer._get_tick_configuration(frame)
        
        # Determine label position (default to both for horizontal if not specified or vertical-specific)
        label_pos = frame.widget_config.get("style", {}).get("tick_label_position", "both")
        if label_pos in ["left", "right"]: label_pos = "both" # Sanitize for horizontal

        value_range = frame.max_val - frame.min_val
        
        for index, value in enumerate(tick_values):
            norm_val = max(0.0, min(1.0, (value - frame.min_val) / value_range if value_range != 0 else 0))
            display_norm = max(1e-7, norm_val) ** (1.0 / frame.log_exponent) if frame.log_exponent != 1.0 else norm_val
            tick_x = available_width * display_norm + padding
            
            is_main_tick = (index % label_interval == 0)
            
            if index % draw_interval == 0:
                color = config['tick_color'] if is_main_tick else config['sub_tick_color']
                # Draw tick lines (above and below slot)
                canvas.create_line(tick_x, cy - slot_height/2 - TICK_LINE_GAP, tick_x, cy - slot_height/2 - TICK_LINE_GAP - tick_length_half, 
                                   fill=color, width=frame.tick_thickness, tags="static")
                canvas.create_line(tick_x, cy + slot_height/2 + TICK_LINE_GAP, tick_x, cy + slot_height/2 + TICK_LINE_GAP + tick_length_half, 
                                   fill=color, width=frame.tick_thickness, tags="static")
            
            if is_main_tick:
                label_text = str(int(value)) if value == int(value) else f"{value:.1f}"
                text_color = config['tick_text_color']
                offset = tick_length_half + 8
                
                if label_pos in ["top", "both"]:
                    canvas.create_text(tick_x, cy - offset - slot_height/2, text=label_text, fill=text_color, font=frame.tick_font, anchor="s", tags="static")
                if label_pos in ["bottom", "both"]:
                    canvas.create_text(tick_x, cy + offset + slot_height/2, text=label_text, fill=text_color, font=frame.tick_font, anchor="n", tags="static")
