# Core/batch_processing_engine.py
from oaGui.Methods.i18n_utils import get_text
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
                wd = w["value"]; wt = wd.get("type", wd.get("widget_type"))
                
                # ⚡ FAST RENDER MODE: Use square placeholders instead of full functional widgets
                render_tier = getattr(self.builder, '_render_tier', 'high_res')
                s_pad = getattr(self.builder, 'superficial_pad', 0)
                
                if render_tier == 'fast':
                    import tkinter as tk
                    # ⚡ SIMPLIFIED FAST RENDER: No labels, just a sized placeholder box.
                    
                    # Determine real size
                    geom = wd.get("geometry", {})
                    w_val = wd.get("width") or geom.get("width")
                    h_val = wd.get("height") or geom.get("height")
                    
                    # Create frame with fixed size if specified
                    widget = tk.Frame(parent, bg="#3d3d3d", highlightbackground="#555555", highlightthickness=1)
                    
                    if w_val:
                        try:
                            widget.config(width=max(1, int(float(w_val))))
                        except (ValueError, TypeError): pass
                    if h_val:
                        try:
                            widget.config(height=max(1, int(float(h_val))))
                        except (ValueError, TypeError): pass
                    
                    # If size is specified, prevent grid from shrinking the frame
                    if w_val or h_val:
                        widget.grid_propagate(False)
                        widget.pack_propagate(False)

                    if hasattr(self.builder, 'bind_to_widget'):
                        self.builder.bind_to_widget(widget)
                    widget._oca_path = w["path"]
                    lay = wd.get("layout", {})
                    widget.grid(row=lay.get("row", w["r"]), column=lay.get("column", w["c"]),
                                columnspan=lay.get("col_span", 1), rowspan=lay.get("row_span", 1),
                                padx=w["padx"] + s_pad, pady=w["pady"] + s_pad, sticky=w["sticky"])
                else:
                    creator = self.builder.widget_factory.get(wt)
                    
                    if self.debug: self.logger.debug(f"  └─ 🔨 Creating '{wt}' at '{w['path']}'")
                    if creator:
                        wd["path"] = w["path"] # Inject path for MQTT
                        widget = creator(parent_widget=parent, config_data=wd, context=context)
                        if widget:
                            widget._oca_path = w["path"]; lay = wd.get("layout", {})
                            if hasattr(self.builder, 'bind_to_widget'):
                                self.builder.bind_to_widget(widget)
                            widget.grid(row=lay.get("row", w["r"]), column=lay.get("column", w["c"]),
                                        columnspan=lay.get("col_span", 1), rowspan=lay.get("row_span", 1),
                                        padx=w["padx"] + s_pad, pady=w["pady"] + s_pad, sticky=w["sticky"])
                    else: self.logger.error(f"❌ Unknown functional widget: '{wt}' at {w['path']}")
            except Exception: self.logger.exception(f"❌ Deferred build error: {w['path']}")
            finally: state["pending"] -= 1; on_done()

        if rem: parent.after(1, lambda: self.process(parent, rem, chunk_size, context, state, on_done))