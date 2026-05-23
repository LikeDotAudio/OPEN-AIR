# oaGui/Workers/rendering/widget_grid_applicator.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for applying physical grid placement and padding to GUI widgets.

def apply_widget_to_grid(widget, widget_data, batch_data, builder):
    """Calculates and applies grid coordinates and superficial padding."""
    if not widget:
        return

    layout = widget_data.get("layout", {})
    superficial_pad = getattr(builder, 'superficial_pad', 0)

    widget.grid(
        row=layout.get("row", batch_data["r"]),
        column=layout.get("column", batch_data["c"]),
        columnspan=layout.get("col_span", 1),
        rowspan=layout.get("row_span", 1),
        padx=batch_data["padx"] + superficial_pad,
        pady=batch_data["pady"] + superficial_pad,
        sticky=batch_data["sticky"]
    )
