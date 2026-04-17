# oaGuiEditorWYSIWYG/Managers/palette/palette_visibility.py
# Author: Anthony Peter Kuzub
# Version: 20260416.0230.1
#
# Description: Service for managing the visibility/packing of internal palette panels.

from oaLogging.Methods.matrix_gate import matrix_log

class PaletteVisibilityService:
    """Manages the packing and unpacking of palette widgets within the stack."""
    
    def __init__(self, container_widget, visibility_tracker):
        self.container = container_widget
        self.visibility_tracker = visibility_tracker

    def toggle_visibility(self, panel_name, panel_widget):
        """Switches the packing state of a panel based on its tracked visibility."""
        is_visible = self.visibility_tracker.get(panel_name, False)
        
        if is_visible:
            self._hide_panel(panel_name, panel_widget)
        else:
            self._show_panel(panel_name, panel_widget)

    def _show_panel(self, name, widget):
        widget.pack(in_=self.container, fill="both", expand=True)
        self.visibility_tracker[name] = True
        matrix_log("ui", "palette_manager", "toggle", f"Palette: Showing panel {name}", "DEBUG")

    def _hide_panel(self, name, widget):
        widget.pack_forget()
        self.visibility_tracker[name] = False
        matrix_log("ui", "palette_manager", "toggle", f"Palette: Hiding panel {name}", "DEBUG")

    def hide_all(self, tool_panels):
        """Ensures all panels are removed from the display stack."""
        for panel in tool_panels:
            panel["widget"].pack_forget()
            self.visibility_tracker[panel["name"]] = False
