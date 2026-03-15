# managers/Display/builder/async_grid_renderer.py
#
# High-Fidelity Asynchronous Grid Layout Engine for OPEN-AIR.
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
# Version 20260314.120000.REV02

"""
async_grid_renderer.py - Asynchronous GUI Layout and Rendering Engine.

Purpose:
    Provides a high-performance, "Skeleton-First" rendering system that
    translates normalized JSON blueprints into live Tkinter widget trees.
    It manages recursive grid allocation, batch processing of widgets to
    prevent UI thread starvation, and complex container behaviors.

Responsibilities:
    - Recursively parse GUI blueprints and allocate space in the Tkinter 
      grid system.
    - Implement "Batch Processing" for widget creation, allowing the UI 
      to remain responsive during heavy layout operations.
    - Orchestrate high-fidelity container types including 'OcaBlock' (Canvas-
      based groups) and 'OcaBin' (Viewport/Scrollable containers).
    - Manage transparency and background slicing for complex industrial 
      aesthetics using the TransparencyManager.

Constraints:
    - Relies on 'BlueprintLoader' to provide pre-normalized data.
    - Requires a 'WidgetContext' to be passed through the recursion tree
      to facilitate MQTT and style connectivity.
    - All final widget creation must occur on the main Tkinter thread.
"""

import tkinter as tk
from tkinter import ttk
import traceback
from loguru import logger

from managers.Display.parser.widget_schema_normalizer import WidgetSchemaNormalizer
from managers.Display.context.widget_context import WidgetContext
from managers.Display.transparency.transparency_manager import TransparencyManager

# LOCAL_DEBUG: Toggles verbose tracing for layout and batch processing.
LOCAL_DEBUG = True

# Bound logger to reduce stack-tracing overhead in the hot rendering path.
renderer_logger = logger.bind(subsystem="RENDERER")

class AsyncGridRenderer:
    """
    Handles recursive Grid layout with a Skeleton-First rendering strategy.
    """

    def __init__(self, builder_instance):
        """
        Inputs:
            builder_instance (DynamicGuiBuilder): The master builder instance.
        """
        self.builder = builder_instance

    def render(self, parent_frame, data, path_prefix="", override_cols=None, 
               on_complete=None, parent_bg_pil=None, context=None):
        """
        Primary entry point for the recursive GUI build process.

        Lead with action: Analyzes the provided configuration and initiates
        a batch-processed grid construction pass. It sets up column 
        weights and begins the recursive field loop.

        Inputs:
            parent_frame (tk.Widget): The container for the current branch.
            data (dict): The normalized configuration for this container.
            path_prefix (str): The logical OcaPath for the current branch.
            on_complete (Callable, optional): Callback for when this branch
                                              and all children are ready.

        Outputs:
            None. (The UI is modified in-place).
        """
        try:
            if not isinstance(data, dict):
                if on_complete: on_complete()
                return

            if LOCAL_DEBUG: 
                renderer_logger.debug(f"🏗️ Rendering branch '{path_prefix}'")

            # Resolve dimensions and grid propagation.
            geom = data.get("geometry", {})
            has_dims = any(data.get(k) or geom.get(k) 
                           for k in ["width", "height"])
            
            if has_dims:
                try:
                    parent_frame.grid_propagate(False)
                    # Some widgets (like Canvas) don't have pack_propagate
                    if hasattr(parent_frame, 'pack_propagate'):
                        parent_frame.pack_propagate(False)
                    
                    w = data.get("width") or geom.get("width")
                    h = data.get("height") or geom.get("height")
                    if w: parent_frame.config(width=w)
                    if h: parent_frame.config(height=h)
                except: pass

            fields = data.get("fields", data.get("blocks", data))
            all_fields = list(fields.items())
            
            # Resolve background for transparency slicing.
            eff_bg = (parent_bg_pil if parent_bg_pil 
                      else getattr(self.builder, 'panel_bg_pil', None))

            # --- Grid Configuration ---
            # 1. Determine the grid dimensions from the data
            max_r, max_c = 0, 0
            if all_fields:
                for key, value in all_fields:
                    if isinstance(value, dict):
                        layout = value.get("layout", {})
                        max_r = max(max_r, layout.get("row", 0) + layout.get("row_span", 1) - 1)
                        max_c = max(max_c, layout.get("column", 0) + layout.get("col_span", 1) - 1)
            
            # Use explicit column layout if provided, otherwise use detected max
            num_cols = int(data.get("layout_columns", max_c + 1))

            # 2. Configure Rows
            # Default all rows to have weight so they can expand.
            # A more advanced implementation could take `row_sizing` data.
            num_rows = max_r + 1
            for i in range(num_rows):
                parent_frame.grid_rowconfigure(i, weight=1)

            # 3. Configure Columns
            col_sizing = data.get("column_sizing", [])
            for i in range(num_cols):
                sizing = col_sizing[i] if i < len(col_sizing) else {}
                weight = sizing.get("weight", 1)
                minwidth = sizing.get("minwidth", 0)
                if sizing.get("maxwidth", 0) > 0:
                    minwidth = sizing["maxwidth"]
                    weight = 0
                parent_frame.grid_columnconfigure(i, weight=weight, minsize=minwidth)

            # Ensure execution context is valid.
            if context is None and hasattr(self.builder, '_get_widget_context'):
                context = self.builder._get_widget_context()

            # Delegate to the batch processor to maintain UI responsiveness.
            self._process_fields_in_batches(
                parent_frame, all_fields, path_prefix, num_cols, 
                0, 0, 0, on_complete, eff_bg, parent_data=data, context=context
            )
            
        except Exception as e:
            renderer_logger.exception(f"❌ Synchronized build error: {path_prefix}")
            if on_complete: on_complete()

    def _process_fields_in_batches(self, parent_frame, field_list, path_prefix, 
                                   max_cols, start_index, col, row, 
                                   on_complete=None, effective_bg_pil=None, 
                                   parent_data=None, context=None):
        """
        Internal batch-processing loop for widget creation.

        Lead with action: Iterates through fields, creating structural
        containers (Blocks/Bins) immediately and deferring functional
        widgets to background "chunks". This ensures the basic layout
        appears instantly while complex widgets "pop in".

        Inputs:
            parent_frame (tk.Widget): The container to populate.
            field_list (list): The list of (key, value) widget configs.
            ... [standard layout tracking params]
        """
        i = start_index
        c = col
        r = row
        
        STRUCT_TYPES = ["OcaBlock", "OcaBin", "OcaArray", "OcaBreakLine"]
        deferred_widgets = []

        # completion_tracking manages the asynchronous join point.
        state = {"pending": 0, "loop_done": False, "aborted": False}

        def _check_done():
            if state["loop_done"] and state["pending"] <= 0:
                if parent_frame.winfo_exists() and path_prefix == "":
                    if hasattr(self.builder, '_trigger_reslice_all'):
                         self.builder._trigger_reslice_all()
                if on_complete:
                    try: parent_frame.after(1, on_complete)
                    except: on_complete()

        def _on_task_end():
            state["pending"] -= 1
            _check_done()

        def _process_deferred(widgets, chunk_size=25):
            """Processes a chunk of widgets and schedules the next chunk."""
            if not widgets or not parent_frame.winfo_exists():
                state["pending"] -= len(widgets)
                state["loop_done"] = True
                _check_done()
                return

            chunk = widgets[0:chunk_size]
            rem = widgets[chunk_size:]
            
            for w in chunk:
                try:
                    w_data = w["val"]
                    w_type = w_data.get("type", w_data.get("widget_type"))
                    creator = self.builder.widget_factory.get(w_type)
                    
                    if creator:
                        # ⚡ CRITICAL: Inject the path into the config so creators 
                        # can register with the StateMirrorEngine.
                        w_data["path"] = w["path"]
                        
                        widget = creator(parent_widget=parent_frame, 
                                         config_data=w_data, context=context)
                        if widget:
                            widget._oca_path = w["path"]
                            layout = w_data.get("layout", {})
                            widget.grid(
                                row=layout.get("row", w["r"]), 
                                column=layout.get("column", w["c"]), 
                                columnspan=layout.get("col_span", 1), 
                                rowspan=layout.get("row_span", 1), 
                                padx=w["padx"], pady=w["pady"], 
                                sticky=w["sticky"]
                            )
                    else:
                        renderer_logger.error(f"❌ Unknown functional widget type: '{w_type}' at {w['path']}")
                except Exception as e:
                    renderer_logger.exception(f"❌ Deferred build error: {w['path']}")
                finally:
                    _on_task_end()

            if rem:
                parent_frame.after(1, lambda: _process_deferred(rem, chunk_size))

        # --- Primary Field Iteration ---
        try:
            META = ["layout", "type", "geometry", "column_sizing", "background"]

            while i < len(field_list):
                if not parent_frame.winfo_exists():
                    state["aborted"] = True; break

                key, value = field_list[i]
                if key in META or not isinstance(value, dict):
                    i += 1; continue
                
                # Construct logical OcaPath.
                p_suffix = "fields" if (parent_data and 
                           "fields" in parent_data) else ""
                cur_path = f"{path_prefix}.{p_suffix}.{key}".strip(".")
                
                w_type = value.get("type", value.get("widget_type"))
                if not w_type:
                    i += 1; continue

                # Resolve Layout Parameters.
                layout = value.get("layout", {})
                cs = int(layout.get("col_span", 1))
                rs = int(layout.get("row_span", 1))
                st = layout.get("sticky", "nsew" if w_type in STRUCT_TYPES 
                                else "")
                
                curr_r = layout.get("row", r)
                curr_c = layout.get("column", c)

                if w_type in STRUCT_TYPES:
                    # Structural blocks are handled immediately and recursively.
                    if w_type == "OcaBlock":
                        # Create Canvas-based high-fidelity block.
                        target = tk.Canvas(parent_frame, bd=0, relief="flat", 
                                           highlightthickness=0, bg="#2b2b2b")
                        target.grid(row=curr_r, column=curr_c, columnspan=cs, 
                                    rowspan=rs, sticky=st)
                        
                        # --- 🐞 DEBUG: Visual Structure Box ---
                        if self.builder and hasattr(self.builder, 'show_structure') and self.builder.show_structure.get():
                            target.config(highlightbackground="red", highlightthickness=1)
                        
                        TransparencyManager.apply_transparency(
                            target, target, value, self.builder
                        )
                        
                        state["pending"] += 1
                        self.render(target, value, cur_path, on_complete=_on_task_end, 
                                    parent_bg_pil=effective_bg_pil, context=context)
                    
                    elif w_type == "OcaBin":
                        # ⚡ IMPLEMENTATION: Viewport Triad (Outer -> Viewport -> Inner)
                        # 1. Outer Hull
                        hull = tk.Frame(parent_frame, bg="#2b2b2b", bd=0, highlightthickness=0)
                        hull.grid(row=curr_r, column=curr_c, columnspan=cs, rowspan=rs, sticky=st)
                        hull.grid_rowconfigure(0, weight=1)
                        hull.grid_columnconfigure(0, weight=1)

                        # 2. Viewport (Canvas)
                        viewport = tk.Canvas(hull, bd=0, highlightthickness=0, bg="#2b2b2b")
                        viewport.grid(row=0, column=0, sticky="nsew")

                        # 3. Inner Payload Frame
                        # Use tk.Frame here as it will be inside the viewport canvas window
                        inner = tk.Frame(viewport, bg="#2b2b2b", bd=0, highlightthickness=0)
                        inner_window_id = viewport.create_window((0, 0), window=inner, anchor="nw")

                        # 4. Bindings for Elastic Viewport Logic
                        def _on_inner_configure(event, v=viewport, i=inner):
                            if v.winfo_exists():
                                v.configure(scrollregion=v.bbox("all"))
                        inner.bind("<Configure>", _on_inner_configure)

                        def _on_viewport_configure(event, v=viewport, i_id=inner_window_id):
                            # Compare required size vs available size
                            # Optional: Implement auto-scrollbar logic here if behavior dictates
                            pass
                        viewport.bind("<Configure>", _on_viewport_configure)

                        TransparencyManager.apply_transparency(hull, viewport, value, self.builder)
                        TransparencyManager.apply_transparency(hull, inner, value, self.builder)

                        state["pending"] += 1
                        self.render(inner, value, cur_path, on_complete=_on_task_end, 
                                    parent_bg_pil=effective_bg_pil, context=context)

                    else:
                        # Standard Factory-created structural widgets (e.g. OcaArray).
                        state["pending"] += 1
                        creator = self.builder.widget_factory.get(w_type)
                        if creator:
                            target = creator(parent_widget=parent_frame, 
                                             config_data=value, context=context)
                            if target:
                                target.grid(row=curr_r, column=curr_c, 
                                            columnspan=cs, rowspan=rs, sticky=st)
                        else:
                            renderer_logger.error(f"❌ Unknown structural widget type: '{w_type}' at {cur_path}")
                        _on_task_end()
                else:
                    # Functional widgets are deferred for batching.
                    state["pending"] += 1
                    deferred_widgets.append({
                        "r": r, "c": c, "val": value, "path": cur_path,
                        "sticky": st, "padx": layout.get("padx", 0),
                        "pady": layout.get("pady", 0)
                    })

                c += cs
                if c >= max_cols: c = 0; r += rs
                i += 1
        except Exception as e:
            renderer_logger.exception("❌ Critical error in field loop.")
            state["aborted"] = True

        state["loop_done"] = True
        if deferred_widgets and not state["aborted"]:
            _process_deferred(deferred_widgets)
        else:
            _check_done()
