# Managers/engine_widget_assembler.py
# Author: Anthony Peter Kuzub
# Version 20260502.1001.1
#
# Description: Orchestrates the creation of dynamic widgets using atomic services.

from loguru import logger

from oaGui.Methods.formatting.ui_coordinate_utils import UICoordinateUtils
from oaLogging.Methods.matrix_gate import matrix_log

from .dynamic_widget_factory import instantiate_dynamic_widgets


class EngineWidgetAssemblerMixin:
    """Orchestrates dynamic widget assembly via atomic services."""

    def _initialize_renderer(self):
        """Initializes coordinate cache."""
        self._coord_cache = {}

    def _get_relative_coords(self, widget, ref_widget):
        """Standard coordinate extraction via utility."""
        if not hasattr(self, '_coord_cache'): self._coord_cache = {}
        return UICoordinateUtils.get_relative_coords(widget, ref_widget, self._coord_cache)

    def _clear_coord_cache(self):
        """Clears the coordinate cache for fresh layout pass."""
        matrix_log("ui", "gui_builder", "_clear_coord_cache", "🧩 BatchBuilder: Clearing coordinate cache.", "TRACE")
        self._coord_cache = {}

    def _create_dynamic_widgets(self, parent_frame, data, path_prefix="", override_cols=None, on_complete=None, parent_bg_pil=None, context=None):
        """Delegates widget construction to atomic factory service."""
        instantiate_dynamic_widgets(self, parent_frame, data, path_prefix, override_cols, on_complete, parent_bg_pil, context)

    def _process_fields_in_batches(self, *args, **kwargs):
        """Legacy placeholder."""
        logger.warning("⚠️ Deprecated call to _process_fields_in_batches. Use BatchLayoutEngine.")
