# oaGui/Workers/engine_render_scheduler.py
# Author: Anthony Peter Kuzub
# Version: 1.0.1
#
# Description: Orchestrates the non-blocking, asynchronous batching of functional widgets using atomic services.

from ..rendering.applicator_widget_grid import apply_widget_to_grid
from ..rendering.service_fast_render import render_fast_widget_placeholder
from ..rendering.service_high_res_render import render_functional_widget


class EngineRenderScheduler:
    """Orchestrates the asynchronous batch processing of functional widgets via atomic services."""

    def __init__(self, builder, renderer_logger, local_debug=True):
        self.builder, self.logger, self.debug = builder, renderer_logger, local_debug

    def process(self, parent, widgets, chunk_size, context, state, on_done):
        """Processes a single chunk of widgets via modular rendering pipeline."""
        if not widgets or not parent.winfo_exists():
            state["pending"] -= len(widgets); state["loop_done"] = True; on_done(); return

        chunk, rem = widgets[:chunk_size], widgets[chunk_size:]
        render_tier = getattr(self.builder, '_render_tier', 'high_res')

        for w in chunk:
            try:
                widget_data = w["value"]
                path = w["path"]

                if render_tier == 'fast':
                    widget = render_fast_widget_placeholder(parent, widget_data, path, self.builder)
                else:
                    widget = render_functional_widget(parent, widget_data, path, self.builder, context, self.logger, self.debug)

                if widget:
                    apply_widget_to_grid(widget, widget_data, w, self.builder)

            except Exception:
                self.logger.exception(f"❌ Deferred build error: {w['path']}")
            finally:
                state["pending"] -= 1; on_done()

        if rem:
            parent.after(1, lambda: self.process(parent, rem, chunk_size, context, state, on_done))
