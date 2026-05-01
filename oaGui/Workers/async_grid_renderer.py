# Workers/async_grid_renderer.py
#
# Modularized Asynchronous Grid Layout Engine. Orchestrates recursive
# Grid layout using a modular Skeleton-First strategy.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260330.1600.1

import tkinter as tk

from loguru import logger

from oaGui.Core.grid_topology_configurator import GridTopologyConfigurator
from oaGui.Core.structural_assembler import StructuralAssembler
from oaLogging.Methods.matrix_gate import matrix_log


class AsyncGridRenderer:
    """Asynchronous Grid Layout Engine."""

    def __init__(self, factory, batch_engine):
        self.factory = factory
        self.batch_engine = batch_engine

    def render(self, parent, data, path_prefix="", override_cols=None, on_complete=None, parent_bg_pil=None, context=None):
        """Asynchronously renders a GUI branch into the parent frame."""
        if not data:
            if on_complete: on_complete()
            return

        branch_name = data.get("id", data.get("path", "root"))
        matrix_log("ui", "gui_shell", "render", f"🔨🔨🔨 [BUILDING] Rendering branch '{branch_name}' (Bin: {data.get('id')}, Block: {data.get('type') if data.get('type') != 'OcaBin' else 'None'})", "INFO")

        # 1. Geometry Normalization
        if "geometry" in data:
            geom = data["geometry"]
            try:
                if "width" in geom: parent.config(width=int(geom["width"]))
                if "height" in geom: parent.config(height=int(geom["height"]))
            except (tk.TclError, ValueError) as e:
                matrix_log("ui", "gui_shell", "render", f"⚠️ Geometry configuration skipped: {e}", "TRACE")

        # 2. ⚡ DEEP NESTING RESOLUTION:
        # Find the actual widget fields, descending through 'blocks' or 'fields' containers.
        fields = data.get("fields", data.get("blocks"))

        # If the level has no 'type', it's an anonymous container (likely the top-level dict).
        if fields is None and not data.get("type"):
            fields = data

        # ⚡ RECURSIVE DESCEND: Handle 'blocks -> fields' redundant nesting.
        while isinstance(fields, dict) and len(fields) == 1:
            key = next(iter(fields))
            if key in ["fields", "blocks"]:
                fields = fields[key]
            else:
                break

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

                # ⚡ ROBUSTNESS: Normalize (key, config) regardless of source (dict.items or enumerate)
                if isinstance(item, tuple) and len(item) == 2:
                    key, config = item
                else:
                    # Fallback for unexpected formats
                    key, config = f"field_{field_idx}", item

                # Recursively resolve nested fields for this specific item if needed
                # (Ensures internal OcaBlock/OcaBin fields are also discovered)
                item_config = config
                if not isinstance(item_config, dict):
                    continue

                while isinstance(item_config, dict) and len(item_config) == 1 and not item_config.get("type"):
                    inner_key = next(iter(item_config))
                    if inner_key in ["fields", "blocks"]:
                        item_config = item_config[inner_key]
                    else:
                        break

                w_type = item_config.get("type")
                STRUCTURAL_TYPES = ["OcaBin", "Bin", "OcaBlock", "Block"]
                if not isinstance(w_type, str) or (w_type not in self.factory and w_type not in STRUCTURAL_TYPES):
                    # Skip items with unknown types that are not structural
                    continue

                # 5. Widget Instantiation
                widget = None
                try:
                    # ⚡ PATH INJECTION: Ensure the widget config knows its own MQTT path
                    full_widget_path = f"{path_prefix}.{key}".strip(".")
                    item_config["path"] = full_widget_path

                    # Handle structural types (Bin/Block) vs standard widgets
                    if w_type in ["OcaBin", "Bin"]:
                        builder = getattr(context, 'builder_instance', self.factory)
                        hull, inner = StructuralAssembler.create_bin(parent, item_config, builder)
                        self._apply_grid(hull, item_config, row_idx, col_idx)
                        widget = hull # Represent the hull for overlays
                        # Recursive call for children
                        state["count"] += 1
                        self.render(inner, item_config, path_prefix=full_widget_path, context=context, on_complete=lambda: (state.update({"count": state["count"]-1}), _check_done()))
                    elif w_type in ["OcaBlock", "Block"]:
                        builder = getattr(context, 'builder_instance', self.factory)
                        hull, inner = StructuralAssembler.create_block(parent, item_config, builder)
                        self._apply_grid(hull, item_config, row_idx, col_idx)
                        widget = hull # Represent the hull for overlays
                        # Recursive call for children
                        state["count"] += 1
                        self.render(inner, item_config, path_prefix=full_widget_path, context=context, on_complete=lambda: (state.update({"count": state["count"]-1}), _check_done()))
                    else:
                        widget = self.factory[w_type](parent, item_config, context)
                        if widget:
                            self._apply_grid(widget, item_config, row_idx, col_idx)

                    # ⚡ DESIGN INJECTION: Attach the path for the overlay system
                    if widget:
                        widget._oca_path = full_widget_path

                except Exception as e:
                    logger.exception(f"❌ Failed to render widget '{key}' of type '{w_type}': {e}")

                # Update Grid Markers
                rs = int(item_config.get("layout", {}).get("row_span", 1))
                cs = int(item_config.get("layout", {}).get("col_span", 1))
                col_idx += cs
                if col_idx >= num_cols:
                    col_idx = 0; row_idx += rs
                field_idx += 1

            state["loop_done"] = True
            if deferred and not state["aborted"]:
                self.batch_engine.process(parent, deferred, 25, context, state, _check_done)
            else:
                _check_done()

        # Kick off processing
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
            matrix_log("ui", "gui_shell", "_apply_grid", f"⚠️ Grid placement failed: {e}", "TRACE")
