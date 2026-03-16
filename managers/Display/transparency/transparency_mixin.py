# managers/Display/transparency/transparency_mixin.py
#
# Legacy Mixin for Industrial Transparency.
# Now delegates to the centralized TransparencyManager.
#
# Author: Anthony Peter Kuzub
# Version 20260222.Adapter.1

from .transparency import TransparencyManager

class TransparencyMixin:
    """Legacy Mixin. Forwards to TransparencyManager."""

    def _apply_transparency(self, target_widget, canvas, config_data, builder_instance):
        """Bridge to the new manager."""
        TransparencyManager.apply_transparency(target_widget, canvas, config_data, builder_instance)

    def register_for_bg_sync(self, widget, canvas, config_data, context):
        """
        Registers a widget for automatic background synchronization with its parent.
        Eliminates the need for local sync_bg() functions in widget creators.
        """
        builder_instance = context.builder_instance if context else None
        parent = widget.master

        def perform_sync(event=None):
            if not widget.winfo_exists(): return
            try:
                p_bg = parent.cget("bg")
                if widget.cget("bg") != p_bg:
                    widget.configure(bg=p_bg)
                if canvas and canvas.winfo_exists() and canvas.cget("bg") != p_bg:
                    canvas.configure(bg=p_bg)
                
                # Re-apply transparency slicing if active
                self._apply_transparency(widget, canvas, config_data, builder_instance)
            except Exception:
                pass

        # Bind to parent's configuration changes to keep in sync
        parent.bind("<Configure>", perform_sync, add="+")
        # Also sync immediately on Map
        widget.bind("<Map>", perform_sync, add="+")
