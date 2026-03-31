# layout/overlay.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk
# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from oaLogging.Core.logger import GUI_LOGGER as logger
from ...layout_overlays import selection, structure, blocks, columns, sizing, sticky, alignment, colors

class OverlayManager:
    """Manages the recursive application of design controls (structure, sticky, sizing, etc.) to widgets."""

    def __init__(self, workspace):
        self.workspace = workspace

    def apply_outlines(self, container):
        if not container or not container.winfo_exists(): return
        self._recursive_clear(container)
        self._recursive_apply(container)

    def _recursive_clear(self, container):
        for child in list(container.winfo_children()):
            if getattr(child, '_is_design_overlay', False):
                try: child.destroy()
                except Exception as e: logger.trace(f"Failed to destroy child overlay: {e}")
            elif isinstance(child, (tk.Frame, ttk.Frame, tk.Canvas, tk.LabelFrame)):
                self._recursive_clear(child)

    def _recursive_apply(self, container, depth=0):
        if depth > 10: return
        for child in container.winfo_children():
            if getattr(child, '_is_design_overlay', False): continue
            
            path = getattr(child, '_oca_path', None)
            if path and "unknown" not in path:
                self._inject_controls(child)
            
            if isinstance(child, (tk.Frame, ttk.Frame, tk.Canvas, tk.LabelFrame)):
                self._recursive_apply(child, depth + 1)

    def _inject_controls(self, widget):
        try:
            path = getattr(widget, '_oca_path', 'unknown')
            is_focused = (self.workspace.focused_path == path)
            design_elements, sync_funcs = [], []

            modules = [selection, structure, blocks, columns, sizing, sticky, alignment, colors]
            for mod in modules:
                sync_fn = mod.apply_design_overlay(self.workspace, widget, path, is_focused, design_elements)
                if sync_fn: sync_funcs.append(sync_fn)

            def _sync_pos(event=None):
                if not widget.winfo_exists(): return
                try:
                    x, y, w, h = widget.winfo_x(), widget.winfo_y(), widget.winfo_width(), widget.winfo_height()
                    if w <= 1 or h <= 1: return
                    for sync_fn in sync_funcs: sync_fn(x, y, w, h)
                except tk.TclError: pass
            
            if hasattr(widget, '_oca_configure_sid'):
                try: widget.unbind("<Configure>", widget._oca_configure_sid)
                except Exception as e: logger.trace(f"Failed to unbind from widget: {e}")
            widget._oca_configure_sid = widget.bind("<Configure>", _sync_pos, add="+")
            widget.after(100, _sync_pos)
                
        except Exception:
            logger.exception(f"❌ Error injecting handles for {getattr(widget, '_oca_path', 'unknown')}")
