# Workers/engine_engine_engine_structural_assembler.py
# Author: Anthony Peter Kuzub
# Version: 1.0.1
#
# Description: Manages the immediate creation of structural containers (OcaBlock, OcaBin).

import tkinter as tk

from oaGui.Workers.compositing.engine_visual_effects import EngineVisualEffects


class StructuralAssembler:
    """Manages the immediate creation of structural containers (OcaBlock, OcaBin)."""

    @staticmethod
    def create_block(parent, value, builder):
        # Blocks are typically transparent canvases
        target = tk.Canvas(parent, bd=0, relief="flat", highlightthickness=0, bg="#2b2b2b", width=10, height=10)
        target.grid_propagate(True) # ⚡ PROPAGATION: Allow canvas to grow to fit gridded children

        if builder and hasattr(builder, 'show_structure') and builder.show_structure.get():
            target.config(highlightbackground="red", highlightthickness=1)

        # ⚡ SLICING: Ensure block is registered for industrial transparency inheritance
        EngineVisualEffects.apply_transparency(target, target, value, builder)
        return target, target

    @staticmethod
    def create_bin(parent, value, builder):
        # ⚡ HULL: The outer frame gridded into the parent
        hull = tk.Frame(parent, bg="#2b2b2b", bd=0, highlightthickness=0)
        hull.grid_rowconfigure(0, weight=1)
        hull.grid_columnconfigure(0, weight=1)

        # 📏 GEOMETRY: Extract explicit size or default to minimal to allow expansion
        geom = value.get("geometry", {})
        w = value.get("width") or geom.get("width") or 1
        h = value.get("height") or geom.get("height") or 1

        # ⚡ BEHAVIOR: Check for scrolling override
        behavior = value.get("behavior", {})
        allow_scrolling = behavior.get("allow_scrolling", True)

        if not allow_scrolling:
            # ⚡ OVERLAY MODE: Build directly into a transparent canvas without scrollbars
            inner = tk.Canvas(hull, bg="#2b2b2b", bd=0, highlightthickness=0, width=w, height=h)
            inner.grid(row=0, column=0, sticky="nsew")
            
            # ⚡ SLICING: Ensure overlay is registered for industrial transparency inheritance
            EngineVisualEffects.apply_transparency(hull, inner, value, builder)
            return hull, inner

        # ⚡ VIEWPORT: The scrollable canvas
        viewport = tk.Canvas(hull, bd=0, highlightthickness=0, bg="#2b2b2b", width=w, height=h)
        viewport.grid(row=0, column=0, sticky="nsew")

        # ⚡ SCROLLBARS: Auto-hiding scrollbars
        from oaGui.Interface.controls.auto_scrollbar import AutoScrollbar
        vsb = AutoScrollbar(hull, orient=tk.VERTICAL, command=viewport.yview)
        hsb = AutoScrollbar(hull, orient=tk.HORIZONTAL, command=viewport.xview)
        viewport.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # ⚡ INNER: The content frame inside the canvas
        # Must be a Canvas so EngineVisualEffects can inject background slices onto it
        inner = tk.Canvas(viewport, bg="#2b2b2b", bd=0, highlightthickness=0)
        inner_id = viewport.create_window((0, 0), window=inner, anchor="nw")

        # ⚡ RESPONSIVE SYNC: Track canvas size to allow inner frame to fill viewport
        def _on_canvas_configure(event):
            # ⚡ EVENT GATE: Ignore resize events from gridded children (like buttons/knobs)
            if event.widget != viewport: return
            
            # Track width for horizontal stretching
            # Track height to ensure background fills the viewport even when content is short
            # Use max(req_height, event.height) to allow scrolling if content is tall
            req_w = inner.winfo_reqwidth()
            req_h = inner.winfo_reqheight()
            new_h = max(event.height, req_h)
            
            # ⚡ STABILITY CHECK: Avoid redundant updates that trigger layout loops
            try:
                curr_w = int(float(viewport.itemcget(inner_id, "width")))
                curr_h = int(float(viewport.itemcget(inner_id, "height")))
                if curr_w == event.width and curr_h == new_h:
                    return
            except (tk.TclError, ValueError):
                pass

            from oaLogging.Methods.matrix_gate import matrix_log
            matrix_log("ui", "gui_render", "create_bin", 
                       f"📦📐🔳 [RENDER] Bin Size Sync (ID: {value.get('id', '??')}) | "
                       f"Viewport: {event.width}x{event.height} | Content: {req_w}x{req_h} | Target: {event.width}x{new_h}", "TRACE")

            # ⚡ FOOTER UPDATE: If this is the main workspace bin, update the builder footer
            if builder and hasattr(builder, '_update_footer'):
                builder._update_footer(event.width, event.height, req_w, req_h)

            viewport.itemconfig(inner_id, width=event.width, height=new_h)

        viewport.bind("<Configure>", _on_canvas_configure, add="+")
        inner.bind("<Configure>", lambda e: viewport.configure(scrollregion=viewport.bbox("all")))

        # ⚡ SLICING: Ensure both viewport and inner frame are registered for inheritance
        EngineVisualEffects.apply_transparency(hull, viewport, value, builder)
        EngineVisualEffects.apply_transparency(hull, inner, value, builder)
        return hull, inner
