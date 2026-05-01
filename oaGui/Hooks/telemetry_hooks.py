# oaGui/Hooks/telemetry_hooks.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Event hooks for UI telemetry tracking.

class TelemetryHooks:
    """
    Event hooks for UI telemetry tracking.
    """
    @staticmethod
    def bind_tracking_events(widget, on_visible, on_hidden, on_destroy, on_configure):
        """Binds standard tracking events to a widget."""
        widget.bind("<Map>", on_visible, add="+")
        widget.bind("<Unmap>", on_hidden, add="+")
        widget.bind("<Destroy>", on_destroy, add="+")
        widget.bind("<Configure>", on_configure, add="+")
