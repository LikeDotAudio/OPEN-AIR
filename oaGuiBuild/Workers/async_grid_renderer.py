# managers/Display/builder/async_grid_renderer.py
# Modularized Asynchronous Grid Layout Engine.
# Version 20260315.Modular.1

import tkinter as tk
from loguru import logger

# --- EXTRACTED CORE MODULES ---
from ..Core.grid_topology_configurator import GridTopologyConfigurator
from ..Core.structural_assembler import StructuralAssembler
from ..Core.batch_processing_engine import BatchProcessingEngine

LOCAL_DEBUG = True
renderer_logger = logger.bind(subsystem="RENDERER")

class AsyncGridRenderer:
    """
    Orchestrates recursive Grid layout using a modular Skeleton-First strategy.
    """

    def __init__(self, builder_instance):
        self.builder = builder_instance
        self.batch_engine = BatchProcessingEngine(builder_instance, renderer_logger, LOCAL_DEBUG)

    def render(self, parent_frame, data, path_prefix="", override_cols=None, 
               on_complete=None, parent_bg_pil=None, context=None):
        try:
            if not isinstance(data, dict):
                if on_complete: on_complete()
                return

            if LOCAL_DEBUG: renderer_logger.debug(f"🏗️ Rendering branch '{path_prefix}'")

            # 1. Topology & Geometry
            geom = data.get("geometry", {})
            if any(data.get(k) or geom.get(k) for k in ["width", "height"]):
                try:
                    parent_frame.grid_propagate(False)
                    if hasattr(parent_frame, 'pack_propagate'): parent_frame.pack_propagate(False)
                    w, h = data.get("width") or geom.get("width"), data.get("height") or geom.get("height")
                    if w: parent_frame.config(width=w)
                    if h: parent_frame.config(height=h)
                except Exception as e:
                    renderer_logger.trace(f"Geometry configuration skipped: {e}")

            fields = data.get("fields", data.get("blocks", data))
            
            # Robust Field Parsing: handle dict (default) or list of dicts (presets/OcaBin)
            if isinstance(fields, dict):
                all_fields = list(fields.items())
            elif isinstance(fields, list):
                all_fields = []
                for item in fields:
                    if isinstance(item, dict):
                        # Handle list of single-keyed dicts (presets style)
                        if len(item) == 1 and not any(k in ["type", "widget_type"] for k in item.keys()):
                            all_fields.extend(item.items())
                        else:
                            # Handle list of widget configs (items style)
                            item_key = item.get("id") or item.get("label") or item.get("label_active")
                            all_fields.append((item_key, item))
                    else:
                        all_fields.append((None, item))
            else:
                all_fields = []

            num_cols = GridTopologyConfigurator.configure(parent_frame, data, all_fields)
            
            eff_bg = parent_bg_pil or getattr(self.builder, 'panel_bg_pil', None)
            if context is None and hasattr(self.builder, '_get_widget_context'):
                context = self.builder._get_widget_context()

            # 2. Batch Orchestration
            self._process_fields(parent_frame, all_fields, path_prefix, num_cols, on_complete, eff_bg, data, context)
            
        except Exception as e:
            renderer_logger.exception(f"❌ Synchronized build error in '{path_prefix}': {e}")
            if on_complete: on_complete()

    def _process_fields(self, parent, field_list, prefix, max_cols, on_complete, bg_pil, parent_data, context):
        i = c = r = 0
        STRUCT = ["OcaBlock", "OcaBin", "OcaArray", "OcaBreakLine"]
        deferred = []; state = {"pending": 0, "loop_done": False, "aborted": False}

        def _check_done():
            if state["loop_done"] and state["pending"] <= 0:
                if parent.winfo_exists() and prefix == "" and hasattr(self.builder, '_trigger_reslice_all'):
                    self.builder._trigger_reslice_all()
                if on_complete:
                    try:
                        parent.after(1, on_complete)
                    except Exception as e:
                        renderer_logger.trace(f"Deferred completion callback failed, executing immediately: {e}")
                        on_complete()

        while i < len(field_list):
            if not parent.winfo_exists(): state["aborted"] = True; break
            key, val = field_list[i]
            
            # Metadata filter
            if key in ["layout", "type", "geometry", "column_sizing", "background"] or not isinstance(val, dict):
                i += 1; continue
            
            # Resolve unique path key
            path_key = key or val.get("id") or val.get("label") or f"item_{i}"
            
            # ⚡ FIX: Correct path segment identification to prevent double dots.
            p_sfx = ""
            if parent_data:
                if "fields" in parent_data: p_sfx = "fields"
                elif "blocks" in parent_data: p_sfx = "blocks"
            
            raw_path = f"{prefix}.{p_sfx}.{path_key}"
            cur_path = ".".join([part for part in raw_path.split(".") if part])
            
            w_type = val.get("type", val.get("widget_type"))
            if not w_type: i += 1; continue

            lay = val.get("layout", {}); cs, rs = int(lay.get("col_span", 1)), int(lay.get("row_span", 1))
            st = lay.get("sticky", "nsew" if w_type in STRUCT else "")
            cr, cc = lay.get("row", r), lay.get("column", c)

            if w_type in STRUCT:
                if w_type == "OcaBlock":
                    target = StructuralAssembler.create_block(parent, val, self.builder)
                    target._oca_path = cur_path
                    target.grid(row=cr, column=cc, columnspan=cs, rowspan=rs, sticky=st)
                    state["pending"] += 1
                    self.render(target, val, cur_path, on_complete=lambda: (state.update({"pending": state["pending"]-1}), _check_done()), parent_bg_pil=bg_pil, context=context)
                elif w_type == "OcaBin":
                    hull, inner = StructuralAssembler.create_bin(parent, val, self.builder)
                    hull._oca_path = cur_path
                    inner._oca_path = f"{cur_path}.fields"
                    hull.grid(row=cr, column=cc, columnspan=cs, rowspan=rs, sticky=st)
                    state["pending"] += 1
                    self.render(inner, val, cur_path, on_complete=lambda: (state.update({"pending": state["pending"]-1}), _check_done()), parent_bg_pil=bg_pil, context=context)
                else:
                    state["pending"] += 1; creator = self.builder.widget_factory.get(w_type)
                    if creator:
                        target = creator(parent_widget=parent, config_data=val, context=context)
                        if target: 
                            target._oca_path = cur_path
                            target.grid(row=cr, column=cc, columnspan=cs, rowspan=rs, sticky=st)
                    state["pending"] -= 1; _check_done()
            else:
                state["pending"] += 1
                deferred.append({"r": r, "c": c, "val": val, "path": cur_path, "sticky": st, "padx": lay.get("padx", 0), "pady": lay.get("pady", 0)})

            c += cs
            if c >= max_cols: c = 0; r += rs
            i += 1

        state["loop_done"] = True
        if deferred and not state["aborted"]: self.batch_engine.process(parent, deferred, 25, context, state, _check_done)
        else: _check_done()
