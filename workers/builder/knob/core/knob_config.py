from workers.styling.style import THEMES, DEFAULT_THEME

def extract_knob_config(config_data):
    """Extracts and normalizes configuration for the Rotary Knob."""
    config = config_data
    
    colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
    bg_color = colors.get("bg", "#2b2b2b")
    fg_color = colors.get("fg", "#dcdcdc")
    accent_color = colors.get("accent", "#33A1FD")
    secondary_color = colors.get("secondary", "#444444")
    indicator_color = config.get("indicator_color", accent_color)

    min_val = float(config.get("min", 0.0))
    max_val = float(config.get("max", 100.0))
    reff_point = float(config.get("reff_point", (min_val + max_val) / 2.0))
    value_default = float(config.get("value_default", 0.0))
    infinity = config.get("infinity", False)
    fine_pitch = config.get("fine_pitch", False)
    
    width = config.get("width", 50)
    height = config.get("height", 50)
    
    text_pos = config.get("label_Text_position", "top").lower()
    show_label = config.get("show_label", True)
    
    text_inside = config.get("text_inside", False)
    no_center = config.get("no_center", False)
    show_ticks = config.get("show_ticks", False)
    tick_length = int(config.get("tick_length", 10))
    arc_width = int(config.get("arc_width", 5))
    
    pointer_length = config.get("pointer_length", None)
    pointer_offset = int(config.get("pointer_offset", 0)) 

    knob_style = config.get("knob_style", "standard").lower()
    shape = config.get("shape", "circle").lower()
    pointer_style = config.get("pointer_style", "line").lower()
    tick_style = config.get("tick_style", "simple").lower()
    gradient_level = int(config.get("gradient_level", 0))
    
    knob_outline_thickness = int(config.get("knob_outline_thickness", 0))
    knob_outline_color = config.get("knob_outline_color", secondary_color)
    knob_fill_color = config.get("knob_fill_color", "")
    knob_teeth = int(config.get("knob_teeth", 8))

    return {
        "bg_color": bg_color,
        "fg_color": fg_color,
        "accent_color": accent_color,
        "secondary_color": secondary_color,
        "indicator_color": indicator_color,
        "min": min_val,
        "max": max_val,
        "reff_point": reff_point,
        "value_default": value_default,
        "infinity": infinity,
        "fine_pitch": fine_pitch,
        "width": width,
        "height": height,
        "text_pos": text_pos,
        "show_label": show_label,
        "text_inside": text_inside,
        "no_center": no_center,
        "show_ticks": show_ticks,
        "tick_length": tick_length,
        "arc_width": arc_width,
        "pointer_length": pointer_length,
        "pointer_offset": pointer_offset,
        "knob_style": knob_style,
        "shape": shape,
        "pointer_style": pointer_style,
        "tick_style": tick_style,
        "gradient_level": gradient_level,
        "outline_thickness": knob_outline_thickness,
        "outline_color": knob_outline_color,
        "fill_color": knob_fill_color,
        "teeth": knob_teeth
    }
