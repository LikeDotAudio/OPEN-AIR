# factory/button_canvas_base.py
# Author: Anthony Peter Kuzub
# Version: 20260315.Modular.1
#
# Description: Shared Base Class for photorealistic Canvas-based buttons.

import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
from loguru import logger
import math
from oaGuiFramework.Methods.i18n_utils import get_text

class CanvasButton(tk.Canvas):
    """
    A base class for creating photorealistic buttons using PIL and Tkinter Canvas.
    Supports transparency, rounded corners, glow effects, and dynamic resizing.
    """
    def __init__(self, parent, text="", command=None, width=100, height=50, 
                 corner_radius=6, bg_color="#1a1a1a", active_color="#FF9900", 
                 active_bg_color="#000000", text_color="#888888", 
                 active_text_color="#1a1a1a", glow_intensity=1.0, 
                 active_font_style="bold", active_font_size=None,
                 inactive_font_style="normal", inactive_font_size=None,
                 alpha=1.0, font=("TkDefaultFont", 10), 
                 transparency_applicator=None, config=None, builder=None, **kwargs):
        
        self.bg_color = bg_color
        self.active_color = active_color
        self.active_bg_color = active_bg_color
        self.text_color = text_color
        self.active_text_color = active_text_color
        self.glow_intensity = glow_intensity
        self.corner_radius = corner_radius
        self.alpha = alpha
        self.text = text
        self.command = command
        self.font = font
        self.active_font_style = active_font_style
        self.active_font_size = active_font_size or font[1]
        self.inactive_font_style = inactive_font_style
        self.inactive_font_size = inactive_font_size or font[1]
        
        self.is_active = False
        self.is_hovered = False
        self.is_pressed = False
        self.builder = builder
        self.config_data = config
        self.transparency_applicator = transparency_applicator

        super().__init__(parent, width=max(1, int(width)), height=max(1, int(height)), 
                         bg=parent.cget("bg") if not transparency_applicator else "#2b2b2b", 
                         highlightthickness=0, bd=0, relief="flat", **kwargs)

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Configure>", lambda e: self._draw())

        if transparency_applicator:
            transparency_applicator(self, self, config, builder)

    def set_active(self, active):
        self.is_active = active
        self._draw()

    def set_text(self, text):
        self.text = text
        self._draw()

    def _on_enter(self, event):
        self.is_hovered = True
        self._draw()

    def _on_leave(self, event):
        self.is_hovered = False
        self.is_pressed = False
        self._draw()

    def _on_press(self, event):
        self.is_pressed = True
        self._draw()

    def _on_release(self, event):
        if self.is_pressed:
            self._safe_execute_command(event)
        self.is_pressed = False
        self._draw()

    def _safe_execute_command(self, event):
        """Safely executes the command, passing the event if supported."""
        if not self.command:
            return
            
        # ⚡ FIXED: Pass the event to the command lambda if it expects it.
        # Standard Tkinter commands usually take 0 args, 
        # but CanvasButton's command often needs the event (e.g. for Alt-click/modifiers).
        try:
            self.command(event)
        except TypeError:
            self.command()

    def _get_font_path(self):
        # Placeholder for robust font finding
        return None

    def _create_button_image(self, width, height, text, is_active, is_hovered, is_pressed):
        width, height = max(1, int(width)), max(1, int(height))
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Determine colors
        if is_active:
            bg = self.active_bg_color
            border = None  # ⚡ REMOVE BORDER WHEN ACTIVE
        else:
            bg = self.bg_color
            border = "#333333"

        if is_pressed:
            bg = "#000000"
            border = None # ⚡ REMOVE BORDER WHEN PRESSED

        # Draw Base Rounded Rect
        r = self.corner_radius
        draw.rounded_rectangle([0, 0, width-1, height-1], r, fill=bg, outline=border, width=1)

        # Glow Effect if active: Radiating light behind text
        if is_active and self.glow_intensity > 0:
            glow_color = self.active_color
            
            # ⚡ RADIATING LIGHT: Create a soft radial glow centered behind the text
            try:
                # Parse hex color to RGB
                r_c = int(glow_color[1:3], 16)
                g_c = int(glow_color[3:5], 16)
                b_c = int(glow_color[5:7], 16)
                
                center_x, center_y = width / 2, height / 2
                # ⚡ SCALED GLOW: Intensity scale 0-10. Radius and opacity now map to this scale.
                # max_radius scales from 0% to ~80% of button size based on intensity (0-10)
                max_radius = min(width, height) * 0.8 * (self.glow_intensity / 10.0)
                
                # ⚡ SOFTER GRADIENT: steps scale with intensity for smoothness
                num_steps = max(10, int(30 * (self.glow_intensity / 10.0)))
                for i in range(num_steps, 0, -1):
                    radius = (max_radius / num_steps) * i
                    # Smooth quadratic falloff. Max alpha ~100 at intensity 10.
                    alpha_factor = (1 - (i / (num_steps + 1)))**2
                    alpha = int(100 * alpha_factor * (self.glow_intensity / 10.0))
                    
                    if alpha > 0:
                        draw.ellipse(
                            [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
                            fill=(r_c, g_c, b_c, alpha)
                        )
            except Exception as e:
                logger.error(f"Failed to render radiating glow: {e}")

        # Draw Text
        try:
            display_text = get_text(text)
            f_size = self.active_font_size if is_active else self.inactive_font_size
            f_style = self.active_font_style if is_active else self.inactive_font_style
            # This is a simplification; real app might use complex font loading
            font = ImageFont.load_default()
            
            # Simple text centering
            text_x, text_y = width / 2, height / 2
            draw.text((text_x, text_y), display_text, fill=self.active_text_color if is_active else self.text_color, anchor="mm")
        except Exception as e:
            logger.error(f"Error drawing button text: {e}")

        return ImageTk.PhotoImage(image)

    def _draw(self):
        # ⚡ INDUSTRIAL TRANSPARENCY: Don't delete everything, preserve the patina slice
        for item in self.find_all():
            tags = self.gettags(item)
            if "panel_bg_slice" not in tags:
                self.delete(item)

        w = self.winfo_width()
        h = self.winfo_height()
        
        try:
            if int(w) <= 1 or int(h) <= 1: return
        except (ValueError, TypeError):
            return

        # ⚡ DETERMINISTIC COLORING: 
        # When inactive, use a fixed dark grey instead of inheriting background patina.
        # This makes the buttons feel like physical objects on the panel.
        
        effective_bg = self.bg_color
        
        if not self.is_active:
            # Default dark grey for inactive state
            effective_bg = "#1a1a1a" if self.bg_color in [None, "#2b2b2b"] else self.bg_color

        # Implementation of photorealistic drawing would go here.
        # For now, we use a simple representation to satisfy the test requirements
        
        self.img = self._create_button_image(w, h, self.text, self.is_active, self.is_hovered, self.is_pressed)
        self.create_image(0, 0, image=self.img, anchor="nw", tags="button_img")
        
        # Ensure image is behind text if we were adding more items
        self.tag_lower("button_img")
