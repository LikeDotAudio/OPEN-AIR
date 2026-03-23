# layout/preview_engine.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from oaGuiBuilder.Workers.builder import DynamicGuiBuilder
from oaTranslator.Core.state_mirror_engine import StateMirrorEngine
# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from oaLogging.Core.logger import GUI_LOGGER as logger
import copy

class PreviewEngine:
    """Manages the lifecycle and instantiation of the DynamicGuiBuilder preview."""

    def __init__(self, render_area, on_focus_callback):
        self.render_area = render_area
        self.on_focus_callback = on_focus_callback
        self.preview_builder = None

    def refresh(self, json_data):
        if not self.render_area.winfo_exists(): return None
        
        render_data = copy.deepcopy(json_data)
        self._strip_constraints(render_data)

        if self.preview_builder:
            self.preview_builder._is_rebuilding = True
            try:
                self.preview_builder._last_reported_width = 0
                self.preview_builder.config_data = render_data
                self.preview_builder._rebuild_gui()
            finally:
                self.preview_builder.after(100, lambda: setattr(self.preview_builder, '_is_rebuilding', False))
        else:
            inert_engine = StateMirrorEngine(base_topic="PREVIEW", subscriber_router=None, root=None, state_cache_manager=None)
            builder_config = {
                "state_mirror_engine": inert_engine,
                "subscriber_router": None,
                "on_focus_widget": self.on_focus_callback,
                "is_editor": True
            }
            self.preview_builder = DynamicGuiBuilder(self.render_area, config=builder_config, tab_name="InteractivePreview")
            self.preview_builder.pack(fill="both", expand=True)
            self.preview_builder._is_rebuilding = True
            try:
                self.preview_builder.config_data = render_data
                self.preview_builder._rebuild_gui()
            finally:
                self.preview_builder.after(100, lambda: setattr(self.preview_builder, '_is_rebuilding', False))
                
        return self.preview_builder

    def _strip_constraints(self, data):
        """Removes fixed geometry to allow the editor preview to fluidly resize."""
        if isinstance(data, dict):
            if "geometry" in data and isinstance(data["geometry"], dict):
                data["geometry"].pop("width", None)
                data["geometry"].pop("height", None)
            data.pop("width", None)
            data.pop("height", None)
            for v in data.values(): self._strip_constraints(v)
        elif isinstance(data, list):
            for item in data: self._strip_constraints(item)
