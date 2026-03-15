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
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.Display.transparency.transparency_mixin import TransparencyMixin

class BreakLineCreatorMixin(TransparencyMixin):
    """A mixin for creating a horizontal break line (Separator)."""

    def _create_break_line(self, parent_widget, config_data, context=None, **kwargs):
        """Creates a horizontal or vertical break line using a Canvas for alpha support."""
        path = config_data.get("path", "unspecified_path")
        
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️📏 [BUILDER] '{path}': Entering _create_break_line")
            builder_logger.debug(f"📜📑💻 [CONFIG] '{path}' Raw config: {config_data}")

        # ⚡ HARDENED INTERFACE: Extract from context if available
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
            if BUILDER_DEBUG: builder_logger.trace(f"🔗🗂️⚙️ [CONTEXT] '{path}': Extracted from WidgetContext.")
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self
            if BUILDER_DEBUG: builder_logger.debug(f"⚠️🔔🖱️ [CONTEXT] '{path}': Context missing; fell back to self/kwargs.")

        layout = config_data.get("layout", {})
        
        # 📏 GEOMETRY PARSING
        # Default to horizontal if not specified
        orientation = config_data.get("Orientation") or layout.get("Orientation") or "horizontal"
        orientation = orientation.lower()
        
        # thickness: how thick the line is
        thickness = layout.get("thickness") or layout.get("height") if orientation == "horizontal" else layout.get("width")
        thickness = int(thickness) if thickness else 1
        
        # style: "normal" or "FOLD"
        style = config_data.get("style", "normal").upper()
        if config_data.get("type") == "OcaFold": style = "FOLD"

        # length: how long the line is (if specified, otherwise fills)
        length = layout.get("width") if orientation == "horizontal" else layout.get("height")
        
        padx = int(layout.get("padx", 0))
        pady = int(layout.get("pady", 0))
        # 🎨 BRIGHTER DEFAULT: #888888 is more visible than #555555 on dark backgrounds
        line_color = layout.get("colour") or layout.get("color") or config_data.get("color") or "#888888"

        if BUILDER_DEBUG: 
            builder_logger.debug(f"📐📏🔳 [LAYOUT] '{path}': orient={orientation}, thickness={thickness}, style={style}, color={line_color}, pad=({padx},{pady})")
        
        # 🎨 COLORS
        try:
            p_bg = parent_widget.cget("bg")
            if not p_bg or not p_bg.startswith("#"): p_bg = "#2b2b2b"
        except:
            p_bg = "#2b2b2b"

        # 🏗️ CONSTRUCTION
        # Calculate frame size based on thickness and internal padding
        if style == "FOLD":
            # Folds need a bit more space for the 2-line effect (highlight + shadow)
            thickness = max(thickness, 4) 

        if orientation == "vertical":
            frame_w = thickness + 2 * padx
            frame_h = int(length) if length else 1 # Let grid/pack expand it
            frame = tk.Canvas(parent_widget, width=frame_w, height=frame_h, bd=0, highlightthickness=0, relief="flat", bg=p_bg)
        else:
            frame_h = thickness + 2 * pady
            frame_w = int(length) if length else 1 # Let grid/pack expand it
            frame = tk.Canvas(parent_widget, width=frame_w, height=frame_h, bd=0, highlightthickness=0, relief="flat", bg=p_bg)

        # ⚡ AUTO-STRETCH: If no sticky is provided in layout, force it to fill its axis
        if not layout.get("sticky"):
            config_data.setdefault("layout", {})["sticky"] = "ew" if orientation == "horizontal" else "ns"

        # Apply Industrial Transparency
        if hasattr(self, '_apply_transparency'):
            if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] '{path}': Applying transparency.")
            self._apply_transparency(frame, frame, config_data, builder_instance)

        def redraw_line():
            if not frame.winfo_exists(): return
            frame.delete("break_line")
            
            # Preserve industrial slice if it exists
            if hasattr(frame, 'panel_bg_image') and not frame.find_withtag("panel_bg_slice"):
                 frame.create_image(0, 0, image=frame.panel_bg_image, anchor="nw", tags="panel_bg_slice")
            
            w = frame.winfo_width()
            h = frame.winfo_height()
            
            if style == "FOLD":
                # Only draw the extra lines if we are in the editor
                if getattr(builder_instance, "is_editor", False):
                    if orientation == "vertical":
                        cx = w / 2
                        # Highlight (left side of crease) - Using White with 60% alpha lookalike
                        frame.create_line(cx - 1, pady, cx - 1, max(pady + 1, h - pady), fill="#FFFFFF", width=1, tags="break_line", stipple="gray50")
                        # Shadow (right side of crease) - Using Black with 100% alpha lookalike
                        frame.create_line(cx + 1, pady, cx + 1, max(pady + 1, h - pady), fill="#000000", width=2, tags="break_line")
                    else:
                        cy = h / 2
                        # Highlight (top side of crease)
                        frame.create_line(padx, cy - 1, max(padx + 1, w - padx), cy - 1, fill="#FFFFFF", width=1, tags="break_line", stipple="gray50")
                        # Shadow (bottom side of crease)
                        frame.create_line(padx, cy + 1, max(padx + 1, w - padx), cy + 1, fill="#000000", width=2, tags="break_line")
            else:
                if orientation == "vertical":
                    cx = w / 2
                    # Use entire height minus padding
                    frame.create_line(cx, pady, cx, max(pady + 1, h - pady), fill=line_color, width=thickness, tags="break_line")
                else:
                    cy = h / 2
                    # Use entire width minus padding
                    frame.create_line(padx, cy, max(padx + 1, w - padx), cy, fill=line_color, width=thickness, tags="break_line")
            
            frame.tag_raise("break_line")

        def sync_bg():
            redraw_line()
            
        frame._draw = sync_bg
        frame.render = sync_bg
        frame.bind("<Configure>", lambda e: redraw_line(), add="+")
        
        if BUILDER_DEBUG: builder_logger.success(f"✅🆗📏 [SUCCESS] '{path}': The {orientation} break line has materialized!")
        return frame
