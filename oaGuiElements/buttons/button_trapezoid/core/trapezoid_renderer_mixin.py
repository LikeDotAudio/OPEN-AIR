import math
from oaStyle.style import THEMES, DEFAULT_THEME

# Default Dimensions
DEFAULT_BUTTON_WIDTH = 80
DEFAULT_BUTTON_HEIGHT = 50
LABEL_HEIGHT_ADJUSTMENT = 25
WIDTH_SCALING_FACTOR = 0.8
HEIGHT_SCALING_FACTOR = 0.8

# Rendering Constants
PRESSED_OFFSET_Y = 4
SHADOW_OFFSET_X = 2
SHADOW_OFFSET_Y = 6
BEVEL_WIDTH_RATIO = 0.15
TOP_SHRINK_RATIO = 0.1
INDICATOR_WIDTH_RATIO = 0.4
INDICATOR_HEIGHT_RATIO = 0.15
INDICATOR_Y_RATIO = 0.2
GLOW_WIDTH_RATIO = 1.5
GLOW_HEIGHT_RATIO = 2.0
LABEL_VERTICAL_OFFSET = 10

# Color Adjustment Factors
PRESSED_LIGHTNESS_FACTOR = 0.8
NORMAL_LIGHTNESS_FACTOR = 1.0
TOP_BEVEL_LIGHT_FACTOR = 1.2
TOP_BEVEL_PRESSED_FACTOR = 0.9
BOTTOM_BEVEL_FACTOR = 0.5
SIDE_BEVEL_FACTOR = 0.7

# Fonts
BUTTON_TEXT_FONT = ("Arial", 9, "bold")
LABEL_TEXT_FONT = ("Arial", 8, "bold")

class TrapezoidRendererMixin:
    """Handles the rendering logic and mathematics for the 3D Trapezoidal button."""

    def render_trapezoid_button(self, canvas, configuration, rendering_state):
        """Draws the complete trapezoid button assembly."""
        canvas.delete("button_elements")
        
        # Preserve industrial background
        for item in canvas.find_all():
            tags = canvas.gettags(item)
            if "panel_bg_slice" not in tags and "industrial_text" not in tags:
                canvas.delete(item)

        if hasattr(canvas, 'panel_bg_image') and not canvas.find_withtag("panel_bg_slice"):
            canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")

        canvas_width = int(canvas.winfo_width()) if canvas.winfo_width() > 1 else configuration.get("width", DEFAULT_BUTTON_WIDTH)
        canvas_height = int(canvas.winfo_height()) if canvas.winfo_height() > 1 else configuration.get("height", DEFAULT_BUTTON_HEIGHT) + (LABEL_HEIGHT_ADJUSTMENT if rendering_state.get("label") else 0)

        center_x, center_y = canvas_width / 2, canvas_height / 2
        button_width, button_height = canvas_width * WIDTH_SCALING_FACTOR, configuration.get("height", DEFAULT_BUTTON_HEIGHT) * HEIGHT_SCALING_FACTOR

        is_pressed = rendering_state.get("pressed", False)
        is_lit = rendering_state.get("lit", False)
        base_color = rendering_state.get("base_color", "#8B0000")
        led_color = rendering_state.get("led_color", "#FF0000")
        button_text = configuration.get("button_text", "")
        label_text = rendering_state.get("label")

        # Offset for pressed state
        delta_y = PRESSED_OFFSET_Y if is_pressed else 0

        # Colors
        shadow_color = "#111111"
        face_color = self.adjust_color_lightness(base_color, PRESSED_LIGHTNESS_FACTOR if is_pressed else NORMAL_LIGHTNESS_FACTOR)
        top_bevel_color = self.adjust_color_lightness(base_color, TOP_BEVEL_LIGHT_FACTOR if not is_pressed else TOP_BEVEL_PRESSED_FACTOR)
        bottom_bevel_color = self.adjust_color_lightness(base_color, BOTTOM_BEVEL_FACTOR)
        side_bevel_color = self.adjust_color_lightness(base_color, SIDE_BEVEL_FACTOR)
        indicator_color = led_color if is_lit else "#330000"

        # Geometry
        base_x = center_x - button_width / 2
        base_y = center_y - button_height / 2 - (LABEL_VERTICAL_OFFSET if label_text else 0)
        if label_text:
            base_y += LABEL_VERTICAL_OFFSET
        
        y_offset_coordinate = base_y + delta_y
        bevel_width = button_width * BEVEL_WIDTH_RATIO
        top_shrink_amount = button_width * TOP_SHRINK_RATIO

        outer_points = [
            base_x, y_offset_coordinate + button_height, 
            base_x + top_shrink_amount, y_offset_coordinate, 
            base_x + button_width - top_shrink_amount, y_offset_coordinate, 
            base_x + button_width, y_offset_coordinate + button_height
        ]
        inner_points = [
            base_x + bevel_width, y_offset_coordinate + button_height - bevel_width, 
            base_x + top_shrink_amount + bevel_width * 0.5, y_offset_coordinate + bevel_width,
            base_x + button_width - top_shrink_amount - bevel_width * 0.5, y_offset_coordinate + bevel_width, 
            base_x + button_width - bevel_width, y_offset_coordinate + button_height - bevel_width
        ]

        # Draw Layers
        if not is_pressed:
            shadow_points = [
                base_x - SHADOW_OFFSET_X, base_y + button_height + SHADOW_OFFSET_Y, 
                base_x + top_shrink_amount - SHADOW_OFFSET_X, base_y + SHADOW_OFFSET_Y, 
                base_x + button_width - top_shrink_amount + SHADOW_OFFSET_X, base_y + SHADOW_OFFSET_Y, 
                base_x + button_width + SHADOW_OFFSET_X, base_y + button_height + SHADOW_OFFSET_Y
            ]
            canvas.create_polygon(shadow_points, fill=shadow_color, outline="", tags="button_elements")

        canvas.create_polygon(outer_points, fill=face_color, outline="#222222", width=1, tags="button_elements")
        
        # Bevels
        canvas.create_polygon([outer_points[0], outer_points[1], inner_points[0], inner_points[1], inner_points[6], inner_points[7], outer_points[6], outer_points[7]], fill=bottom_bevel_color, outline="", tags="button_elements")
        canvas.create_polygon([outer_points[2], outer_points[3], inner_points[2], inner_points[3], inner_points[4], inner_points[5], outer_points[4], outer_points[5]], fill=top_bevel_color, outline="", tags="button_elements")
        canvas.create_polygon([outer_points[0], outer_points[1], inner_points[0], inner_points[1], inner_points[2], inner_points[3], outer_points[2], outer_points[3]], fill=side_bevel_color, outline="", tags="button_elements")
        canvas.create_polygon([outer_points[6], outer_points[7], inner_points[6], inner_points[7], inner_points[4], inner_points[5], outer_points[4], outer_points[5]], fill=side_bevel_color, outline="", tags="button_elements")
        
        canvas.create_polygon(inner_points, fill=face_color, outline="", tags="button_elements")

        # Indicator
        indicator_width, indicator_height = button_width * INDICATOR_WIDTH_RATIO, button_height * INDICATOR_HEIGHT_RATIO
        indicator_x, indicator_y = center_x - indicator_width / 2, y_offset_coordinate + button_height * INDICATOR_Y_RATIO
        canvas.create_rectangle(indicator_x, indicator_y, indicator_x + indicator_width, indicator_y + indicator_height, fill=indicator_color, outline="#111111", width=1, tags="button_elements")

        if is_lit:
            glow_width = indicator_width * GLOW_WIDTH_RATIO
            glow_height = indicator_height * GLOW_HEIGHT_RATIO
            glow_x = center_x - glow_width / 2
            glow_y = indicator_y + indicator_height / 2 - glow_height / 2
            canvas.create_oval(glow_x, glow_y, glow_x + glow_width, glow_y + glow_height, fill="", outline=indicator_color, width=2, stipple="gray50", tags="button_elements")

        if button_text:
            canvas.create_text(center_x, y_offset_coordinate + button_height * 0.6, text=button_text, fill="white", font=BUTTON_TEXT_FONT, tags="button_elements")

        if label_text:
            foreground_color = THEMES.get(DEFAULT_THEME, THEMES["dark"]).get("fg", "#dcdcdc")
            canvas.delete("industrial_text")
            canvas.create_text(center_x, base_y - LABEL_VERTICAL_OFFSET, text=label_text, fill=foreground_color, font=LABEL_TEXT_FONT, anchor="s", tags="industrial_text")

    def adjust_color_lightness(self, hex_color, factor):
        """Helper to lighten/darken a hex color."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3: 
            hex_color = ''.join([char * 2 for char in hex_color])
        try:
            red, green, blue = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            red = max(0, min(255, int(red * factor)))
            green = max(0, min(255, int(green * factor)))
            blue = max(0, min(255, int(blue * factor)))
            return f"#{red:02x}{green:02x}{blue:02x}"
        except Exception: 
            return "#8B0000"
