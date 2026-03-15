from workers.styling.style import THEMES, DEFAULT_THEME
from workers.builder.meter_needle.constants import COLOR_WHITE, NEEDLE_SCALES

class MeterConfig:
    def __init__(self, config_data):
        self.config = config_data
        self.layout_config = self.config.get("layout", {})
        self.geometry_config = self.config.get("geometry", {})
        self.cosmetics = self.config.get("cosmetics", {})
        self.colors_cfg = self.cosmetics.get("colors", {})

        # Theme Resolution
        self.theme_colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        self.default_theme_bg = self.theme_colors.get("bg", "#2b2b2b")
        self.accent_color = self.theme_colors.get("accent", "#33A1FD")
        self.secondary_color = self.theme_colors.get("secondary", "#444444")
        self.danger_color = "#FF4500"

    @property
    def label(self):
        return self.config.get("label_active")

    @property
    def path(self):
        return self.config.get("path")

    @property
    def show_label(self):
        return self.config.get("show_label", True)

    @property
    def font_size(self):
        return self.layout_config.get("font", 10)
    
    @property
    def custom_colour(self):
        return self.layout_config.get("colour", None)

    @property
    def widget_label_color(self):
        # Default to theme foreground (white-ish) for the instrument title
        return self.custom_colour or self.theme_colors.get("fg", COLOR_WHITE)

    @property
    def intended_bg(self):
        # STRICT ENFORCEMENT: The area outside the bezel is ALWAYS transparent
        # to allow the industrial panel texture to show through.
        return "transparent"

    @property
    def is_transparent(self):
        # Always True for Next Gen meters
        return True

    @property
    def faceplate_color(self):
        """The color of the card INSIDE the bezel."""
        # ⚡ Support for both root level and nested cosmetics keys
        color = self.colors_cfg.get("meter_face_colour") or \
                self.config.get("meter_face_colour") or \
                self.colors_cfg.get("faceplate")
        
        if color:
            return color
            
        # ⚡ HIGH-FIDELITY DEFAULT: If we have a custom bezel, default to transparent 
        # to show the industrial panel texture unless specifically overridden.
        if self.bezel_shape:
            return "transparent"
            
        return "#e0d4b4" # Classic beige for standard meters

    @property
    def canvas_bg(self):
        return self.default_theme_bg

    @property
    def fg_color(self):
        c = self.colors_cfg.get("foreground", self.config.get("fg_color", ""))
        return c if c.lower() != "" else self.theme_colors.get("fg", "#dcdcdc")

    @property
    def scale_label_color(self):
        # Default to the cosmetic foreground color if explicitly provided, else black
        # This ensures high contrast on dark backgrounds if the user set a light foreground.
        from workers.builder.meter_needle.constants import COLOR_BLACK
        return self.colors_cfg.get("scale_label", self.colors_cfg.get("foreground", COLOR_BLACK))

    @property
    def bezel_shape(self):
        return self.cosmetics.get("style_overrides", {}).get("bezel_shape", "").lower()

    @property
    def scale_padding(self):
        # SPECIFIC: Per-shape scale padding (e.g. Badge 90)
        from workers.builder.meter_needle.constants import SCALE_PADDINGS
        has_custom_bezel = "bezel_shape" in self.cosmetics.get("style_overrides", {})
        if not has_custom_bezel:
            return 20
        return SCALE_PADDINGS.get(self.bezel_shape, SCALE_PADDINGS["default"])

    @property
    def needle_scale(self):
        # SPECIFIC: Per-shape needle scaling (e.g. Hex .8)
        return NEEDLE_SCALES.get(self.bezel_shape, NEEDLE_SCALES["default"])

    @property
    def size(self):
        return int(self.geometry_config.get("width", self.layout_config.get("width", self.config.get("size", 150))))
    
    @property
    def width(self):
        return int(self.geometry_config.get("width", self.config.get("width", 0)))

    @property
    def height(self):
        return int(self.geometry_config.get("height", self.config.get("height", 0)))

    @property
    def min_val(self):
        return float(self.config.get("min", -20.0))

    @property
    def max_val(self):
        return float(self.config.get("max", 3.0))

    @property
    def red_zone_start(self):
        return float(self.config.get("upper_range", 0.0))

    @property
    def value_default(self):
        return float(self.config.get("value_default", self.min_val))

    @property
    def resting_point(self):
        return float(self.config.get("resting_point", self.min_val))

    @property
    def lower_colour(self):
        return self.config.get("Lower_range_colour", self.config.get("lower_range_colour", "green"))

    @property
    def middle_colour(self):
        return self.config.get("Middle_range_colour", self.config.get("middle_range_colour", "#FFD700"))

    @property
    def upper_colour(self):
        return self.config.get("upper_range_Colour", self.config.get("upper_range_colour", self.config.get("Upper_range_colour", self.danger_color)))

    @property
    def mid_range_start(self):
        return float(self.config.get("mid_range", self.red_zone_start))

    @property
    def anchor_point(self):
        val = self.config.get("reff_point", self.config.get("zero_point"))
        return float(val) if val is not None else None

    @property
    def tick_step(self):
        val = self.config.get("step")
        return float(val) if val is not None else None

    @property
    def sub_tick_style(self):
        return self.config.get("sub_tick_style", "line")

    @property
    def pointer_colour(self):
        return self.config.get("Pointer_colour", self.config.get("pointer_colour", self.accent_color))

    @property
    def needle_thickness(self):
        return int(self.config.get("Needle_thickness", 3))

    @property
    def scale_numbers(self):
        return self.config.get("Scale_numbers", True)

    @property
    def ticks_visible(self):
        return self.config.get("Ticks_visible", True)

    @property
    def curve_thickness(self):
        return int(self.config.get("curve_thickness", 4))

    @property
    def meter_viewable_angle(self):
        return float(self.config.get("Meter_viewable_angle", 90.0))

    @property
    def meter_center_angle(self):
        return float(self.config.get("Meter_center_angle", 90.0))

    @property
    def counter_clockwise(self):
        return self.config.get("Counter_Clockwise", False)

    @property
    def custom_ticks(self):
        return self.config.get("custom_ticks", None)

    @property
    def sub_ticks(self):
        return int(self.config.get("sub_ticks", 0))

    @property
    def label_overrides(self):
        return self.config.get("label_overrides", {})

    @property
    def pointer_style(self):
        return self.config.get("Pointer_Style", "line").lower()

    @property
    def pointer_style_2(self):
        return self.config.get("Pointer_Style_2", self.pointer_style).lower()

    @property
    def pivot_size(self):
        return int(self.config.get("Pivot_size", 10))

    @property
    def pivot_colour(self):
        return self.config.get("Pivot_colour", self.config.get("pivot_colour", self.fg_color))
    
    @property
    def pivot_crop(self):
        return float(self.config.get("pivot_crop", 0.0))

    @property
    def mask(self):
        default_mask = (self.meter_viewable_angle <= 100) and (abs(self.meter_center_angle - 90) < 1)
        return self.config.get("mask", default_mask)

    @property
    def meter_mode(self):
        return self.config.get("meter_mode", "mono").lower()

    @property
    def pointer_colour_2(self):
        return self.config.get("Pointer_colour_2", "#FF0000")

    @property
    def needle_thickness_2(self):
        return int(self.config.get("Needle_thickness_2", self.needle_thickness))
    
    @property
    def glide_time(self):
        return float(self.config.get("glide_time", 100))

    @property
    def dwell_time(self):
        return float(self.config.get("dwell_time", 100))

    @property
    def hold_time(self):
        return float(self.config.get("hold_time", 0))

    @property
    def fall_time(self):
        return float(self.config.get("fall_time", 100))

    @property
    def peak_hold_ms(self):
        return float(self.config.get("peak_hold_ms", 2000))
    
    @property
    def peak_flag(self):
        return self.config.get("Peak_flag", True)

    # --- Pivot Offsets ---
    @property
    def pivot_offset_x(self):
        return float(self.cosmetics.get("style_overrides", {}).get("pivot_offset_x", 0.0))

    @property
    def pivot_offset_y(self):
        return float(self.cosmetics.get("style_overrides", {}).get("pivot_offset_y", 0.0))

    @property
    def pivot_offset_x_2(self):
        return float(self.cosmetics.get("style_overrides", {}).get("pivot_offset_x_2", self.pivot_offset_x))

    @property
    def pivot_offset_y_2(self):
        return float(self.cosmetics.get("style_overrides", {}).get("pivot_offset_y_2", self.pivot_offset_y))

    # --- Style Overrides (New) ---
    @property
    def tick_length_override(self):
        return self.cosmetics.get("style_overrides", {}).get("tick_length", None)

    @property
    def sub_tick_length_override(self):
        return self.cosmetics.get("style_overrides", {}).get("sub_tick_length", None)

    @property
    def arc_radius_offset(self):
        # Pixel offset for the main arc radius
        return self.cosmetics.get("style_overrides", {}).get("arc_radius_offset", None)

    @property
    def tick_radius_offset(self):
        # Pixel offset for the ticks radius
        return self.cosmetics.get("style_overrides", {}).get("tick_radius_offset", None)

    @property
    def label_radius_offset(self):
        # Pixel offset for the text labels radius
        return self.cosmetics.get("style_overrides", {}).get("label_radius_offset", None)

    @property
    def needle_length_factor_override(self):
        # Float factor (e.g., 1.0, 1.2) to scale needle length
        return self.cosmetics.get("style_overrides", {}).get("needle_length_factor", None)
