# graphing/graph_updater.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from collections import deque
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from typing import List, Any, Dict
import numpy as np
import time

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

def smooth_data(data: List[float], window_size: int) -> List[float]:
    """Applies a simple moving average smoothing to the data."""
    if window_size <= 1 or len(data) < (window_size // 2):
        return data
    window = np.ones(window_size) / window_size
    smoothed = np.convolve(data, window, mode='same')
    return smoothed.tolist()

def update_graph_data(line: Any, x_data: deque, y_data: deque, new_x: float, new_y: float, smoothing: int = 0):
    x_data.append(new_x)
    y_data.append(new_y)
    if smoothing > 1 and len(y_data) >= smoothing:
        y_plot = smooth_data(list(y_data), smoothing)
        line.set_data(list(x_data), y_plot)
    else:
        line.set_data(list(x_data), list(y_data))

def load_initial_data(line: Any, x_data: deque, y_data: deque, x_values: List[float], y_values: List[float], smoothing: int = 0):
    x_data.clear(); y_data.clear()
    x_data.extend(x_values); y_data.extend(y_values)
    if smoothing > 1 and len(y_values) >= smoothing:
        y_plot = smooth_data(y_values, smoothing)
        line.set_data(x_values, y_plot)
    else:
        line.set_data(x_values, y_values)

def clear_plot_data(line: Any, x_data: deque, y_data: deque):
    x_data.clear(); y_data.clear(); line.set_data([], [])

# ⚡ BLIT OPTIMIZATION ENGINE
# redrawing everything (axes, grid, text) is 100x slower than blitting lines.
_bg_cache = {}

def autoscale_axes(ax: Any):
    """
    ⚡ MATH ONLY: Recalculates axis limits based on current data.
    """
    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] autoscale_axes: Recalculating axis limits.", level="TRACE")
    
    # Force background cache invalidation on autoscale
    fig = ax.get_figure()
    fig_id = id(fig)
    if fig_id in _bg_cache:
        del _bg_cache[fig_id]

    ax.relim()
    ax.autoscale(enable=True, axis='both', tight=True)

def render_canvas(canvas: Any):
    """
    ⚡ RENDER ONLY: Commands the UI to redraw the canvas.
    """
    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] render_canvas: Redrawing canvas structure.", level="TRACE")
    
    canvas.draw() # Synchronous draw to update background buffer
    canvas.draw_idle()

def autoscale_and_redraw(ax: Any, canvas: Any):
    """
    ⚡ HIGH PERFORMANCE: Redraws the graph using Blit logic if possible.
    Bypasses Matplotlib's slow 'get_window_extent' text measurement on every frame.
    Refactored for Modular SRP.
    """
    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] graph_updater: Executing full autoscale and redraw sequence.", level="TRACE")

    # SRP REFACTOR: Orchestrate modular actions
    autoscale_axes(ax)
    render_canvas(canvas)

def perform_fast_blit(ax: Any, canvas: Any, lines: List[Any]):
    """
    Redraws ONLY the lines on top of a cached background.
    Stops the 12-second 'get_window_extent' stall cold.
    """
    fig = ax.get_figure()
    fig_id = id(fig)
    
    # ⚡ OPTIMIZATION: Only do full draw once to capture axes/background
    if fig_id not in _bg_cache:
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] graph_updater: Blit cache miss for fig {fig_id}. Capturing background fabric.", level="DEBUG")
        # This is where the get_window_extent stall usually happens, but we only do it once.
        canvas.draw()
        _bg_cache[fig_id] = canvas.copy_from_bbox(ax.bbox)
        
    canvas.restore_region(_bg_cache[fig_id])
    for line in lines:
        ax.draw_artist(line)
    canvas.blit(ax.bbox)
    
    matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] graph_updater: Fast blit redraw complete for {len(lines)} lines.", level="TRACE")
    
    # Flush GUI events to ensure blit shows immediately without waiting for mainloop idle
    canvas.flush_events()