# oaGui/Core/break_line/break_line_creator.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Modular.1
#
# Description: Factory for creating horizontal or vertical break lines (separators).
# Specialized to handle "OcaFold" visual indicators for industrial layouts.

import tkinter as tk

from oaGui.Constants.builder_constants import BREAKLINE_DEFAULT_COLOR, BREAKLINE_MIN_THICKNESS
from oaGui.Core.factory.widget_registry import WidgetRegistry
from oaGui.Core.transparency.transparency import TransparencyManager
from oaGui.Core.transparency.transparency_mixin import TransparencyMixin


@WidgetRegistry.register("OcaFold", "BreakLine", "_Separator", "OcaSeparator")
class BreakLineCreator(TransparencyMixin):
    """Factory for industrial break lines and fold indicators."""

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """Constructs a Canvas-based break line with transparency support."""
        builder = context.builder_instance if context else kwargs.get("builder_instance")
        layout = config_data.get("layout", {})

        # 1. Parse Geometry and Style
        params = BreakLineCreator._parse_parameters(config_data, layout)

        # 2. Setup Canvas
        canvas = BreakLineCreator._create_canvas(parent_widget, params)

        # 3. Apply Defaults and Transparency
        if not layout.get("sticky"):
            config_data.setdefault("layout", {})["sticky"] = "ew" if params["is_horizontal"] else "ns"

        if builder:
            TransparencyManager.apply_transparency(canvas, canvas, config_data, builder)

        # 4. Redraw Pipeline
        def redraw():
            BreakLineCreator._draw_line_logic(canvas, params, builder)

        canvas._draw = redraw
        canvas.render = redraw
        canvas.bind("<Configure>", lambda e: redraw(), add="+")

        return canvas

    @staticmethod
    def _parse_parameters(config, layout):
        """Standardizes input dictionary parsing for the creator."""
        orient = (config.get("Orientation") or layout.get("Orientation") or "horizontal").lower()
        is_horiz = orient == "horizontal"

        thick = layout.get("thickness") or layout.get("height") if is_horiz else layout.get("width")
        thick = int(thick) if thick else 1

        style = config.get("style", "normal").upper()
        if config.get("type") == "OcaFold":
            style = "FOLD"
            thick = max(thick, BREAKLINE_MIN_THICKNESS)

        return {
            "is_horizontal": is_horiz,
            "thickness": thick,
            "style": style,
            "length": layout.get("width") if is_horiz else layout.get("height"),
            "padx": int(layout.get("padx", 0)),
            "pady": int(layout.get("pady", 0)),
            "color": layout.get("colour") or layout.get("color") or config.get("color") or BREAKLINE_DEFAULT_COLOR
        }

    @staticmethod
    def _create_canvas(parent, p):
        """Initializes the physical Tkinter Canvas with calculated base dimensions."""
        try:
            bg = parent.cget("bg")
            if not bg or not bg.startswith("#"): bg = "#2b2b2b"
        except:
            bg = "#2b2b2b"

        if not p["is_horizontal"]:
            w, h = p["thickness"] + 2 * p["padx"], int(p["length"]) if p["length"] else 1
        else:
            w, h = int(p["length"]) if p["length"] else 1, p["thickness"] + 2 * p["pady"]

        return tk.Canvas(parent, width=w, height=h, bd=0, highlightthickness=0, relief="flat", bg=bg)

    @staticmethod
    def _draw_line_logic(canvas, p, builder):
        """Handles the actual drawing commands for simple lines vs fold indicators."""
        if not canvas.winfo_exists(): return
        canvas.delete("content")

        # Background slice support
        if hasattr(canvas, 'panel_bg_image') and not canvas.find_withtag("panel_bg_slice"):
             canvas.create_image(0, 0, image=canvas.panel_bg_image, anchor="nw", tags="panel_bg_slice")

        w, h = canvas.winfo_width(), canvas.winfo_height()

        if p["style"] == "FOLD" and getattr(builder, "is_editor", False):
            BreakLineCreator._draw_fold_indicator(canvas, p, w, h)
        else:
            BreakLineCreator._draw_standard_line(canvas, p, w, h)

        canvas.tag_raise("content")

    @staticmethod
    def _draw_standard_line(canvas, p, w, h):
        """Draws a solid single-color line."""
        if p["is_horizontal"]:
            cy = h / 2
            canvas.create_line(p["padx"], cy, max(p["padx"] + 1, w - p["padx"]), cy,
                               fill=p["color"], width=p["thickness"], tags="content")
        else:
            cx = w / 2
            canvas.create_line(cx, p["pady"], cx, max(p["pady"] + 1, h - p["pady"]),
                               fill=p["color"], width=p["thickness"], tags="content")

    @staticmethod
    def _draw_fold_indicator(canvas, p, w, h):
        """Draws high-contrast highlight/shadow lines to represent a metal fold."""
        if p["is_horizontal"]:
            cy = h / 2
            canvas.create_line(p["padx"], cy - 1, max(p["padx"] + 1, w - p["padx"]), cy - 1,
                               fill="#FFFFFF", width=1, tags="content", stipple="gray50")
            canvas.create_line(p["padx"], cy + 1, max(p["padx"] + 1, w - p["padx"]), cy + 1,
                               fill="#000000", width=2, tags="content")
        else:
            cx = w / 2
            canvas.create_line(cx - 1, p["pady"], cx - 1, max(p["pady"] + 1, h - p["pady"]),
                               fill="#FFFFFF", width=1, tags="content", stipple="gray50")
            canvas.create_line(cx + 1, p["pady"], cx + 1, max(p["pady"] + 1, h - p["pady"]),
                               fill="#000000", width=2, tags="content")
