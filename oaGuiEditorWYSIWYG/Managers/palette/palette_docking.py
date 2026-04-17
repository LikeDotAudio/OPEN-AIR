# oaGuiEditorWYSIWYG/Managers/palette/palette_docking.py
# Author: Anthony Peter Kuzub
# Version: 20260416.0230.1
#
# Description: Service for undocking/redocking tool panels into Toplevel windows.

import tkinter as tk
from oaLogging.Methods.matrix_gate import matrix_log

class PaletteDockingService:
    """Handles the lifecycle of detached (Toplevel) palette panels."""
    
    def __init__(self, container_widget, tool_panels_config, visibility_tracker):
        self.container = container_widget
        self.tool_panels = tool_panels_config
        self.visibility_tracker = visibility_tracker
        self.detached_windows = {}

    def undock_panel(self, panel_name):
        """Moves a panel from the main container to a new Toplevel window."""
        if self._focus_existing_detached(panel_name):
            return

        for panel_config in self.tool_panels:
            if panel_config["name"] == panel_name:
                self._create_detached_window(panel_name, panel_config["widget"])
                return

    def _focus_existing_detached(self, panel_name):
        """Brings an already detached window to the front."""
        if panel_name in self.detached_windows and self.detached_windows[panel_name].winfo_exists():
            self.detached_windows[panel_name].lift()
            self.detached_windows[panel_name].focus_set()
            return True
        return False

    def _create_detached_window(self, panel_name, panel_widget):
        """Spawns a new window and reparents the panel widget into it."""
        top_level = tk.Toplevel(self.container)
        top_level.title(f"Palette: {panel_name}")
        top_level.geometry("400x300")
        
        # Reparenting logic
        panel_widget.pack_forget()
        panel_widget.pack(in_=top_level, fill="both", expand=True)

        def on_close():
            self._handle_detached_close(panel_name, top_level, panel_widget)
            
        top_level.protocol("WM_DELETE_WINDOW", on_close)
        
        self.detached_windows[panel_name] = top_level
        self.visibility_tracker[panel_name] = True
        matrix_log("ui", "palette_manager", "undock_panel", f"📱🎨🖱️ [MOBILE] PaletteManager: Undocked panel: {panel_name}", "INFO")
        
    def _handle_detached_close(self, panel_name, top_level, panel_widget):
        """Cleans up state when a detached window is closed by the user."""
        matrix_log("ui", "palette_manager", "on_toplevel_close", f"📱🎨🛌 [MOBILE] PaletteManager: Detached window for {panel_name} closed.", "INFO")
        panel_widget.pack_forget()
        self.visibility_tracker[panel_name] = False 
        if panel_name in self.detached_windows:
            del self.detached_windows[panel_name]
        top_level.destroy()

    def cleanup(self):
        """Cleanly destroy all detached windows during application shutdown."""
        for window in list(self.detached_windows.values()):
            if window.winfo_exists():
                window.destroy()
        self.detached_windows.clear()
