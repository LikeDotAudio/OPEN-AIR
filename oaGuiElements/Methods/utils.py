# Methods/utils.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from loguru import logger

from oaGuiElements.Constants.gui_constants import (
    COLOR_BLACK_RGB,
    COLOR_GREY_128,
    COLOR_GREY_128_ALPHA,
    COLOR_TRANSPARENT_HEX,
)


class PanelUtils:
    @staticmethod
    def hex_to_rgba(hex_str):
        if not isinstance(hex_str, str): return COLOR_GREY_128_ALPHA
        if hex_str.lower() == COLOR_TRANSPARENT_HEX: return (0, 0, 0, 0)
        c = hex_str.lstrip('#')
        try:
            rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
            return rgb[:3] + (255,)
        except Exception as e:
            logger.error(f"Failed to convert hex to rgba ({hex_str}): {e}")
            return COLOR_GREY_128_ALPHA

    @staticmethod
    def hex_to_rgb(hex_str):
        if not isinstance(hex_str, str): return COLOR_GREY_128
        if hex_str.lower() == COLOR_TRANSPARENT_HEX: return COLOR_BLACK_RGB # Return 3-tuple for consistency
        c = hex_str.lstrip('#')
        try:
            rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
            return rgb[:3] # Ensure only 3 components
        except Exception as e:
            logger.error(f"Failed to convert hex to rgb ({hex_str}): {e}")
            return COLOR_GREY_128
