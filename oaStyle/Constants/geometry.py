# oaStyle/Constants/geometry.py
# Author: Anthony Peter Kuzub
# Version: 20260402.1.0
#
# Description: Centralized aesthetic and geometry constants for the OPEN-AIR UI.

# --- Splash Screen Animation (makegif.py) ---
SPLASH_FRAMES = 50
SPLASH_FPS = 20
SPLASH_WIDTH = 6
SPLASH_HEIGHT = 2.5
SPLASH_Y_LIMIT_MAX = 22
SPLASH_NUM_BARS = 120
SPLASH_BAR_WIDTH = 0.08
SPLASH_ENVELOPE_COEFFICIENT = -0.025
SPLASH_ENVELOPE_RANGE_LIMIT = 10
SPLASH_SPIKE_TRIGGER_CENTER = 3.5
SPLASH_SPIKE_TRIGGER_STEEPNESS = -8
SPLASH_LINE_OFFSET_STANDARD = 0.2
SPLASH_LINE_OFFSET_ELECTRIC = 0.3

# Splash Layer Heights
SPLASH_BASE_HEIGHT_L1 = 6
SPLASH_BASE_HEIGHT_L2 = 8
SPLASH_BASE_HEIGHT_L3 = 10
SPLASH_BASE_HEIGHT_L4 = 7
SPLASH_BASE_HEIGHT_L5 = 18

# --- Industrial Transparency (transparency.py) ---
MIN_WIDGET_DIMENSION = 1
PRE_LAYOUT_DIMENSION_LIMIT = 1
JITTER_THRESHOLD_PIXELS = 5
CENTER_SAMPLE_DIVISOR = 2
DEFAULT_THEME_BACKGROUND = "#2b2b2b"

# Structural widget types that default to transparency
STRUCTURAL_WIDGET_TYPES = [
    "OcaBlock", "OcaBin", "OcaArray", "OcaCollapsibleBlock",
    "Block", "Array", "Bin", "_Label", "_SmartLabel", "_GuiLabel", "Label"
]

# Standard background colors for theme matching
THEME_BACKGROUND_COLORS = [
    "#2b2b2b", "#3c3f41", "#4e5254", "#1a1a1a",
    "#000000", "#dcdcdc", "#f0f0f0"
]
