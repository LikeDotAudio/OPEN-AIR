# break_line/hidden_BreakLine.py
#
# A mixin for creating a horizontal break line (Separator).
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260214.2

import tkinter as tk
from tkinter import ttk

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from oaLogging.Core.logger import builder_logger
from loguru import logger

from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaGuiManager.Core.transparency.transparency import TransparencyManager
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

@WidgetRegistry.register("OcaFold", "BreakLine", "_Separator", "OcaSeparator")
class BuilderBreakLineCreator(TransparencyMixin):
    """Factory class for creating horizontal or vertical break lines."""

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """Creates a horizontal or vertical break line using a Canvas for alpha support."""
        path = config_data.get("path", "unspecified_path")
        
        # ⚡ HARDENED INTERFACE: Extract from context if available
        if context:
            builder_instance = context.builder_instance
        else:
            builder_instance = kwargs.get("builder_instance")

        layout = config_data.get("layout", {})
        
        # 📏 GEOMETRY PARSING
        orientation = config_data.get("Orientation") or layout.get("Orientation") or "horizontal"
        orientation = orientation.lower()
        
        thickness = layout.get("thickness") or layout.get("height") if orientation == "horizontal" else layout.get("width")
        thickness = int(thickness) if thickness else 1
        
        style = config_data.get("style", "normal").upper()
        if config_data.get("type") == "OcaFold": style = "FOLD"

        length = layout.get("width") if orientation == "horizontal" else layout.get("height")
        
        padx = int(layout.get("padx", 0))
        pady = int(layout.get("pady", 0))
        line_color = layout.get("colour") or layout.get("color") or config_data.get("color") or "#888888"

        # 🎨 COLORS
        try:
            p_bg = parent_widget.cget("bg")
            if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
        except:
            p_bg = "#2b2b2b"

        # 🏗️ CONSTRUCTION
        if style == "FOLD":
            thickness = max(thickness, 4) 

        if orientation == "vertical":
            frame_w = thickness + 2 * padx
            frame_h = int(length) if length else 1
            frame = tk.Canvas(parent_widget, width=frame_w, height=frame_h, bd=0, highlightthickness=0, relief="flat", bg=p_bg)
        else:
            frame_h = thickness + 2 * pady
            frame_w = int(length) if length else 1
            frame = tk.Canvas(parent_widget, width=frame_w, height=frame_h, bd=0, highlightthickness=0, relief="flat", bg=p_bg)

        # ⚡ AUTO-STRETCH
        if not layout.get("sticky"):
            config_data.setdefault("layout", {})["sticky"] = "ew" if orientation == "horizontal" else "ns"

        # Apply Industrial Transparency
        if builder_instance and hasattr(builder_instance, '_apply_transparency'):
            TransparencyManager.apply_transparency(frame, frame, config_data, builder_instance)

        def redraw_line():
            if not frame.winfo_exists(): return
            frame.delete("break_line")
            if hasattr(frame, 'panel_bg_image') and not frame.find_withtag("panel_bg_slice"):
                 frame.create_image(0, 0, image=frame.panel_bg_image, anchor="nw", tags="panel_bg_slice")
            
            w, h = frame.winfo_width(), frame.winfo_height()
            
            if style == "FOLD":
                if getattr(builder_instance, "is_editor", False):
                    if orientation == "vertical":
                        cx = w / 2
                        frame.create_line(cx - 1, pady, cx - 1, max(pady + 1, h - pady), fill="#FFFFFF", width=1, tags="break_line", stipple="gray50")
                        frame.create_line(cx + 1, pady, cx + 1, max(pady + 1, h - pady), fill="#000000", width=2, tags="break_line")
                    else:
                        cy = h / 2
                        frame.create_line(padx, cy - 1, max(padx + 1, w - padx), cy - 1, fill="#FFFFFF", width=1, tags="break_line", stipple="gray50")
                        frame.create_line(padx, cy + 1, max(padx + 1, w - padx), cy + 1, fill="#000000", width=2, tags="break_line")
            else:
                if orientation == "vertical":
                    cx = w / 2
                    frame.create_line(cx, pady, cx, max(pady + 1, h - pady), fill=line_color, width=thickness, tags="break_line")
                else:
                    cy = h / 2
                    frame.create_line(padx, cy, max(padx + 1, w - padx), cy, fill=line_color, width=thickness, tags="break_line")
            frame.tag_raise("break_line")

        frame._draw = redraw_line
        frame.render = redraw_line
        frame.bind("<Configure>", lambda e: redraw_line(), add="+")
        return frame

    def make_break_line(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderBreakLineCreator.make(parent_widget, config_data, context, builder_instance=self, **kwargs)

class BreakLineCreatorMixin:
    """A mixin for legacy support."""
    def _create_break_line(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderBreakLineCreator.make(parent_widget, config_data, context, builder_instance=self, **kwargs)
