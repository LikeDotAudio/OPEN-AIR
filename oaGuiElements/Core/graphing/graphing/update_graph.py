# graphing/update_graph.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: update_graph.py

from collections import deque
from typing import List, Any, Dict
import numpy as np
import time
from oaLogging.Core.logger import builder_logger

# --- BLIT OPTIMIZATION ENGINE CACHE ---
_bg_cache = {}

class GraphDataManager:
    """Handles data discovery, processing, and core drawing orchestration."""

    @staticmethod
    def discover_datasets(config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discovers dataset definitions from JSON."""
        return config.get("datasets", [])

    @staticmethod
    def process_initial_data(widget, datasets: List[Dict[str, Any]]):
        """Processes initial CSV data for discovered datasets."""
        for ds in datasets:
            ds_id = ds.get("id")
            csv = ds.get("initial_csv_data")
            if ds_id and csv:
                if hasattr(widget, 'dataset_vars') and ds_id in widget.dataset_vars:
                    widget.dataset_vars[ds_id].set(csv)

    @staticmethod
    def smooth_data(data: List[float], window_size: int) -> List[float]:
        """Applies a simple moving average smoothing to the data."""
        if window_size <= 1 or len(data) < (window_size // 2):
            return data
        window = np.ones(window_size) / window_size
        smoothed = np.convolve(data, window, mode='same')
        return smoothed.tolist()

    @staticmethod
    def update_line_data(line: Any, x_data: deque, y_data: deque, new_x: float, new_y: float, smoothing: int = 0):
        x_data.append(new_x)
        y_data.append(new_y)
        if smoothing > 1 and len(y_data) >= smoothing:
            y_plot = GraphDataManager.smooth_data(list(y_data), smoothing)
            line.set_data(list(x_data), y_plot)
        else:
            line.set_data(list(x_data), list(y_data))

    @staticmethod
    def load_dataset_data(line: Any, x_queue: deque, y_queue: deque, x_vals: List[float], y_vals: List[float], smoothing: int = 0):
        x_queue.clear(); y_queue.clear()
        x_queue.extend(x_vals); y_queue.extend(y_vals)
        if smoothing > 1 and len(y_vals) >= smoothing:
            y_plot = GraphDataManager.smooth_data(y_vals, smoothing)
            line.set_data(x_vals, y_plot)
        else:
            line.set_data(x_vals, y_vals)

    @staticmethod
    def autoscale_axes(ax: Any):
        """⚡ MATH ONLY: Recalculates axis limits based on current data."""
        fig_id = id(ax.get_figure())
        if fig_id in _bg_cache: del _bg_cache[fig_id]
        ax.relim()
        ax.autoscale(enable=True, axis='both', tight=True)

    @staticmethod
    def perform_full_draw(ax: Any, canvas: Any):
        """⚡ HEAVY RENDER: Redraws the entire axes structure."""
        GraphDataManager.autoscale_axes(ax)
        canvas.draw()
        canvas.draw_idle()

    @staticmethod
    def perform_fast_blit(ax: Any, canvas: Any, lines: List[Any]):
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
