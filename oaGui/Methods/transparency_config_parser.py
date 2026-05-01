# oaGui/Methods/transparency_config_parser.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Parses transparency-related configurations for GUI widgets.

import tkinter as tk
from oaStyle.Constants.geometry import STRUCTURAL_WIDGET_TYPES, THEME_BACKGROUND_COLORS

class TransparencyConfigParser:
    """
    Parses transparency-related configurations for GUI widgets.
    """
    @staticmethod
    def parse_configuration(configuration, widget):
        background_color = configuration.get("bg_color") or configuration.get("bg") or configuration.get("background_color")
        if not background_color:
            style_settings = configuration.get("style", {})
            if isinstance(style_settings, dict):
                background_color = style_settings.get("background_color") or style_settings.get("bg_color") or style_settings.get("bg")

        is_structural_type = any(configuration.get(key) in STRUCTURAL_WIDGET_TYPES for key in ["type", "widget_type"])
        is_virtual_container = is_structural_type and isinstance(widget, tk.Canvas)

        background_string = str(background_color).lower() if background_color else ""

        # Keywords that explicitly signal transparency
        trans_keywords = ["transparent", "none", "match_theme"]

        is_explicitly_solid = (background_color and
                               background_string not in THEME_BACKGROUND_COLORS and
                               background_string not in trans_keywords)

        is_explicitly_transparent = (background_string in trans_keywords) or \
                                    (configuration.get("transparent") is True) or \
                                    is_virtual_container or \
                                    is_structural_type

        return background_string, is_explicitly_solid, is_explicitly_transparent
