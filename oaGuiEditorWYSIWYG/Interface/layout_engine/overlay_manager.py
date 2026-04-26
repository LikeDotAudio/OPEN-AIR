# oaGuiEditorWYSIWYG/Interface/layout_engine/overlay_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260416.01.0
#
# Description: Modularized design control injector.

import tkinter as tk

from .overlays.alignment_overlay import AlignmentOverlay

# Import modular overlay classes
from .overlays.selection_overlay import SelectionOverlay
from .overlays.sizing_overlay import SizingOverlay


class OverlayManager:
    """Orchestrates the injection of designer overlays onto live widgets."""

    def __init__(self, workspace):
        self.workspace = workspace
        self.active_overlays = {} # path -> [BaseOverlay, ...]
        self.event_blocker_canvas = None

        # Registry of functional overlay classes
        self.overlay_registry = [
            SelectionOverlay,
            AlignmentOverlay,
            SizingOverlay
        ]

    def create_event_blocker(self, parent_widget):
        """Creates a transparent canvas to prevent interaction with preview widgets."""
        if self.event_blocker_canvas:
            self.event_blocker_canvas.destroy()

        self.event_blocker_canvas = tk.Canvas(parent_widget, highlightthickness=0, bd=0)
        for event in ["<Button-1>", "<Button-2>", "<Button-3>", "<Motion>", "<MouseWheel>"]:
            self.event_blocker_canvas.bind(event, lambda e: "break")

        self.show_event_blocker(False)

    def show_event_blocker(self, show=True):
        """Toggles the visibility of the event-blocking layer."""
        if not self.event_blocker_canvas:
            return

        if show:
            parent = self.event_blocker_canvas.master
            if parent.winfo_width() > 1 and parent.winfo_height() > 1:
                self.event_blocker_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            self.event_blocker_canvas.place_forget()

    def apply_outlines(self, container):
        """Top-level entry point to refresh all designer overlays for a container."""
        if not container or not container.winfo_exists():
            return

        self._recursive_clear(container)
        self._recursive_apply(container)

    def _recursive_clear(self, container):
        """Recursively clears all existing design overlays and state."""
        # 1. Clear established overlay class instances
        for overlays in self.active_overlays.values():
            for overlay in overlays:
                overlay.destroy()
        self.active_overlays.clear()

        # 2. Cleanup orphaned design widgets (for robustness)
        self._clear_orphaned_design_widgets(container)

    def _clear_orphaned_design_widgets(self, container):
        """Recursively destroys any widget marked as a design overlay."""
        for child in list(container.winfo_children()):
            if getattr(child, '_is_design_overlay', False):
                try:
                    child.destroy()
                except Exception:
                    pass
            elif isinstance(child, (tk.Frame, tk.Canvas, tk.LabelFrame)):
                self._clear_orphaned_design_widgets(child)

    def _recursive_apply(self, container, depth=0):
        """Recursively injects designer controls into widgets with valid paths."""
        if depth > 10:
            return

        for child in container.winfo_children():
            if getattr(child, '_is_design_overlay', False):
                continue

            path = getattr(child, '_oca_path', None)
            if path and "unknown" not in path:
                self._inject_modular_controls(child, path)

            if isinstance(child, (tk.Frame, tk.Canvas, tk.LabelFrame)):
                self._recursive_apply(child, depth + 1)

    def _inject_modular_controls(self, widget, path):
        """Instantiates and syncs modular overlay classes for a specific widget."""
        is_focused = (self.workspace.focused_path == path)
        overlay_instances = []

        for overlay_cls in self.overlay_registry:
            instance = overlay_cls(self.workspace, widget, path, is_focused)
            overlay_instances.append(instance)

        self.active_overlays[path] = overlay_instances

        def _sync_pos(event=None):
            """Syncs overlay elements with the widget's physical bounds."""
            if not widget.winfo_exists():
                return
            try:
                bounds = (widget.winfo_x(), widget.winfo_y(), widget.winfo_width(), widget.winfo_height())
                if bounds[2] <= 1 or bounds[3] <= 1:
                    return
                for instance in overlay_instances:
                    instance.sync(*bounds)
            except (tk.TclError, ValueError):
                pass

        # Bind sync to widget resize and trigger initial sync
        widget.bind("<Configure>", _sync_pos, add="+")
        widget.after(100, _sync_pos)
