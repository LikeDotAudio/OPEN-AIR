# oaGui/Workers/rendering/fast_render_service.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for rendering lightweight placeholder frames for fast UI previews.

import tkinter as tk


def render_fast_widget_placeholder(parent, widget_data, path, builder):
    """Constructs a sized frame to represent a widget without functional overhead."""
    geom = widget_data.get("geometry", {})
    width = widget_data.get("width") or geom.get("width")
    height = widget_data.get("height") or geom.get("height")

    placeholder = tk.Frame(
        parent,
        bg="#3d3d3d",
        highlightbackground="#555555",
        highlightthickness=1
    )

    # ⚡ SIZING
    if width:
        try: placeholder.config(width=max(1, int(float(width))))
        except (ValueError, TypeError): pass
    if height:
        try: placeholder.config(height=max(1, int(float(height))))
        except (ValueError, TypeError): pass

    # ⚡ PREVENT AUTO-SHRINK
    if width or height:
        placeholder.grid_propagate(False)
        placeholder.pack_propagate(False)

    if hasattr(builder, 'bind_to_widget'):
        builder.bind_to_widget(placeholder)

    placeholder._oca_path = path
    return placeholder
