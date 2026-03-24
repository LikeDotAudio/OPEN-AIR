# graphing/dynamic_bar_graph.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import simpledialog
from collections import deque
from typing import Dict, Any, List

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = False    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from . import graph
from . import graph_styler
from . import graph_interactor
from . import graph_updater
from .dynamic_graph import FluxPlotter

class DynamicBarGraph(FluxPlotter):
    """
    A bar-chart version of the dynamic graph widget.
    Inherits most functionality from FluxPlotter but overrides data rendering.
    """
    
    def _initialize_plot_elements(self):
        """Initializes plot elements like bars, styles, and interactions."""
        if BUILDER_DEBUG:
            builder_logger.debug(f"🔬🏗️📊 [BUILDER] DynamicBarGraph '{self.widget_id}' initializing plot elements.")
        
        theme = graph_styler.get_theme_style("dark")
        graph_styler.apply_style(self.ax, self.fig, self.widget_config, theme)

        callbacks = {
            "on_view_change": self._on_view_change,
            "on_setting_change": self._on_setting_change,
            "on_add_marker": self._on_add_marker
        }
        graph_interactor.setup_interaction(self.fig, self.ax, self.widget_config, callbacks)

        self.bar_containers = {}

        # Create placeholder bar containers for each dataset
        for ds_config in self.widget_config.get("datasets", []):
            ds_id = ds_config.get("id")
            if ds_id:
                self.bar_containers[ds_id] = None # Will be created on first data
                self.x_data[ds_id] = deque(maxlen=self.widget_config.get("buffer_size", 100))
                self.y_data[ds_id] = deque(maxlen=self.widget_config.get("buffer_size", 100))
        
        if BUILDER_DEBUG:
            builder_logger.success(f"🔬🏗️📊 [BUILDER] DynamicBarGraph '{self.widget_id}' plot elements initialized.")

    def load_initial_data(self, dataset_id: str, x_values: List[float], y_values: List[float]):
        """Loads data and renders as bars."""
        if dataset_id not in self.bar_containers:
            return
            
        if BUILDER_DEBUG:
            builder_logger.debug(f"🔬🏗️📊 [BUILDER] DynamicBarGraph '{self.widget_id}' loading {len(x_values)} points into dataset '{dataset_id}'.")
            
        # Update deques
        self.x_data[dataset_id].clear()
        self.y_data[dataset_id].clear()
        self.x_data[dataset_id].extend(x_values)
        self.y_data[dataset_id].extend(y_values)
        
        self._render_bars(dataset_id)
        graph_updater.autoscale_and_redraw(self.ax, self.canvas)
        
        if BUILDER_DEBUG:
            builder_logger.success(f"🔬🏗️📊 [BUILDER] DynamicBarGraph '{self.widget_id}' dataset '{dataset_id}' population complete.")

    def update_plot(self, dataset_id: str, x_new: float, y_new: float):
        """Updates a dataset with a new data point and re-renders bars."""
        if dataset_id not in self.bar_containers:
            return
        
        # ⚡ OPTIMIZATION: Check for duplicate data points to prevent redundant redraws
        last_x = self.x_data[dataset_id][-1] if self.x_data[dataset_id] else None
        last_y = self.y_data[dataset_id][-1] if self.y_data[dataset_id] else None
        if x_new == last_x and y_new == last_y:
            return

        if BUILDER_DEBUG:
            builder_logger.trace(f"🔬🏗️📊 [BUILDER] DynamicBarGraph '{self.widget_id}' receiving point ({x_new}, {y_new}) for dataset '{dataset_id}'.")
            
        self.x_data[dataset_id].append(x_new)
        self.y_data[dataset_id].append(y_new)
        
        self._render_bars(dataset_id)
        graph_updater.autoscale_and_redraw(self.ax, self.canvas)

    def _render_bars(self, dataset_id):
        """Internal helper to draw/update bars for a dataset."""
        if BUILDER_DEBUG:
            builder_logger.trace(f"🔬🏗️📊 [BUILDER] DynamicBarGraph '{self.widget_id}' rendering bars for dataset '{dataset_id}'.")
            
        # Remove old bars for this dataset
        if self.bar_containers[dataset_id]:
            for bar in self.bar_containers[dataset_id]:
                bar.remove()
        
        ds_config = next((d for d in self.widget_config.get("datasets", []) if d.get("id") == dataset_id), {})
        style = ds_config.get("style", {})
        
        # Draw new bars
        self.bar_containers[dataset_id] = self.ax.bar(
            list(self.x_data[dataset_id]),
            list(self.y_data[dataset_id]),
            color=style.get("line_color", "cyan"),
            label=ds_config.get("label", dataset_id),
            alpha=0.7
        )
        
    def clear_plot(self, dataset_id: str = None):
        """Clears bar data."""
        ids = [dataset_id] if dataset_id else self.bar_containers.keys()
        for d_id in ids:
            if d_id in self.bar_containers:
                if self.bar_containers[d_id]:
                    for bar in self.bar_containers[d_id]:
                        bar.remove()
                    self.bar_containers[d_id] = None
                self.x_data[d_id].clear()
                self.y_data[d_id].clear()
        graph_updater.autoscale_and_redraw(self.ax, self.canvas)
        
        if BUILDER_DEBUG:
            builder_logger.debug(f"🔬🏗️📊 [BUILDER] DynamicBarGraph '{self.widget_id}' data has been cleared.")
