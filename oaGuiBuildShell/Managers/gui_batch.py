# Managers/gui_batch.py
# Author: Anthony Peter Kuzub
# Version: 20260222.Adapter.1
#
# Description: Handles recursive JSON parsing and Grid layout with a "Skeleton-First" rendering system.

import tkinter as tk
from loguru import logger
from ..Workers.async_grid_renderer import AsyncGridRenderer

LOCAL_DEBUG = False    # Set to False in production, True for dev on this file

class GuiBatchBuilderMixin:
    """
    Legacy Mixin for Batch Building.
    Now acts as a thin wrapper around the standalone AsyncGridRenderer.
    """

    def _initialize_batch_builder(self):
        """Initialize mixin state."""
        self._coord_cache = {}
        # We can instantiate the renderer here or on demand
        self._async_renderer = AsyncGridRenderer(self)

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

        rx, ry = 0, 0
        curr = widget
        ref_path = ref_widget._w if ref_widget else ""

        while curr:
            curr_path = curr._w
            if curr_path == ref_path:
                break
            rx += curr.winfo_x()
            ry += curr.winfo_y()
            
            parent_path = curr.winfo_parent()
            if not parent_path: break
            curr = curr.nametowidget(parent_path)
        
        if widget.winfo_ismapped():
            self._coord_cache[wid] = (rx, ry)
            
        return rx, ry

    def _clear_coord_cache(self):
        """Clears the coordinate cache (call on resize)."""
        if LOCAL_DEBUG: logger.trace("🧩 BatchBuilder: Clearing coordinate cache.")
        self._coord_cache = {}

    def _create_dynamic_widgets(self, parent_frame, data, path_prefix="", override_cols=None, on_complete=None, parent_bg_pil=None, context=None):
        """
        Public entry point for creating dynamic widgets using a single-pass synchronized system.
        Delegates to AsyncGridRenderer.
        """
        if not hasattr(self, '_async_renderer'):
            self._async_renderer = AsyncGridRenderer(self)
            
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
