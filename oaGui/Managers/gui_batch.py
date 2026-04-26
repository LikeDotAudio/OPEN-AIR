# Managers/gui_batch.py
# Author: Anthony Peter Kuzub
# Version: 20260222.Adapter.1
#
# Description: Handles recursive JSON parsing and Grid layout with a "Skeleton-First" rendering system.

from loguru import logger

from oaLogging.Methods.matrix_gate import is_debug_allowed, matrix_log

from ..Core.batch_processing_engine import BatchProcessingEngine
from ..Workers.async_grid_renderer import AsyncGridRenderer


def _is_debug():
    return is_debug_allowed(system="UI", element="GUI_BUILDER")

class GuiBatchBuilderMixin:
    """
    Legacy Mixin for Batch Building.
    Now acts as a thin wrapper around the standalone AsyncGridRenderer.
    """

    def _initialize_batch_builder(self):
        """Initialize mixin state."""
        self._coord_cache = {}
        # We can instantiate the renderer here or on demand
        batch_engine = BatchProcessingEngine(self, logger, _is_debug())
        factory = getattr(self, 'widget_factory', {})
        self._async_renderer = AsyncGridRenderer(factory, batch_engine)

    def _get_relative_coords(self, widget, ref_widget):
        """
        Calculates coordinates of widget relative to ref_widget.
        OPTIMIZED: Caches results to prevent millions of redundant lookups.
        """
        if not hasattr(self, '_coord_cache'):
            self._coord_cache = {}

        wid = widget._w
        if wid in self._coord_cache:
            return self._coord_cache[wid]

        relative_x, relative_y = 0, 0
        current_widget = widget
        ref_path = ref_widget._w if ref_widget else ""

        while current_widget:
            curr_path = current_widget._w
            if curr_path == ref_path:
                break
            relative_x += current_widget.winfo_x()
            relative_y += current_widget.winfo_y()

            parent_path = current_widget.winfo_parent()
            if not parent_path: break
            current_widget = current_widget.nametowidget(parent_path)

        if widget.winfo_ismapped():
            self._coord_cache[wid] = (relative_x, relative_y)

        return relative_x, relative_y

    def _clear_coord_cache(self):
        """Clears the coordinate cache (call on resize)."""
        matrix_log("ui", "gui_builder", "_clear_coord_cache", "🧩 BatchBuilder: Clearing coordinate cache.", "TRACE")
        self._coord_cache = {}

    def _create_dynamic_widgets(self, parent_frame, data, path_prefix="", override_cols=None, on_complete=None, parent_bg_pil=None, context=None):
        """
        Public entry point for creating dynamic widgets using a single-pass synchronized system.
        Delegates to AsyncGridRenderer.
        """
        if context is None:
            from oaGuiManager.Core.context.widget_context import WidgetContext
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
            parent_frame,
            data,
            path_prefix,
            override_cols,
            on_complete,
            parent_bg_pil,
            context
        )

    # Legacy method kept for interface compatibility if any direct calls exist (unlikely)
    # The Renderer handles this internally now.
    def _process_fields_in_batches(self, *args, **kwargs):
        logger.warning("⚠️ Deprecated call to _process_fields_in_batches. Use AsyncGridRenderer.")
        pass
