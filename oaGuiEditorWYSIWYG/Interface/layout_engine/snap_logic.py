# Interface/layout_engine/snap_logic.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Interface.1
#
# Description: Mathematical logic for snapping coordinates and dimensions to a grid.

def snap_to_grid(value, grid_size=100):
    """
    Snaps a single numeric value to the nearest grid point.
    
    Args:
        value (float): The raw coordinate or dimension.
        grid_size (int): The distance between grid points.
        
    Returns:
        int: The snapped value.
    """
    return round(value / grid_size) * grid_size

def snap_geometry(geometry, grid_size=100):
    """
    Snaps a geometry dictionary to the specified grid.
    
    Args:
        geometry (dict): Dictionary containing x, y, width, and/or height.
        grid_size (int): The distance between grid points.
        
    Returns:
        dict: A new dictionary with snapped values.
    """
    snapped = {}
    if "x" in geometry:
        snapped["x"] = snap_to_grid(geometry["x"], grid_size)
    if "y" in geometry:
        snapped["y"] = snap_to_grid(geometry["y"], grid_size)
    if "width" in geometry:
        snapped["width"] = max(grid_size, snap_to_grid(geometry["width"], grid_size))
    if "height" in geometry:
        snapped["height"] = max(grid_size, snap_to_grid(geometry["height"], grid_size))
    return snapped
