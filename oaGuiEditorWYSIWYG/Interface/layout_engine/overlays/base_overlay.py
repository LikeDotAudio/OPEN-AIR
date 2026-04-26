# oaGuiEditorWYSIWYG/Interface/layout_engine/overlays/base_overlay.py
# Author: Anthony Peter Kuzub
# Version: 20260416.01.0
#
# Description: Abstract base class for all layout design overlays.

import tkinter as tk


class BaseOverlay:
    """Standardized interface for all designer feedback overlays."""

    def __init__(self, workspace, widget, path, is_focused):
        self.workspace = workspace
        self.widget = widget
        self.path = path
        self.is_focused = is_focused
        self.elements = []
        self._is_active = True

    def create_element(self, widget_type, **kwargs):
        """Helper to create and track a design-only widget."""
        kwargs["master"] = self.widget.master
        element = widget_type(**kwargs)
        element._is_design_overlay = True
        self.elements.append(element)
        return element

    def sync(self, x, y, w, h):
        """Updates element positions. To be implemented by subclasses."""
        pass

    def destroy(self):
        """Cleans up all elements associated with this overlay."""
        for element in self.elements:
            try:
                if element.winfo_exists():
                    element.destroy()
            except tk.TclError:
                pass
        self.elements.clear()

    def hide(self):
        """Hides all elements from the layout."""
        for element in self.elements:
            element.place_forget()
