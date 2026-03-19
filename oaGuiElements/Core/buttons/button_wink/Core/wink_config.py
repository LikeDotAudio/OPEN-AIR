from oaStyle.Core.style import THEMES, DEFAULT_THEME

def extract_wink_config(config_data):
    """Extracts and normalizes configuration for the Wink Button."""
    config = config_data
    
    # Shape and Size
    shape_type = config.get("shape_type", "rect").lower()
    width = config.get("width", 60)
    height = config.get("height", 60) if shape_type != "round" else width
    radius = config.get("radius", 5)
    
    # Colors
    bg_color = config.get("color", "#39FF14")
    shutter_color = config.get("shutter_color", "black")
    
    theme_colors = THEMES.get(DEFAULT_THEME, THEMES["dark"])
    default_bg = theme_colors.get("bg", "#2b2b2b")
    bezel_color = config.get("bezel_color", default_bg)
    
    # Text
    text_closed = config.get("text_closed", "")
    if isinstance(text_closed, str) and " " in text_closed:
        text_closed = text_closed.replace(" ", "\n")
    text_closed_color = config.get("text_closed_color", "white" if shutter_color == "black" else "black")
    
    text_inside = config.get("text_inside", "")
    if text_inside == "":
        text_inside = None
    if isinstance(text_inside, str) and " " in text_inside:
        text_inside = text_inside.replace(" ", "\n")
    text_inside_color = config.get("text_inside_color", "black")
    
    font_size_cfg = config.get("font_size")
    font_size_closed_cfg = config.get("font_size_closed")
    
    # Border/Lens
    border_thickness = config.get("border_thickness", 2)
    default_border_color = "#333333" if shutter_color.lower() in ["black", "#000000"] else "black"
    border_color = config.get("border_color", default_border_color)
    
    # Glass Lens specific (New)
    use_glass_lens = config.get("use_glass_lens", True) # Default to true as per request? Or false for compatibility?
    # User said: "intead of a border to the buttons, i would like it to resembel a glass lens."
    # So if use_glass_lens is true, we might suppress the border or integrate it.
    
    # Physics/Animation
    open_duration = config.get("open_speed", 150)
    close_duration = config.get("close_speed", 300)
    
    if 0 < open_duration < 1.0: open_duration = 16 / open_duration
    if 0 < close_duration < 1.0: close_duration = 16 / close_duration

    open_inc = 16 / open_duration if open_duration > 0 else 1.0
    close_inc = 16 / close_duration if close_duration > 0 else 1.0

    blink_interval = config.get("blink_interval", 0)
    
    # Logic
    is_latching = config.get("latching", False)
    is_locked_init = config.get("LOCKED", False)
    value_default = config.get("value_default", False)
    
    label_pos = config.get("label_position", "top").lower()
    
    return {
        "shape_type": shape_type,
        "width": width,
        "height": height,
        "radius": radius,
        "bg_color": bg_color,
        "shutter_color": shutter_color,
        "bezel_color": bezel_color,
        "text_closed": text_closed,
        "text_closed_color": text_closed_color,
        "text_inside": text_inside,
        "text_inside_color": text_inside_color,
        "font_size": font_size_cfg,
        "font_size_closed": font_size_closed_cfg,
        "border_thickness": border_thickness,
        "border_color": border_color,
        "use_glass_lens": use_glass_lens,
        "open_inc": open_inc,
        "close_inc": close_inc,
        "blink_interval": blink_interval,
        "is_latching": is_latching,
        "is_locked_init": is_locked_init,
        "value_default": value_default,
        "label_position": label_pos,
        "text_align": config.get("text_align", "center").lower()
    }
