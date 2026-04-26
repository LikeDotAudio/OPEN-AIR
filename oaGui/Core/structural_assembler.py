# Core/structural_assembler.py
# Author: Anthony Peter Kuzub
# Version: 1.0.1
#
# Description: Manages the immediate creation of structural containers (OcaBlock, OcaBin).

import tkinter as tk

from oaGuiManager.Core.transparency.transparency import TransparencyManager


class StructuralAssembler:
    """Manages the immediate creation of structural containers (OcaBlock, OcaBin)."""

    @staticmethod
    def create_block(parent, value, builder):
        # Blocks are typically transparent canvases
        target = tk.Canvas(parent, bd=0, relief="flat", highlightthickness=0, bg="#2b2b2b", width=10, height=10)
        target.grid_propagate(True) # ⚡ PROPAGATION: Allow canvas to grow to fit gridded children

        if builder and hasattr(builder, 'show_structure') and builder.show_structure.get():
            target.config(highlightbackground="red", highlightthickness=1)

        TransparencyManager.apply_transparency(target, target, value, builder)
        return target, target

    @staticmethod
    def create_bin(parent, value, builder):
        # ⚡ HULL: The outer frame gridded into the parent
        hull = tk.Frame(parent, bg="#2b2b2b", bd=0, highlightthickness=0)
        hull.grid_rowconfigure(0, weight=1)
        hull.grid_columnconfigure(0, weight=1)

        # 📏 GEOMETRY: Extract explicit size or default to 200x200
        geom = value.get("geometry", {})
        w = value.get("width") or geom.get("width") or 200
        h = value.get("height") or geom.get("height") or 200

        # ⚡ VIEWPORT: The scrollable canvas
        viewport = tk.Canvas(hull, bd=0, highlightthickness=0, bg="#2b2b2b", width=w, height=h)
        viewport.grid(row=0, column=0, sticky="nsew")

        # ⚡ SCROLLBARS: Auto-hiding scrollbars
        from oaGuiBuilder.Workers.builder import AutoScrollbar
        vsb = AutoScrollbar(hull, orient=tk.VERTICAL, command=viewport.yview)
        hsb = AutoScrollbar(hull, orient=tk.HORIZONTAL, command=viewport.xview)
        viewport.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # ⚡ INNER: The content frame inside the canvas
        # Must be a Canvas so TransparencyManager can inject background slices onto it
        inner = tk.Canvas(viewport, bg="#2b2b2b", bd=0, highlightthickness=0)
        inner_id = viewport.create_window((0, 0), window=inner, anchor="nw")

        # ⚡ RESPONSIVE SYNC: Track canvas size to allow inner frame to fill viewport
        def _on_canvas_configure(event):
            # Track width for horizontal stretching
            # Track height to ensure background fills the viewport even when content is short
            # Use max(req_height, event.height) to allow scrolling if content is tall
            req_h = inner.winfo_reqheight()
            new_h = max(event.height, req_h)
            
            from oaLogging.Methods.matrix_gate import matrix_log
            matrix_log("gui", "gui_builder", "create_bin", 
                       f"📦 [BIN_SIZE] ID: {value.get('id', '??')} | "
                       f"Hull: {hull.winfo_width()}x{hull.winfo_height()} | "
                       f"Viewport: {event.width}x{event.height} | "
                       f"Inner Req: {inner.winfo_reqwidth()}x{req_h} | "
                       f"Inner Target: {event.width}x{new_h}", "TRACE")

            viewport.itemconfig(inner_id, width=event.width, height=new_h)

        viewport.bind("<Configure>", _on_canvas_configure, add="+")
        inner.bind("<Configure>", lambda e: viewport.configure(scrollregion=viewport.bbox("all")))

        TransparencyManager.apply_transparency(hull, viewport, value, builder)
        TransparencyManager.apply_transparency(hull, inner, value, builder)
        return hull, inner
