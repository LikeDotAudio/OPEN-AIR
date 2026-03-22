# Core/batch_processing_engine.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from loguru import logger

class BatchProcessingEngine:
    """Orchestrates the asynchronous batch processing of functional widgets."""

    def __init__(self, builder, renderer_logger, local_debug=True):
        self.builder, self.logger, self.debug = builder, renderer_logger, local_debug

    def process(self, parent, widgets, chunk_size, context, state, on_done):
        """Processes a single chunk of widgets and schedules the next."""
        if not widgets or not parent.winfo_exists():
            state["pending"] -= len(widgets); state["loop_done"] = True; on_done(); return

        chunk, rem = widgets[:chunk_size], widgets[chunk_size:]
        for w in chunk:
            try:
                wd = w["val"]; wt = wd.get("type", wd.get("widget_type"))
                creator = self.builder.widget_factory.get(wt)
                
                if self.debug: self.logger.debug(f"  └─ 🔨 Creating '{wt}' at '{w['path']}'")
                if creator:
                    wd["path"] = w["path"] # Inject path for MQTT
                    widget = creator(parent_widget=parent, config_data=wd, context=context)
                    if widget:
                        widget._oca_path = w["path"]; lay = wd.get("layout", {})
                        widget.grid(row=lay.get("row", w["r"]), column=lay.get("column", w["c"]),
                                    columnspan=lay.get("col_span", 1), rowspan=lay.get("row_span", 1),
                                    padx=w["padx"], pady=w["pady"], sticky=w["sticky"])
                else: self.logger.error(f"❌ Unknown functional widget: '{wt}' at {w['path']}")
            except Exception: self.logger.exception(f"❌ Deferred build error: {w['path']}")
            finally: state["pending"] -= 1; on_done()

        if rem: parent.after(1, lambda: self.process(parent, rem, chunk_size, context, state, on_done))
