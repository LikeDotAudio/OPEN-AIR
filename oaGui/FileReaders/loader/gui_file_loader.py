# FileReaders/gui_file_loader.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1001.1
#
# Description: Handles File I/O via atomic lifecycle services.

from oaGui.Managers.lifecycle.blueprint_sync_service import load_and_synchronize_blueprint

class GuiFileLoaderMixin:
    """Mixin for File Loading via atomic services."""

    def _load_and_build_from_file(self):
        """Delegates loading to atomic service."""
        load_and_synchronize_blueprint(self)

    def _auto_configure_metal_folds(self):
        """Deprecated."""
        pass

    def _load_default_background(self):
        """Retrieves background config from cached defaults."""
        from oaGui.FileReaders.loader.json_blueprint_reader import JsonBlueprintReader
        return JsonBlueprintReader._load_default_config().get("background")
