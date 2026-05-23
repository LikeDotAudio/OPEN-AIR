# oaGui/Workers/compositing/sync_behavior.py
# Author: Anthony Peter Kuzub
# Version: 20260222.Adapter.1
#
# Description: Defines behavior for synchronizing background textures across the UI tree.

import tkinter as tk

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log

from .engine_visual_effects import EngineVisualEffects


class SyncBehavior:
    """Defines behavior for synchronizing background textures across the UI tree."""

    def _apply_transparency(self, target_widget, canvas, configuration, builder_instance):
        """Bridge to the EngineVisualEffects."""
        EngineVisualEffects.apply_transparency(target_widget, canvas, configuration, builder_instance)

    def register_for_bg_sync(self, widget, canvas, configuration, context):
        """
        Registers a widget for automatic background synchronization with its parent.
        """
        builder_instance = context.builder_instance if context else None
        parent = widget.master
        widget_name = getattr(widget, 'path', type(widget).__name__)

        def perform_sync(event=None):
            if not widget.winfo_exists(): return

            try:
                # ⚡ LIGHTWEIGHT CHECK: Ensure widget is physically realized
                w, h = widget.winfo_width(), widget.winfo_height()
                if w <= 1 or h <= 1: return
            except tk.TclError: return

            try:
                # ⚡ COLOR SYNC: Match parent's background color
                p_bg = parent.cget("bg")
                if widget.cget("bg") != p_bg:
                    widget.configure(bg=p_bg)
                if canvas and canvas.winfo_exists() and canvas.cget("bg") != p_bg:
                    canvas.configure(bg=p_bg)

                # ⚡ SLICING: Use stored slice method if available
                # Note: Transparent widgets are already registered with the builder's
                # centralized registry via EngineVisualEffects.
                if hasattr(widget, '_perform_background_slice'):
                    widget._perform_background_slice()

            except Exception as e:
                matrix_log("UI", "GUI_MANAGER", "perform_sync", f"perform_sync error for {widget_name}: {e}", level="TRACE")

        # Sync immediately once the widget is mapped to the screen
        widget.bind("<Map>", perform_sync, add="+")

        # ⚡ OPTIMIZATION: Removed parent.bind("<Configure>").
        # This was causing layout thrashing in dense modules like EDAC.
        # Background updates are now driven by the Orchestrator's debounced _trigger_reslice_all().
