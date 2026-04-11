# Core/layout/snap_logic.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Mathematical logic for snapping coordinates and dimensions to a grid.

def snap_to_grid(value, grid_size=100):
    """Snaps a single value to the nearest grid point."""
    return round(value / grid_size) * grid_size

def snap_geometry(geometry, grid_size=100):
    """
    Snaps a geometry dictionary (x, y, width, height) to the grid.
    Returns a new dictionary with snapped values.
    """
    snapped = {}
    if "x" in geometry: snapped["x"] = snap_to_grid(geometry["x"], grid_size)
    if "y" in geometry: snapped["y"] = snap_to_grid(geometry["y"], grid_size)
    if "width" in geometry: snapped["width"] = max(grid_size, snap_to_grid(geometry["width"], grid_size))
    if "height" in geometry: snapped["height"] = max(grid_size, snap_to_grid(geometry["height"], grid_size))
    return snapped
