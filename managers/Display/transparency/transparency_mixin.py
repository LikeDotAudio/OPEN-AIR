# managers/Display/transparency/transparency_mixin.py
#
# Legacy Mixin for Industrial Transparency.
# Now delegates to the centralized TransparencyManager.
#
# Author: Anthony Peter Kuzub
# Version 20260222.Adapter.1

from .transparency_manager import TransparencyManager

class TransparencyMixin:
    """Legacy Mixin. Forwards to TransparencyManager."""

    def _apply_transparency(self, target_widget, canvas, config_data, builder_instance):
        """Bridge to the new manager."""
        TransparencyManager.apply_transparency(target_widget, canvas, config_data, builder_instance)
