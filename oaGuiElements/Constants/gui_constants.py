# oaGuiElements/Constants/gui_constants.py
# Author: Gemini (Collaborator)
# Version: 20260324.1.0
#
# Description: Standard GUI Element constants for layout, animation and defaults.

# Grid and Spacing
DEFAULT_COLUMN_SPACING = [80, 10, 10]
GRID_ROW_WEIGHT_TOP = 3
GRID_ROW_WEIGHT_BOTTOM = 7
GRID_ROW_MINSIZE_TOP = 25
GRID_ROW_MINSIZE_BOTTOM = 50

# Composite Dial Constants
DIAL_MAX_VALUE = 999.0
DIAL_WRAP_THRESHOLD = 999
KNOB_SAFE_DIM_MIN = 30
KNOB_SAFE_DIM_MAX = 100
KNOB_SAFE_DIM_DEFAULT = 40
V_WIDTH_LIMIT_RATIO = 8

# Wink Button Constants
WINK_OPEN_SPEED_DEFAULT = 0.08
WINK_CLOSE_SPEED_DEFAULT = 0.15
WINK_MASK_THICKNESS = 200
WINK_FRAME_THICKNESS = 4
WINK_BORDER_THICKNESS = 2

# Colors
COLOR_GREY_128 = (128, 128, 128)
COLOR_GREY_128_ALPHA = (128, 128, 128, 255)
COLOR_BLACK_RGB = (0, 0, 0)
COLOR_TRANSPARENT_HEX = "transparent"

# Other Defaults
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2
DEFAULT_FONT_SIZE = 12
DEFAULT_DECIMAL_PLACES = 2

# Panel Defaults
DEFAULT_PANEL_CONFIG = {
    "type": "layered_industrial",
    "parameters": {
        "random_seed": 304,
        "global_blur": 0.5,
        "base_material": {
            "color": "#2a2a2a",
            "texture_type": "brushed",
            "grain_intensity": 0.35
        },
        "paint_layer": {
            "color": "#3a4a5a",
            "opacity": 0.15,
            "gradient_intensity": 0.2
        },
        "edge_wear": {
            "enabled": True,
            "fade_depth": 30,
            "vignette_intensity": 0.5
        }
    }
}
