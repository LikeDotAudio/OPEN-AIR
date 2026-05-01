# oaGui/Core/factory/button_canvas_base.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Shared Base Class for photorealistic Canvas-based buttons.

import tkinter as tk
from oaGui.Methods.button_image_renderer import ButtonImageRenderer

class CanvasButton(tk.Canvas):
    """
    A base class for creating photorealistic buttons using PIL and Tkinter Canvas.
    """
    def __init__(self, parent, text="", command=None, width=100, height=50,
                 corner_radius=6, bg_color="#1a1a1a", active_color="#FF9900",
                 active_bg_color="#000000", text_color="#888888",
                 active_text_color="#1a1a1a", glow_intensity=1.0,
                 active_font_style="bold", active_font_size=None,
                 inactive_font_style="normal", inactive_font_size=None,
                 alpha=1.0, font=("TkDefaultFont", 10),
                 transparency_applicator=None, config=None, builder=None, **kwargs):

        self.button_config = {
            "bg_color": bg_color,
            "active_color": active_color,
            "active_bg_color": active_bg_color,
            "text_color": text_color,
            "active_text_color": active_text_color,
            "glow_intensity": glow_intensity,
            "corner_radius": corner_radius,
            "alpha": alpha
        }
        
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
        if not self.command: return
        try:
            self.command(event)
        except TypeError:
            self.command()

    def _draw(self):
        for item in self.find_all():
            tags = self.gettags(item)
            if "panel_bg_slice" not in tags:
                self.delete(item)

        w, h = self.winfo_width(), self.winfo_height()
        if int(w) <= 1 or int(h) <= 1: return

        self.img = ButtonImageRenderer.create_button_image(
            w, h, self.text, self.is_active, self.is_hovered, self.is_pressed, self.button_config
        )
        self.create_image(0, 0, image=self.img, anchor="nw", tags="button_img")
        self.tag_lower("button_img")
