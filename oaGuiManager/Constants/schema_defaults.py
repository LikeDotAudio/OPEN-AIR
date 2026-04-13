# Constants/schema_defaults.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Default schema mappings, lexicons, and structural constants.

LEXICON = {
    "lbl": "label", 
    "w": "width", 
    "h": "height", 
    "value": "value_default", 
    "min": "min", 
    "max": "max",
    "bg": "bg_color", 
    "fg": "text_color", 
    "unit": "units"
}

# Structural widget types that default to transparency
STRUCT_TYPES = ["OcaBlock", "OcaBin", "OcaArray", "Block", "Array"]

# Semantic Layout Constants
DEFAULT_PANEL_PERCENTAGE = 50
ANCHOR_MAP = {
    "top": "n", 
    "bottom": "s", 
    "left": "w", 
    "right": "e"
}

# Industry Standard Defaults
DEFAULT_COLORS = {
    "active_text": "#1a1a1a",
    "inactive_text": "#888888",
    "active_accent": "#FF9900",
    "panel_bg": "#2b2b2b"
}

# The 5 pillars of the "Universal Rhyme" schema
PILLARS = ["identity", "geometry", "domain", "dynamics", "cosmetics"]
