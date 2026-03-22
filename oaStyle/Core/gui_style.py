# Core/gui_style.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: Configures and applies global TTK styles for the application.

import tkinter as tk
from tkinter import ttk

class GuiStyleMixin:
    """Configures and applies global TTK styles for the application."""

    def _blend_colors(self, color1, color2, alpha):
        """Blends two colors based on alpha (0.0 to 1.0)."""
        try:
            # Convert hex/name to RGB
            rgb1 = self.winfo_rgb(color1)
            rgb2 = self.winfo_rgb(color2)
            
            # winfo_rgb returns 16-bit values (0-65535)
            r = int((rgb1[0] * (1 - alpha) + rgb2[0] * alpha) / 256)
            g = int((rgb1[1] * (1 - alpha) + rgb2[1] * alpha) / 256)
            b = int((rgb1[2] * (1 - alpha) + rgb2[2] * alpha) / 256)
            
            return f'#{r:02x}{g:02x}{b:02x}'
        except Exception as e:
            return color1 # Fallback
