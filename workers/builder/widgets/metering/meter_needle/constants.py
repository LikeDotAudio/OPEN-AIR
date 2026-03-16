# workers/builder/meter_needle/constants.py

# Colors
COLOR_WHITE = "#ffffff"
COLOR_BLACK = "#000000"
COLOR_DANGER_RED = "#FF4500"
COLOR_GOLD = "#FFD700"
COLOR_DARK_GREY = "#2b2b2b"
COLOR_ACCENT_BLUE = "#33A1FD"
COLOR_SECONDARY_GREY = "#444444"

# General Geometry
SAFE_MARGIN = 10
LINE_WIDTH_DEFAULT = 12

# Shape Multipliers (Width, Height)
# These represent the 'Maximum Extents' of the shape relative to R.
# Used to calculate the Radius (R) so the shape fits the canvas.
SHAPE_MULTIPLIERS = {
    "gem": (1.9, 2.4),       
    "super_gem": (1.9, 2.4),
    "triangle": (2.0, 2.0),   
    "parking_meter": (2.0, 2.5),
    "pyramid": (2.0, 2.0),    
    "hotdog": (2.91, 3.5),   
    "cylinder": (1.85, 1.3),
    "hex": (2.52, 2.6),      
    "octagon": (1.5, 1.5),
    "squircle": (1.2, 3.5),
    "squimonde": (1.9, 1.9),
    "squectangle": (1.7, 2.1),
    "trapezoid": (1.8, 2.6), 
    "badge": (1.8, 2.6),     
    "crest": (1.5, 2.1),      
    "stereo_diamond": (3.5, 2.5), 
    "intersecting_overlay": (4.0, 2.25),
    "default": (1.5, 1.5)
}

# Shape Vertical Shifts (Relative to R)
# Positive shifts move the shape UP relative to the pivot.
SHAPE_Y_SHIFTS = {
    "hotdog": 1.30,  
    "pyramid": 0.5,   
    "triangle": 0.5,  
    "parking_meter": 0.5,
    "hex": 0.5,      
    "octagon": 0.9,
    "squircle": 0.4,
    "squimonde": 0.014,
    "squectangle": 0.4, 
    "crest": 0.2,     
    "badge": 0.3,    
    "trapezoid": 0.3,
    "gem": 0.5,      
    "super_gem": 0.5,
    "stereo_diamond": 0.0,
    "intersecting_overlay": 0.0,
    "default": 0.0
}

# Expansion Factors (Bezel only, doesn't affect needle/scale)
GEM_BEZEL_EXPANSION = 3.06  
HEX_BEZEL_EXPANSION = 1.4  
OCTAGON_BEZEL_EXPANSION = 1.4
TRIANGLE_BEZEL_EXPANSION = 4.32 
PARKING_METER_BEZEL_EXPANSION = 4.32
PYRAMID_BEZEL_EXPANSION = 4.32

# Custom Needle Scales (Per Shape)
# Multiplier applied to the needle length R.
NEEDLE_SCALES = {
    "hex": 0.8,      
    "octagon": 0.8,
    "gem": 0.75,      
    "super_gem": 0.75,
    "squimonde": 0.5,
    "pyramid": 0.65,   
    "triangle": 1.235,  
    "parking_meter": 1.35,
    "badge": 0.9625,    
    "trapezoid": 0.9625,
    "stereo_diamond": 0.9,
    "intersecting_overlay": 1.2,
    "default": 1.0
}

# Scale Paddings (Internal Instrument Shrink)
# Higher values shrink the arch/ticks more.
SCALE_PADDINGS = {
    "badge": 90,
    "trapezoid": 90,
    "triangle": 140,
    "parking_meter": 110,
    "pyramid": 75,
    "gem": 50,
    "super_gem": 50,
    "octagon": 50,
    "squimonde": 180,
    "squectangle": 50,
    "squircle": 110,
    "stereo_diamond": 50, 
    "intersecting_overlay": 50,
    "default": 50
}

# Squircle / Squectangle Constants
SQUIRCLE_N = 3.5
SQUIRCLE_WIDTH_FACTOR = 1.0
SQUIRCLE_HEIGHT_FACTOR = 1.0
SQUECTANGLE_WIDTH_FACTOR = 1.7
SQUECTANGLE_HEIGHT_FACTOR = 0.85
SQUIRCLE_STEPS = 40

# Crest Constants
CREST_CURVE_STEPS = 15
CREST_TOP_WIDTH_FACTOR = 1.5
CREST_TOP_HEIGHT_FACTOR = 1.76 
CREST_BOTTOM_HEIGHT_FACTOR = 0.6

# Cylinder / Hotdog Constants
HOTDOG_WIDTH_STRAIGHT = 1.9 
HOTDOG_HEIGHT_TOTAL = 2.02 
HOTDOG_CAP_RADIUS = 1.01
HOTDOG_CAP_CENTER_Y = 1.01

CYLINDER_WIDTH_STRAIGHT = 1.2
CYLINDER_HEIGHT_TOTAL = 1.3
CYLINDER_CAP_RADIUS = 0.65
CYLINDER_CAP_CENTER_Y = 0.6

CYLINDER_STEPS = 10

# Gem Constants
GEM_WIDTH_FACTOR = 0.51
GEM_BASE_HEIGHT = 0.3
GEM_SHOULDER_WIDTH = 0.69
GEM_SHOULDER_HEIGHT = 0.6
GEM_PEAK_HEIGHT = 0.98

# Stereo Diamond Constants (14x10 grid -> 1.4:1 ratio)
STEREO_DIAMOND_WIDTH = 1.4 
STEREO_DIAMOND_HEIGHT = 1.0 
STEREO_DIAMOND_FLAT_WIDTH = 0.6 

# Intersecting Overlay Constants (16:9 ratio -> 1.77:1)
INTERSECTING_OVERLAY_WIDTH = 1.77
INTERSECTING_OVERLAY_HEIGHT = 1.0
INTERSECTING_OVERLAY_SKEW = 0.3 
INTERSECTING_OVERLAY_CUTOUT_RADIUS = 0.4 

# Triangle Constants
TRIANGLE_SHIFT_Y = 0.4
TRIANGLE_BASE_WIDTH = 1.8
TRIANGLE_PEAK_HEIGHT = 1.7

# Pyramid Constants
PYRAMID_BASE_WIDTH = 1.8
PYRAMID_PEAK_HEIGHT = 1.7

# Hex Constants
HEX_MID_WIDTH = 1.8
HEX_MID_HEIGHT = 0.8
HEX_TOP_WIDTH = 1.2
HEX_TOP_HEIGHT = 1.8

# Trapezoid/Badge Constants
TRAPEZOID_TOP_WIDTH = 1.6
TRAPEZOID_TOP_HEIGHT = 1.6 
TRAPEZOID_BOTTOM_WIDTH = 1.3

# Hill Mask / Aperture Constants
HILL_CONFIGS = {
    "hotdog": (2.5, 0.3),
    "gem": (0.8, 0.3),
    "super_gem": (0.4, 0.3),
    "hex": (1.8, 0.3),
    "octagon": (1.8, 0.3),
    "triangle": (0.2, 0.1),
    "pyramid": (0.2, 0.1),
    "parking_meter": (0.2, 0.1),
    "squircle": (0.5, 0.3),
    "squimonde": (0.5, 0.3),
    "crest": (1.0, 0.3),
    "squectangle": (0.7, 0.3),
    "trapezoid": (1.2, 0.3),
    "default": (1.5, 0.3)
}

# Lens Constants
LENS_GLOW_STEPS = 10
LENS_GLOW_SHRINK_MAX = 60
LENS_SHADOW_STEPS = 15
LENS_SHADOW_DEPTH = 12.0

# Scale Constants
SCALE_TICK_LENGTH = 8
SCALE_SUB_TICK_LENGTH = 4
SCALE_TEXT_OFFSET = 15
SCALE_DEFAULT_STEPS = 6
SCALE_SUB_TICK_WIDTH = 1
SCALE_MAIN_TICK_WIDTH = 2
SCALE_SUB_TICK_DOT_RADIUS = 1.5

# Number Constants
NUMBER_FONT_FAMILY = "Helvetica"
NUMBER_FONT_SIZE = 8

# Layout Constants
LAYOUT_PADDING_DEFAULT = 20
LAYOUT_LABEL_PADDING_X = 15
LAYOUT_LABEL_PADDING_Y_TOP = 5
LAYOUT_LABEL_PADDING_Y_BOTTOM = 15
LAYOUT_CANVAS_MARGIN_W = 20
LAYOUT_CANVAS_MARGIN_H = 10
LAYOUT_OFFSET_X = 10
LAYOUT_OFFSET_Y = 2
LAYOUT_PIVOT_CROP_MIN_H = 10
LAYOUT_LABEL_PAD_Y_TOP = 0
LAYOUT_LABEL_PAD_Y_BOTTOM = 5
