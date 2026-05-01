# Managers/dynamic_widget_renderer.py
# Author: Anthony Peter Kuzub
# Version 20260222.Adapter.1
#
# Description: Orchestrates the creation of dynamic widgets from data using the AsyncGridRenderer.

from loguru import logger
from oaLogging.Methods.matrix_gate import is_debug_allowed, matrix_log
from oaGui.Workers.batch_processing_engine import BatchProcessingEngine
from oaGuiEditorWYSIWYG.Workers.async_grid_renderer import AsyncGridRenderer
from oaGui.Methods.ui_coordinate_utils import UICoordinateUtils

def _is_debug():
    return is_debug_allowed(system="UI", element="GUI_BUILDER")

class DynamicWidgetRendererMixin:
    """Orchestrates the creation of dynamic widgets from data using the AsyncGridRenderer."""

    def _initialize_renderer(self):
        """Initialize mixin state."""
        self._coord_cache = {}
        batch_engine = BatchProcessingEngine(self, logger, _is_debug())
        factory = getattr(self, 'widget_factory', {})
        self._async_renderer = AsyncGridRenderer(factory, batch_engine)

    def _get_relative_coords(self, widget, ref_widget):
        """Calculates coordinates of widget relative to ref_widget."""
        if not hasattr(self, '_coord_cache'):
            self._coord_cache = {}
        return UICoordinateUtils.get_relative_coords(widget, ref_widget, self._coord_cache)

    def _clear_coord_cache(self):
        """Clears the coordinate cache (call on resize)."""
        matrix_log("ui", "gui_builder", "_clear_coord_cache", "🧩 BatchBuilder: Clearing coordinate cache.", "TRACE")
        self._coord_cache = {}

    def _create_dynamic_widgets(self, parent_frame, data, path_prefix="", override_cols=None, on_complete=None, parent_bg_pil=None, context=None):
        """Public entry point for creating dynamic widgets."""
        if context is None:
            from oaGui.Core.context.widget_context import WidgetContext
            context = WidgetContext(
                state_mirror_engine=getattr(self, 'state_mirror_engine', None),
                subscriber_router=getattr(self, 'subscriber_router', None),
                base_mqtt_topic_from_path=getattr(self, 'base_mqtt_topic_from_path', ""),
                app_instance=getattr(self, 'app_instance', None),
                builder_instance=self
            )

        if not hasattr(self, '_async_renderer'):
            batch_engine = BatchProcessingEngine(self, logger, _is_debug())
            factory = getattr(self, 'widget_factory', {})
            self._async_renderer = AsyncGridRenderer(factory, batch_engine)

        self._async_renderer.render(
            parent_frame, data, path_prefix, override_cols, on_complete, parent_bg_pil, context
        )

    def _process_fields_in_batches(self, *args, **kwargs):
        logger.warning("⚠️ Deprecated call to _process_fields_in_batches. Use AsyncGridRenderer.")
        pass
