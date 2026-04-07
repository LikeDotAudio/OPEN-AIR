# Core/knob_config.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from oaStyle.Core.style import THEMES, DEFAULT_THEME

def extract_knob_config(config_data):
    """
    Extracts and normalizes configuration for the Rotary Knob.
    Robustly handles nested Universal Rhyme schema and flat legacy keys.
    """
    c = config_data
    
    # 1. Block Extraction
    cosmetics = c.get("cosmetics", {})
    styling = cosmetics.get("styling", {})
    overrides = cosmetics.get("style_overrides", {})
    pointer = cosmetics.get("pointer", {})
    scale = cosmetics.get("scale", c.get("scale", {}))
    readout = c.get("readout", {})
    interaction = c.get("interaction", {})
    domain = c.get("domain", {})
    primary_domain = domain.get("primary", domain)
    
    # 2. Theme and Color Resolution
    themes = THEMES.get(DEFAULT_THEME, THEMES["dark"])
    colors = cosmetics.get("colors", {})
    
    accent_color = colors.get("primary", themes.get("accent", "#33A1FD"))
    bg_color = colors.get("background", themes.get("bg", "#2b2b2b"))
    fg_color = colors.get("fg", themes.get("fg", "#dcdcdc"))
    secondary_color = colors.get("secondary", themes.get("secondary", "#444444"))
    
    indicator_color = c.get("indicator_color", colors.get("active", accent_color))

    # 3. Domain and Range
    min_val = float(primary_domain.get("min", c.get("min", 0.0)))
    max_val = float(primary_domain.get("max", c.get("max", 100.0)))
    reff_point = float(primary_domain.get("reff_point", (min_val + max_val) / 2.0))
    
    val_def_raw = primary_domain.get("value_default", c.get("value_default", 0.0))
    try:
        value_default = float(val_def_raw)
    except (ValueError, TypeError):
        value_default = val_def_raw # Keep as string/other if not a float
    
    # 4. Interaction
    infinity = interaction.get("infinity", c.get("infinity", False))
    fine_pitch = interaction.get("fine_pitch", c.get("fine_pitch", False))
    
    # 5. Geometry
    geom = c.get("geometry", {})
    width = geom.get("width", c.get("width", 50))
    height = geom.get("height", c.get("height", 50))
    
    # 6. Readout and Labels
    text_pos = readout.get("label_position", c.get("label_Text_position", "top")).lower()
    show_label = readout.get("show_label", c.get("show_label", True))
    text_inside = readout.get("text_inside", c.get("text_inside", False))
    
    # 7. Aesthetics (The "Pattern" fix)
    # We probe overrides -> styling -> cosmetics -> top-level
    visualization = cosmetics.get("visualization", c.get("visualization", "")).lower()
    
    knob_style = overrides.get("knob_style", styling.get("knob_style", c.get("knob_style", "standard"))).lower()
    shape = overrides.get("shape", styling.get("shape", c.get("shape", "circle"))).lower()
    
    if visualization:
        if visualization in ["panner", "dial", "standard"]:
            knob_style = visualization
        elif visualization in ["circle", "octagon", "gear"]:
            shape = visualization
    
    no_center = styling.get("no_center", c.get("no_center", False))
    arc_width = int(styling.get("arc_width", c.get("arc_width", 5)))
    gradient_level = int(styling.get("gradient", styling.get("gradient_level", c.get("gradient_level", 0))))
    
    # Teeth for Gear knobs
    knob_teeth = int(styling.get("teeth", c.get("knob_teeth", 8)))
    
    # Outline
    knob_outline_thickness = int(styling.get("outline_thickness", c.get("knob_outline_thickness", 0)))
    knob_outline_color = styling.get("outline_color", c.get("knob_outline_color", secondary_color))
    knob_fill_color = styling.get("fill_color", c.get("knob_fill_color", ""))

    # 8. Pointer Configuration
    pointer_style = pointer.get("style", c.get("pointer_style", "line")).lower()
    pointer_length = pointer.get("length", c.get("pointer_length", None))
    pointer_offset = int(pointer.get("offset", c.get("pointer_offset", 0)))

    # 9. Scale and Ticks
    show_ticks = scale.get("show", c.get("show_ticks", False))
    tick_length = int(scale.get("length", c.get("tick_length", 10)))
    tick_style = scale.get("style", c.get("tick_style", "simple")).lower()

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