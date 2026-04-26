# graphing/graph_updater.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2205.1
#
# Description: Graph updating and drawing orchestration.

from collections import deque
from typing import Any

import numpy as np

# --- BLIT OPTIMIZATION ENGINE CACHE ---
_bg_cache = {}

def discover_datasets(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Discovers dataset definitions from JSON."""
    return config.get("datasets", [])

def process_initial_data(widget, datasets: list[dict[str, Any]]):
    """Processes initial CSV data for discovered datasets."""
    for ds in datasets:
        ds_id = ds.get("id")
        csv = ds.get("initial_csv_data")
        if ds_id and csv:
            if hasattr(widget, 'dataset_vars') and ds_id in widget.dataset_vars:
                widget.dataset_vars[ds_id].set(csv)

def smooth_data(data: list[float], window_size: int) -> list[float]:
    """Applies a simple moving average smoothing to the data."""
    if window_size <= 1 or len(data) < (window_size // 2):
        return data
    window = np.ones(window_size) / window_size
    smoothed = np.convolve(data, window, mode='same')
    return smoothed.tolist()

def update_line_data(line: Any, x_data: deque, y_data: deque, new_x: float, new_y: float, smoothing: int = 0):
    """Updates line data with optional smoothing."""
    x_data.append(new_x)
    y_data.append(new_y)
    if smoothing > 1 and len(y_data) >= smoothing:
        y_plot = smooth_data(list(y_data), smoothing)
        line.set_data(list(x_data), y_plot)
    else:
        line.set_data(list(x_data), list(y_data))

def load_initial_data(line: Any, x_queue: deque, y_queue: deque, x_vals: list[float], y_vals: list[float], smoothing: int = 0):
    """Loads initial data into queues and updates the line."""
    x_queue.clear()
    y_queue.clear()
    x_queue.extend(x_vals)
    y_queue.extend(y_vals)
    if smoothing > 1 and len(y_vals) >= smoothing:
        y_plot = smooth_data(y_vals, smoothing)
        line.set_data(x_vals, y_plot)
    else:
        line.set_data(x_vals, y_vals)

# Alias for backward compatibility if needed
load_dataset_data = load_initial_data

def autoscale_axes(ax: Any, canvas: Any = None):
    """⚡ MATH ONLY: Recalculates axis limits based on current data."""
    fig = ax.get_figure()
    fig_id = id(fig)
    if fig_id in _bg_cache:
        del _bg_cache[fig_id]
    ax.relim()
    ax.autoscale(enable=True, axis='both', tight=True)
    if canvas:
        canvas.draw_idle()

# Alias for backward compatibility
autoscale_and_redraw = autoscale_axes

def perform_full_draw(ax: Any, canvas: Any):
    """⚡ HEAVY RENDER: Redraws the entire axes structure."""
    autoscale_axes(ax)
    canvas.draw()
    canvas.draw_idle()

def perform_fast_blit(ax: Any, canvas: Any, lines: list[Any]):
    """⚡ BLIT OPTIMIZATION: Redraws ONLY the lines on top of a cached background."""
    fig = ax.get_figure()
    fig_id = id(fig)

    if fig_id not in _bg_cache:
        canvas.draw()
        _bg_cache[fig_id] = canvas.copy_from_bbox(ax.bbox)

    canvas.restore_region(_bg_cache[fig_id])
    for line in lines:
        ax.draw_artist(line)
    canvas.blit(ax.bbox)
    canvas.flush_events()

class GraphDataManager:
    """Legacy wrapper for backward compatibility."""
    discover_datasets = staticmethod(discover_datasets)
    process_initial_data = staticmethod(process_initial_data)
    smooth_data = staticmethod(smooth_data)
    update_line_data = staticmethod(update_line_data)
    load_dataset_data = staticmethod(load_dataset_data)
    load_initial_data = staticmethod(load_initial_data)
    autoscale_axes = staticmethod(autoscale_axes)
    perform_full_draw = staticmethod(perform_full_draw)
    perform_fast_blit = staticmethod(perform_fast_blit)
