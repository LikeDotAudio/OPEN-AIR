# Core/structural_assembler.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from oaGuiManager.Core.transparency.transparency import TransparencyManager

class StructuralAssembler:
    """Manages the immediate creation of structural containers (OcaBlock, OcaBin)."""

    @staticmethod
    def create_block(parent, value, builder):
        target = tk.Canvas(parent, bd=0, relief="flat", highlightthickness=0, bg="#2b2b2b")
        if builder and hasattr(builder, 'show_structure') and builder.show_structure.get():
            target.config(highlightbackground="red", highlightthickness=1)
        TransparencyManager.apply_transparency(target, target, value, builder)
        return target

    @staticmethod
    def create_bin(parent, value, builder):
        # ⚡ EXPANSION FIX: The hull frame must fill the parent
        hull = tk.Frame(parent, bg="#2b2b2b", bd=0, highlightthickness=0)
        hull.grid_rowconfigure(0, weight=1); hull.grid_columnconfigure(0, weight=1)
        
        # 📏 GEOMETRY: Extract explicit size from config or geometry block
        geom = value.get("geometry", {})
        w = value.get("width") or geom.get("width") or 200
        h = value.get("height") or geom.get("height") or 200
        
        from oaLogging.Methods.matrix_gate import matrix_log
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        matrix_log("gui", "gui_builder", "create_bin", f"📦 [BIN] Creating hull for {value.get('id', 'unnamed')} (Target: {w}x{h}, Parent current: {parent_w}x{parent_h})", "DEBUG")
        
        # ⚡ Viewport Canvas with Scrollbar Support
        viewport = tk.Canvas(hull, bd=0, highlightthickness=0, bg="#2b2b2b", width=w, height=h)
        viewport.grid(row=0, column=0, sticky="nsew")
        
        # ⚡ Add Auto-hiding Scrollbars to the Bin
        from oaGuiBuilder.Workers.builder import AutoScrollbar
        vsb = AutoScrollbar(hull, orient=tk.VERTICAL, command=viewport.yview)
        hsb = AutoScrollbar(hull, orient=tk.HORIZONTAL, command=viewport.xview)
        viewport.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        matrix_log("gui", "gui_builder", "create_bin", f"  ├─ Viewport initialized with scrollbars (Sticky: nsew)", "TRACE")
        
        # ⚡ Inner frame holds the children
        inner = tk.Frame(viewport, bg="#2b2b2b", bd=0, highlightthickness=0, width=w, height=h)
        inner_id = viewport.create_window((0, 0), window=inner, anchor="nw")
        
        # ⚡ DYNAMIC SYNC: Optimized for fluidity without clipping
        def _sync_dimensions(event):
            if viewport.winfo_exists():
                vw, vh = event.width, event.height
                req_w = inner.winfo_reqwidth()
                req_h = inner.winfo_reqheight()
                
                # Only force-stretch if the viewport is LARGER than the content
                # This keeps the background consistent but allows scrolling if content is huge
                new_w = max(vw, req_w)
                new_h = max(vh, req_h)
                
                viewport.itemconfig(inner_id, width=new_w, height=new_h)
                viewport.configure(scrollregion=(0, 0, new_w, new_h))
        
        viewport.bind("<Configure>", _sync_dimensions, add="+")
        inner.bind("<Configure>", lambda e: _sync_dimensions(None) if viewport.winfo_exists() else None)
        
        TransparencyManager.apply_transparency(hull, viewport, value, builder)
        TransparencyManager.apply_transparency(hull, inner, value, builder)
        return hull, inner
