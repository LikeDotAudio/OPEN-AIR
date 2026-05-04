# oaGui/Workers/compositing/sync_behavior.py
# Author: Anthony Peter Kuzub
# Version: 20260222.Adapter.1
#
# Description: Defines behavior for synchronizing background textures across the UI tree.

import inspect
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

        matrix_log("gui", "gui_manager", "register_for_bg_sync", f"🎨 [UI] Registering {widget_name} for background sync.", "INFO")

        def perform_sync(event=None):
            if not widget.winfo_exists(): return

            try:
                w, h = widget.winfo_width(), widget.winfo_height()
                if w <= 1 or h <= 1: return
            except tk.TclError: return

            try:
                p_bg = parent.cget("bg")
                if widget.cget("bg") != p_bg:
                    widget.configure(bg=p_bg)
                if canvas and canvas.winfo_exists() and canvas.cget("bg") != p_bg:
                    canvas.configure(bg=p_bg)

                # Use stored slice method if available
                if hasattr(widget, '_perform_background_slice'):
                    widget._perform_background_slice()
                else:
                    # Re-apply transparency slicing if not already registered
                    self._apply_transparency(widget, canvas, configuration, builder_instance)
            except Exception as e:
                matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name, f"perform_sync error: {e}", level="DEBUG")
                pass

        # Bind to parent's configuration changes to keep in sync
        parent.bind("<Configure>", perform_sync, add="+")
        # Also sync immediately on Map
        widget.bind("<Map>", perform_sync, add="+")
