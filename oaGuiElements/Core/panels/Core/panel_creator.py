# Core/utils/panels/panel_creator.py
# Author: Anthony Peter Kuzub
# Version: 20260503.1600.1
#
# Description: Creator for procedural panel widgets.

import tkinter as tk
from PIL import ImageTk

from oaGui.Core.factory.base_widget_creator import BaseWidgetCreator
from oaGui.Hooks.registry.registry_widget_store import RegistryWidgetStore
from oaGui.Workers.compositing.sync_behavior import SyncBehavior
from .panel_generator import PanelGenerator

class PanelWidget(tk.Frame):
    """A widget that displays a procedurally generated industrial panel."""
    
    def __init__(self, master, config, **kwargs):
        super().__init__(master, **kwargs)
        self.config_data = config
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.panel_image = None
        self.tk_image = None
        
        self.canvas.bind("<Configure>", self._on_resize)
        
    def _on_resize(self, event):
        width = event.width
        height = event.height
        if width <= 1 or height <= 1: return
        
        # Generate the panel
        self.panel_image = PanelGenerator.generate_procedural_panel(width, height, self.config_data)
        if self.panel_image:
            self.tk_image = ImageTk.PhotoImage(self.panel_image)
            self.canvas.delete("panel_bg")
            self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw", tags="panel_bg")
            self.canvas.tag_lower("panel_bg")

@RegistryWidgetStore.register("panel", "Panel")
class BuilderPanelCreator(BaseWidgetCreator, SyncBehavior):
    """Creator for the procedural Panel widget."""
    
    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Assembles the Panel UI."""
        geom = config_data.get("geometry", {})
        width = geom.get("width", 200)
        height = geom.get("height", 150)
        
        frame = PanelWidget(parent_widget, config_data, width=width, height=height)
        return frame, frame.canvas

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        return BuilderPanelCreator.build(parent_widget, config_data, context, **kwargs)
