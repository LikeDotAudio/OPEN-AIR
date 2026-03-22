# Core/ui_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from .draw_bargraph import create_bar_graph_image

class ShowtimeUIMixin:
    """
    Mixin for managing the dynamic UI elements of the Showtime tab.
    """

    def _create_zone_buttons(self):
        """Generates the top-level zone filter buttons."""
        if not self.zone_frame: return
        for w in self.zone_frame.winfo_children(): w.destroy()
        
        zones = sorted(self.grouped_markers.keys())
        for zone in zones:
            style = "Selected.TButton" if self.selected_zone == zone else "Custom.TButton"
            btn = ttk.Button(self.zone_frame, text=zone, style=style, 
                             command=lambda z=zone: self.on_zone_toggle(z))
            btn.pack(side=tk.LEFT, padx=2)

    def _create_group_buttons(self):
        """Generates group filter buttons for the selected zone."""
        if not self.group_frame: return
        for w in self.group_frame.winfo_children(): w.destroy()
        
        if not self.selected_zone: return
        
        groups = sorted(self.grouped_markers[self.selected_zone].keys())
        for group in groups:
            style = "Selected.TButton" if self.selected_group == group else "Custom.TButton"
            btn = ttk.Button(self.group_frame, text=group, style=style,
                             command=lambda g=group: self.on_group_toggle(g))
            btn.pack(side=tk.LEFT, padx=2)

    def _create_device_buttons(self):
        """Generates the individual device/marker buttons with bar graphs."""
        if not self.device_frame: return
        for w in self.device_frame.winfo_children(): w.destroy()
        
        if not self.selected_zone or not self.selected_group: return
        
        devices = self.grouped_markers[self.selected_zone][self.selected_group]
        for dev in devices:
            name = dev.get("NAME", "Unknown")
            peak = float(dev.get("PEAK", -100))
            
            btn = self._create_button_with_bar_graph(self.device_frame, peak, name)
            btn.marker_data = dev
            btn.config(command=lambda b=btn: self.on_marker_button_click(b))
            btn.pack(side=tk.LEFT, padx=5, pady=5)

    def _create_button_with_bar_graph(self, parent, value, text):
        """Creates a specialized button with a procedural background image."""
        img_path = create_bar_graph_image(value, text)
        img = Image.open(img_path)
        photo = ImageTk.PhotoImage(img)
        
        button = ttk.Button(parent, image=photo)
        button.image = photo # GC Protection
        return button
