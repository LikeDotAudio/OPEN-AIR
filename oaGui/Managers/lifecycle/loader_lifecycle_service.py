# oaGui/Managers/loader_lifecycle_service.py
# Author: Anthony Peter Kuzub
# Version 20260502.1001.1
#
# Description: Handles the destruction and re-initialization of the GUI Frame using atomic services.

from .ui_rebuild_orchestrator import orchestrate_ui_rebuild
from .ui_cache_invalidator import invalidate_ui_render_caches

class LifecycleManagerMixin:
    """Mixin for destroying and recreating the GUI content via atomic services."""

    def _force_rebuild_gui(self):
        """Forces a rebuild via cache invalidation and atomic reload."""
        invalidate_ui_render_caches()
        self.last_build_hash = None
        self._load_and_build_from_file()

    def _rebuild_gui(self):
        """Delegates reconstruction to atomic orchestrator."""
        orchestrate_ui_rebuild(self)
