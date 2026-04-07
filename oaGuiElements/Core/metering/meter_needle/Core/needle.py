# Core/needle.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import math
from dataclasses import dataclass, asdict
from typing import Optional

# Import the Rust backend
from oaGuiElements.Methods.needle_engine import NeedleEngine
_engine = NeedleEngine()

@dataclass
class NeedleConfig:
    val: float
    min_val: float
    max_val: float
    start_angle_deg: float
    end_angle_deg: float
    extent_deg: float
    main_arc_radius: float
    text_offset_from_arc: float
    color: str
    style: str
    thick: float
    counter_clockwise: bool
    pivot_size: float
    needle_scale: float = 1.0
    tag: str = "vu_needle"

class NeedleDrawer:
    @staticmethod
    def draw_needle(canvas, center_x, center_y, 
                    val, min_val, max_val,
                    start_angle_deg, end_angle_deg, extent_deg,
                    main_arc_radius, text_offset_from_arc,
                    color, style, thick, counter_clockwise, pivot_size,
                    needle_scale=1.0, tag="vu_needle"):
        """
        Draws or updates the needle. Legacy wrapper for draw_with_config.
        """
        config = NeedleConfig(
            val=val, min_val=min_val, max_val=max_val,
            start_angle_deg=start_angle_deg, end_angle_deg=end_angle_deg, extent_deg=extent_deg,
            main_arc_radius=main_arc_radius, text_offset_from_arc=text_offset_from_arc,
            color=color, style=style, thick=thick, counter_clockwise=counter_clockwise,
            pivot_size=pivot_size, needle_scale=needle_scale, tag=tag
        )
        return NeedleDrawer.draw_with_config(canvas, center_x, center_y, config)

    @staticmethod
    def draw_with_config(canvas, cx, cy, config: NeedleConfig):
        """Unified entry point for drawing the needle with a config object (RUST OPTIMIZED)."""
        # Call the Rust engine to do all the heavy math
        geom = _engine.calculate_geometry(float(cx), float(cy), asdict(config))
        if not geom: return

        draw_type = geom.get("draw_type")
        coords = geom.get("coords")
        
        # 2. Try Optimization
        if NeedleDrawer._try_update_existing(canvas, config.tag, draw_type, coords):
            return

        # 3. Full redraw
        existing = canvas.find_withtag(config.tag)
        if existing:
            canvas.delete(config.tag)

        # Style Dispatcher
        if draw_type == "line":
            canvas.create_line(*coords, width=config.thick, fill=config.color, 
                               capstyle=tk.ROUND, tags=(config.tag, "vu_element"))
        elif draw_type == "polygon":
            canvas.create_polygon(*coords, fill=config.color, outline=config.color, tags=(config.tag, "vu_element"))
        elif draw_type == "complex_teardrop":
            # Rust provides the individual points, Python does the specific canvas calls
            canvas.create_line(cx, cy, geom["p1x"], geom["p1y"], width=config.thick, fill=config.color, capstyle=tk.ROUND, tags=(config.tag, "vu_element"))
            canvas.create_polygon([geom["bx"], geom["by"], geom["s1x"], geom["s1y"], geom["p2x"], geom["p2y"], geom["s2x"], geom["s2y"]], 
                                  fill=config.color, outline=config.color, smooth=True, tags=(config.tag, "vu_element"))
            canvas.create_line(geom["p2x"], geom["p2y"], geom["tip_x"], geom["tip_y"], width=config.thick, fill=config.color, capstyle=tk.ROUND, tags=(config.tag, "vu_element"))
        elif draw_type == "complex_hollow_diamond":
            canvas.create_polygon([geom["sx"], geom["sy"], geom["p1x"], geom["p1y"], geom["tip_x"], geom["tip_y"], geom["p2x"], geom["p2y"]], 
                                  fill=config.color, outline=config.color, tags=(config.tag, "vu_element"))
            bg = canvas.cget("bg")
            canvas.create_polygon([geom["cutout_sx"], geom["cutout_sy"], geom["ip1x"], geom["ip1y"], geom["itx"], geom["ity"], geom["ip2x"], geom["ip2y"]], 
                                  fill=bg, outline=bg, tags=(config.tag, "vu_element"))
            canvas.create_line(cx, cy, geom["sx"], geom["sy"], width=config.thick, fill=config.color, tags=(config.tag, "vu_element"))


    @staticmethod
    def _try_update_existing(canvas, tag, draw_type, coords):
        """Attempts to update existing needle coordinates for performance."""
        existing = canvas.find_withtag(tag)
        if not existing or draw_type not in ["line", "polygon"]:
            return False
            
        canvas.coords(tag, *coords)
        return True