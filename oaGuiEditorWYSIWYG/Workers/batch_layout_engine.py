# oaGuiEditorWYSIWYG/Workers/batch_layout_engine.py
# Author: Anthony Peter Kuzub
# Version 20260330.1600.1
#
# Description: Non-blocking, asynchronous batch rendering engine for grid layouts.

import tkinter as tk

from loguru import logger

from oaGui.Managers.grid.engine_grid_layout_logic import GridTopologyConfigurator
from oaGui.Methods.rendering.grid_renderer_utils import GridRendererUtils
from oaGui.Workers.assembly.engine_structural_assembler import StructuralAssembler
from oaLogging.Methods.matrix_gate import matrix_log


class BatchLayoutEngine:
    """Non-blocking, asynchronous batch rendering engine for grid layouts."""

    def __init__(self, factory, scheduler_engine_render):
        self.factory = factory
        self.scheduler_engine_render = scheduler_engine_render

    def render(self, parent, data, path_prefix="", override_cols=None, on_complete=None, parent_bg_pil=None, context=None):
        """Asynchronously renders a GUI branch into the parent frame."""
        if not data:
            if on_complete: on_complete()
            return

        branch_name = data.get("id", data.get("path", "root"))
        matrix_log("ui", "batch_layout", "render", f"🔨🔨🔨 [BUILDING] Rendering branch '{branch_name}'", "INFO")

        # 1. Geometry Normalization
        if "geometry" in data:
            geom = data["geometry"]
            try:
                if "width" in geom: parent.config(width=int(geom["width"]))
                if "height" in geom: parent.config(height=int(geom["height"]))
            except (tk.TclError, ValueError) as e:
                matrix_log("ui", "batch_layout", "render", f"⚠️ Geometry configuration skipped: {e}", "TRACE")

        # 2. ⚡ DEEP NESTING RESOLUTION:
        fields = GridRendererUtils.resolve_fields(data)

        if not fields or not isinstance(fields, (dict, list)):
            if on_complete: on_complete()
            return

        # 3. Grid Configuration
        all_items = list(fields.items()) if isinstance(fields, dict) else list(enumerate(fields))
        num_cols = GridTopologyConfigurator.configure(parent, data, all_items)

        # 4. Batched Field Processing
        state = {"count": 0, "aborted": False, "loop_done": False}
        deferred = []
        field_idx = 0
        row_idx, col_idx = 0, 0

        def _check_done():
            if state["loop_done"] and not state["aborted"] and not deferred and state["count"] == 0:
                if on_complete: on_complete()

        def _process_fields(batch):
            nonlocal row_idx, col_idx, field_idx
            for item in batch:
                if state["aborted"]: break

                if isinstance(item, tuple) and len(item) == 2:
                    key, config = item
                else:
                    key, config = f"field_{field_idx}", item

                item_config = GridRendererUtils.normalize_item_config(config)
                if not isinstance(item_config, dict):
                    continue

                w_type = item_config.get("type")
                STRUCTURAL_TYPES = ["OcaBin", "Bin", "OcaBlock", "Block"]
                if not isinstance(w_type, str) or (w_type not in self.factory and w_type not in STRUCTURAL_TYPES):
                    continue

                widget = None
                try:
                    full_widget_path = f"{path_prefix}.{key}".strip(".")
                    item_config["path"] = full_widget_path

                    if w_type in ["OcaBin", "Bin"]:
                        hull, inner = StructuralAssembler.create_bin(parent, item_config, getattr(context, 'builder_instance', self.factory))
                        self._apply_grid(hull, item_config, row_idx, col_idx)
                        widget = hull
                        state["count"] += 1
                        self.render(inner, item_config, path_prefix=full_widget_path, context=context, on_complete=lambda: (state.update({"count": state["count"]-1}), _check_done()))
                    elif w_type in ["OcaBlock", "Block"]:
                        hull, inner = StructuralAssembler.create_block(parent, item_config, getattr(context, 'builder_instance', self.factory))
                        self._apply_grid(hull, item_config, row_idx, col_idx)
                        widget = hull
                        state["count"] += 1
                        self.render(inner, item_config, path_prefix=full_widget_path, context=context, on_complete=lambda: (state.update({"count": state["count"]-1}), _check_done()))
                    else:
                        widget = self.factory[w_type](parent, item_config, context)
                        if widget:
                            self._apply_grid(widget, item_config, row_idx, col_idx)

                    if widget:
                        widget._oca_path = full_widget_path

                except Exception as e:
                    logger.exception(f"❌ Failed to render widget '{key}' of type '{w_type}': {e}")

                rs = int(item_config.get("layout", {}).get("row_span", 1))
                cs = int(item_config.get("layout", {}).get("col_span", 1))
                col_idx += cs
                if col_idx >= num_cols:
                    col_idx = 0; row_idx += rs
                field_idx += 1

            state["loop_done"] = True
            if deferred and not state["aborted"]:
                self.scheduler_engine_render.process(parent, deferred, 25, context, state, _check_done)
            else:
                _check_done()

        _process_fields(all_items)

    def _apply_grid(self, widget, config, row, col):
        """Applies grid layout to a widget based on its configuration."""
        layout = config.get("layout", {})
        r = layout.get("row", row)
        c = layout.get("column", col)
        rs = layout.get("row_span", 1)
        cs = layout.get("col_span", 1)
        px = layout.get("padx", 5)
        py = layout.get("pady", 5)
        sticky = layout.get("sticky", "nsew")

        try:
            widget.grid(row=r, column=c, rowspan=rs, columnspan=cs, padx=px, pady=py, sticky=sticky)
        except tk.TclError as e:
            matrix_log("ui", "batch_layout", "_apply_grid", f"⚠️ Grid placement failed: {e}", "TRACE")
