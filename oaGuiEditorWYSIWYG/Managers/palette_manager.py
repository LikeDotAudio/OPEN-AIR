# Managers/palette_manager.py
# Author: Gemini
# Version: 20260404.1.0
#
# Description: Manages undockable and stackable tool palettes for the WYSIWYG editor.

import tkinter as tk
from tkinter import ttk
from loguru import logger
from oaLogging.Methods.matrix_gate import matrix_log

class PaletteManager(tk.Frame):
    def __init__(self, parent, tool_panels, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.tool_panels_config = tool_panels # List of dicts: [{"widget": instance, "name": "Name"}]
        self.visible_panels = {} # Track currently visible panels by name
        self.detached_windows = {} # Track detached Toplevel windows

        self._build_ui()

    def _build_ui(self):
        self.pack(fill="both", expand=True) # PaletteManager frame itself packs into its parent

        # Create a header for dropdowns or controls
        header_frame = ttk.Frame(self, style="Dark.TFrame")
        header_frame.pack(side="top", fill="x", pady=2)
        
        ttk.Label(header_frame, text="Palettes:", style="DarkLabel.TLabel").pack(side="left", padx=5)

        # Dropdown for showing/hiding panels
        self.panel_options = [panel["name"] for panel in self.tool_panels_config]
        self.selected_panel_var = tk.StringVar()
        self.panel_dropdown = ttk.Combobox(
            header_frame, 
            textvariable=self.selected_panel_var, 
            values=self.panel_options, 
            state="readonly", 
            width=15
        )
        self.panel_dropdown.pack(side="left", padx=5)
        self.panel_dropdown.bind("<<ComboboxSelected>>", self._on_panel_selected)

        # Container for the panels themselves
        self.panel_container = ttk.Frame(self, style="Dark.TFrame")
        self.panel_container.pack(side="top", fill="both", expand=True)

        # Initially pack all panels
        for panel_config in self.tool_panels_config:
            panel_name = panel_config["name"]
            panel_widget = panel_config["widget"]
            
            # Initially hide them, will be shown via dropdown
            panel_widget.pack_forget() 
            self.visible_panels[panel_name] = False
            
            # Make sure panel_widget's parent is the panel_container if it's meant to be embedded
            # This requires the widget to be reparented or instantiated with the correct parent
            # For now, assume widget was created with self.panel_container as parent in WysiwygEditor
            
            # Add a button to undock the panel
            ttk.Button(header_frame, text=f"Undock {panel_name}", command=lambda name=panel_name: self._undock_panel(name)).pack(side="right", padx=5)

    def _on_panel_selected(self, event):
        selected_panel_name = self.selected_panel_var.get()
        self.toggle_panel_visibility(selected_panel_name)
        self.selected_panel_var.set("") # Clear selection after action

    def toggle_panel_visibility(self, panel_name):
        for panel_config in self.tool_panels_config:
            if panel_config["name"] == panel_name:
                panel_widget = panel_config["widget"]
                if self.visible_panels[panel_name]:
                    panel_widget.pack_forget()
                    self.visible_panels[panel_name] = False
                    matrix_log("ui", "palette_manager", "_toggle_panel_visibility", f"PaletteManager: Hiding panel: {panel_name}", "DEBUG")
                else:
                    panel_widget.pack(in_=self.panel_container, fill="both", expand=True) # Pack into our container
                    self.visible_panels[panel_name] = True
                    matrix_log("ui", "palette_manager", "_toggle_panel_visibility", f"PaletteManager: Showing panel: {panel_name}", "DEBUG")
                return

    def _undock_panel(self, panel_name):
        if panel_name in self.detached_windows and self.detached_windows[panel_name].winfo_exists():
            self.detached_windows[panel_name].lift()
            self.detached_windows[panel_name].focus_set()
            return

        for panel_config in self.tool_panels_config:
            if panel_config["name"] == panel_name:
                panel_widget = panel_config["widget"]
                
                # Create Toplevel window
                top_level = tk.Toplevel(self)
                top_level.title(f"Palette: {panel_name}")
                top_level.geometry("400x300")
                
                # Make the panel widget a child of the Toplevel
                panel_widget.pack_forget() # Unpack from current parent
                panel_widget.pack(in_=top_level, fill="both", expand=True) # Pack into Toplevel

                def on_toplevel_close():
                    matrix_log("ui", "palette_manager", "_undock_panel", f"PaletteManager: Detached window for {panel_name} closed.", "INFO")
                    panel_widget.pack_forget() # Remove from Toplevel
                    # Repack into original container when detached window is closed (optional, for re-docking)
                    # For now, just mark it as hidden
                    self.visible_panels[panel_name] = False 
                    if panel_name in self.detached_windows:
                        del self.detached_windows[panel_name]
                    top_level.destroy()
                    
                top_level.protocol("WM_DELETE_WINDOW", on_toplevel_close)
                
                self.detached_windows[panel_name] = top_level
                self.visible_panels[panel_name] = True # Panel is now visible in detached window
                matrix_log("ui", "palette_manager", "_undock_panel", f"PaletteManager: Undocked panel: {panel_name}", "INFO")
                return

    def get_widget(self):
        """Returns the main frame of the PaletteManager for packing into parent."""
        return self