# oaGuiEditorWYSIWYG/Managers/palette_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260416.0230.1
#
# Description: UI Orchestrator for Tool Palettes (Docking, Visibility, Selection).

import tkinter as tk
from tkinter import ttk
from .palette.palette_docking import PaletteDockingService
from .palette.palette_visibility import PaletteVisibilityService

class PaletteManager(tk.Frame):
    """
    Orchestrates the lifecycle of multiple tool palettes.
    Provides a header with selection dropdown and undocking controls.
    """
    
    def __init__(self, parent, tool_panels, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.tool_panels = tool_panels
        self._panel_states = {p["name"]: False for p in tool_panels}

        self._build_scaffolding()
        
        # Services
        self.visibility_service = PaletteVisibilityService(self.panel_container, self._panel_states)
        self.docking_service = PaletteDockingService(self, self.tool_panels, self._panel_states)

        self._initialize_panels()

    def _build_scaffolding(self):
        """Constructs the palette container UI."""
        self.pack(fill="both", expand=True)

        # 1. Header with Controls
        header = ttk.Frame(self, style="Dark.TFrame")
        header.pack(side="top", fill="x", pady=2)
        ttk.Label(header, text="Palettes:", style="DarkLabel.TLabel").pack(side="left", padx=5)

        # Dropdown for panel selection
        self.selected_panel_var = tk.StringVar()
        self.panel_dropdown = ttk.Combobox(
            header, 
            textvariable=self.selected_panel_var, 
            values=[p["name"] for p in self.tool_panels], 
            state="readonly", 
            width=15
        )
        self.panel_dropdown.pack(side="left", padx=5)
        self.panel_dropdown.bind("<<ComboboxSelected>>", self._on_panel_dropdown_select)

        # Quick undock buttons
        for panel in self.tool_panels:
            ttk.Button(header, text=f"⏏ {panel['name']}", 
                       command=lambda n=panel["name"]: self.docking_service.undock_panel(n)).pack(side="right", padx=2)

        # 2. Main Stackable Container
        self.panel_container = ttk.Frame(self, style="Dark.TFrame")
        self.panel_container.pack(side="top", fill="both", expand=True)

    def _initialize_panels(self):
        """Ensures all panels start in a hidden state."""
        self.visibility_service.hide_all(self.tool_panels)

    def _on_panel_dropdown_select(self, event):
        """Event handler for manual panel selection via dropdown."""
        name = self.selected_panel_var.get()
        panel_widget = self._find_widget_by_name(name)
        if panel_widget:
            self.visibility_service.toggle_visibility(name, panel_widget)
        self.selected_panel_var.set("")

    def _find_widget_by_name(self, name):
        """Helper to retrieve a panel widget from the configuration."""
        for p in self.tool_panels:
            if p["name"] == name:
                return p["widget"]
        return None

    def toggle_panel_visibility(self, panel_name):
        """Public API for programmatic panel toggling."""
        panel_widget = self._find_widget_by_name(panel_name)
        if panel_widget:
            self.visibility_service.toggle_visibility(panel_name, panel_widget)

    def shutdown(self):
        """Cleanly releases all palette resources and detached windows."""
        self.docking_service.cleanup()
