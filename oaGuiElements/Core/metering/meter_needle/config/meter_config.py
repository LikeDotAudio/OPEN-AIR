# config/meter_config.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from oaStyle.Core.style import THEMES, DEFAULT_THEME
from oaGuiElements.Core.metering.meter_needle.Core.constants import COLOR_WHITE, COLOR_BLACK, NEEDLE_SCALES, SCALE_PADDINGS

class MeterConfig:
    """Dynamically maps configuration attributes from JSON payload to Python properties."""
    
    # Simple attribute mapping: (source_dict_name, key, default_val, type_caster)
    _MAPPINGS = {
        "label": ("config", "label_active", None, str),
        "path": ("config", "path", None, str),
        "show_label": ("config", "show_label", True, bool),
        "font_size": ("layout", "font", 10, int),
        "custom_colour": ("layout", "colour", None, str),
        "width": ("geometry", "width", 0, int),
        "height": ("geometry", "height", 0, int),
        "min_val": ("config", "min", -20.0, float),
        "max_val": ("config", "max", 3.0, float),
        "red_zone_start": ("config", "upper_range", 0.0, float),
        "tick_step": ("config", "step", None, float),
        "sub_tick_style": ("config", "sub_tick_style", "line", str),
        "needle_thickness": ("config", "Needle_thickness", 3, int),
        "scale_numbers": ("config", "Scale_numbers", True, bool),
        "ticks_visible": ("config", "Ticks_visible", True, bool),
        "curve_thickness": ("config", "curve_thickness", 4, int),
        "meter_viewable_angle": ("config", "Meter_viewable_angle", 90.0, float),
        "meter_center_angle": ("config", "Meter_center_angle", 90.0, float),
        "counter_clockwise": ("config", "Counter_Clockwise", False, bool),
        "custom_ticks": ("config", "custom_ticks", None, list),
        "sub_ticks": ("config", "sub_ticks", 0, int),
        "label_overrides": ("config", "label_overrides", {}, dict),
        "pointer_style": ("config", "Pointer_Style", "line", str),
        "pivot_size": ("config", "Pivot_size", 10, int),
        "pivot_crop": ("config", "pivot_crop", 0.0, float),
        "meter_mode": ("config", "meter_mode", "mono", str),
        "pointer_colour_2": ("config", "Pointer_colour_2", "#FF0000", str),
        "glide_time": ("config", "glide_time", 100.0, float),
        "dwell_time": ("config", "dwell_time", 100.0, float),
        "hold_time": ("config", "hold_time", 0.0, float),
        "fall_time": ("config", "fall_time", 100.0, float),
        "peak_hold_ms": ("config", "peak_hold_ms", 2000.0, float),
        "peak_flag": ("config", "Peak_flag", True, bool),
        "pivot_offset_x": ("style_overrides", "pivot_offset_x", 0.0, float),
        "pivot_offset_y": ("style_overrides", "pivot_offset_y", 0.0, float),
        "tick_length_override": ("style_overrides", "tick_length", None, float),
        "sub_tick_length_override": ("style_overrides", "sub_tick_length", None, float),
        "arc_radius_offset": ("style_overrides", "arc_radius_offset", None, float),
        "tick_radius_offset": ("style_overrides", "tick_radius_offset", None, float),
        "label_radius_offset": ("style_overrides", "label_radius_offset", None, float),
        "needle_length_factor_override": ("style_overrides", "needle_length_factor", None, float),
    }

    def __init__(self, config_data):
        self.config = config_data
        self.layout = self.config.get("layout", {})
        self.geometry = self.config.get("geometry", {})
        self.cosmetics = self.config.get("cosmetics", {})
        self.colors_cfg = self.cosmetics.get("colors", {})
        self.style_overrides = self.cosmetics.get("style_overrides", {})
        self.pointer = self.cosmetics.get("pointer", {})

        self.theme_colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
        self.default_theme_bg = self.theme_colors.get("bg", "#2b2b2b")
        self.accent_color = self.theme_colors.get("accent", "#33A1FD")
        self.secondary_color = self.theme_colors.get("secondary", "#444444")
        self.danger_color = "#FF4500"

    def __getattr__(self, name):
        if name in self._MAPPINGS:
            src_name, key, default, t_cast = self._MAPPINGS[name]
            value = getattr(self, src_name).get(key)
            if value is None and src_name == "config":
                value = self.style_overrides.get(key)
                if value is None:
                    value = self.pointer.get(key)
            if value is None:
                value = default
            if value is None: return None
            try:
                if t_cast == str:
                    v_str = str(value)
                    return v_str.lower() if name in ["pointer_style", "meter_mode"] else v_str
                return t_cast(value)
            except: return default
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")

    # --- Complex Fallback Properties ---

    @property
    def widget_label_color(self):
        return self.custom_colour or self.theme_colors.get("fg", COLOR_WHITE)

    @property
    def intended_bg(self): return "transparent"

    @property
    def is_transparent(self): return True

    @property
    def bezel_shape(self):
        return self.style_overrides.get("bezel_shape", "").lower()

    @property
    def faceplate_color(self):
        c = self.colors_cfg.get("meter_face_colour") or self.config.get("meter_face_colour") or self.colors_cfg.get("faceplate")
        return c if c else ("transparent" if self.bezel_shape else "#e0d4b4")

    @property
    def canvas_bg(self): return self.default_theme_bg

    @property
    def fg_color(self):
        c = self.colors_cfg.get("foreground", self.config.get("fg_color", ""))
        return c if c else self.theme_colors.get("fg", "#dcdcdc")

    @property
    def scale_label_color(self):
        return self.colors_cfg.get("scale_label", self.colors_cfg.get("foreground", COLOR_BLACK))

    @property
    def scale_padding(self):
        return SCALE_PADDINGS.get(self.bezel_shape, SCALE_PADDINGS["default"]) if self.bezel_shape else 20

    @property
    def needle_scale(self):
        return NEEDLE_SCALES.get(self.bezel_shape, NEEDLE_SCALES["default"])

    @property
    def size(self):
        return int(self.geometry.get("width", self.layout.get("width", self.config.get("size", 150))))

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
        v = self.config.get("reff_point", self.config.get("zero_point"))
        return float(v) if v is not None else None

    @property
    def pointer_colour(self):
        return self.config.get("Pointer_colour", self.config.get("pointer_colour", self.accent_color))

    @property
    def pointer_style_2(self):
        return self.config.get("Pointer_Style_2", self.pointer_style).lower()

    @property
    def pivot_colour(self):
        return self.config.get("Pivot_colour", self.config.get("pivot_colour", self.fg_color))

    @property
    def mask(self):
        m = self.style_overrides.get("mask", self.config.get("mask"))
        if m is not None: return m
        return (self.meter_viewable_angle <= 100) and (abs(self.meter_center_angle - 90) < 1)

    @property
    def needle_thickness_2(self):
        return int(self.config.get("Needle_thickness_2", self.needle_thickness))

    @property
    def pivot_offset_x_2(self):
        return float(self.style_overrides.get("pivot_offset_x_2", self.pivot_offset_x))

    @property
    def pivot_offset_y_2(self):
        return float(self.style_overrides.get("pivot_offset_y_2", self.pivot_offset_y))