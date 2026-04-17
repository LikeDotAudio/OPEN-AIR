# Interface/layout_engine/preview_engine.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Interface.1
#
# Description: Manages the lifecycle and instantiation of the GUI builder preview.

import copy
from oaGuiBuilder.Workers.builder import DynamicGuiBuilder
from oaStateCache.Core.state_mirror_engine import StateMirrorEngine
from oaLogging.Core.logger import GUI_LOGGER as logger

class PreviewEngine:
    """Manages the lifecycle and instantiation of the DynamicGuiBuilder preview."""

    def __init__(self, render_area, on_focus_callback, workspace=None):
        self.render_area = render_area
        self.on_focus_callback = on_focus_callback
        self.workspace = workspace
        self.preview_builder = None

    def refresh(self, json_data, render_tier=None, superficial_pad=0):
        """Top-level refresh to update the preview with new JSON data."""
        try:
            if not self.render_area.winfo_exists():
                return None

            render_data = self._prepare_render_data(json_data)

            if self.preview_builder:
                self._update_existing_builder(render_data, render_tier, superficial_pad)
            else:
                self._create_new_builder(render_data, render_tier, superficial_pad)

            return self.preview_builder
        except Exception as e:
            logger.error(f"❌ [PREVIEW] Rebuild failed: {e}")
            return None

    def _prepare_render_data(self, json_data):
        """Deep copies and strips constraints from the JSON data for previewing."""
        render_data = copy.deepcopy(json_data)
        self._strip_constraints(render_data)
        return render_data

    def _update_existing_builder(self, render_data, render_tier, superficial_pad):
        """Updates an already active builder instance with new data."""
        self.preview_builder._is_rebuilding = True
        try:
            self.preview_builder._last_reported_width = 0
            self.preview_builder.config_data = render_data
            self.preview_builder.superficial_pad = superficial_pad
            self.preview_builder._render_tier = self._map_render_tier(render_tier)
            self.preview_builder._rebuild_gui()
        finally:
            self.preview_builder.after(100, lambda: setattr(self.preview_builder, '_is_rebuilding', False))

    def _create_new_builder(self, render_data, render_tier, superficial_pad):
        """Instantiates a fresh DynamicGuiBuilder and attaches it to the render area."""
        inert_engine = StateMirrorEngine(base_topic="PREVIEW", subscriber_router=None, root=None, state_cache_manager=None)
        builder_config = {
            "state_mirror_engine": inert_engine,
            "subscriber_router": None,
            "on_focus_widget": self.on_focus_callback,
            "app_instance": self.workspace,
            "is_editor": True,
            "allow_horizontal_scroll": False
        }
        self.preview_builder = DynamicGuiBuilder(self.render_area, config=builder_config, tab_name="InteractivePreview")
        self.preview_builder.start()
        self.preview_builder.pack(fill="both", expand=True)
        
        # Initial render configuration
        self.preview_builder._is_rebuilding = True
        try:
            self.preview_builder.config_data = render_data
            self.preview_builder.superficial_pad = superficial_pad
            self.preview_builder._render_tier = self._map_render_tier(render_tier)
            self.preview_builder._rebuild_gui()
        finally:
            self.preview_builder.after(100, lambda: setattr(self.preview_builder, '_is_rebuilding', False))

    def _map_render_tier(self, tier):
        """Maps a tier string to the builder's recognized internal tier keys."""
        if tier == 'ghost':
            return 'ghost'
        if tier == 'fast':
            return 'fast'
        return 'high_res'

    def _strip_constraints(self, data):
        """Recursively removes fixed geometry to allow the preview to fluidly resize."""
        if isinstance(data, dict):
            if "geometry" in data and isinstance(data["geometry"], dict):
                data["geometry"].pop("width", None)
                data["geometry"].pop("height", None)
            data.pop("width", None)
            data.pop("height", None)
            for v in data.values():
                self._strip_constraints(v)
        elif isinstance(data, list):
            for item in data:
                self._strip_constraints(item)
