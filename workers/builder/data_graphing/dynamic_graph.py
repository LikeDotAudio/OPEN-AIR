import tkinter as tk
from tkinter import ttk
from collections import deque
import time
from typing import Dict, Any, List
import inspect

from workers.logger.logger import debug_logger
from managers.configini.config_reader import Config
from workers.logger.log_utils import _get_log_args

from . import graph_builder
from . import graph_styler
from . import graph_interactor
from . import graph_updater

app_constants = Config.get_instance()

# Globals
current_version = "20260101.000000.1"

class FluxPlotter(tk.Frame):
    """
    A Tkinter-compatible Matplotlib graph widget that dynamically renders
    plots with multiple datasets based on a JSON configuration.
    Refactored to use helper modules for building, styling, interaction, and updating.
    """

    def __init__(self, parent, config: Dict[str, Any], base_mqtt_topic_from_path: str, widget_id: str, **kwargs):
        self.subscriber_router = kwargs.pop('subscriber_router', None)
        self.state_mirror_engine = kwargs.pop('state_mirror_engine', None)
        super().__init__(parent, **kwargs)
        
        self.config = config
        self.base_mqtt_topic_from_path = base_mqtt_topic_from_path
        self.widget_id = widget_id
        
        self.lines: Dict[str, Any] = {}
        self.x_data: Dict[str, deque] = {}
        self.y_data: Dict[str, deque] = {}
        self.datasets_config: Dict[str, Any] = {}
        self.dataset_vars: Dict[str, tk.StringVar] = {}

        self.fig, self.ax, self.canvas = graph_builder.create_base_plot(self, config)
        
        self._initialize_plot_elements()
        self._process_dataset_config()
        self._load_all_initial_data()
        
        debug_logger(message=f"🧪 FluxPlotter '{self.widget_id}' initialized!", **_get_log_args())

    def _initialize_plot_elements(self):
        """Initializes plot elements like lines, styles, and interactions."""
        theme = graph_styler.get_theme_style('dark') # Or get from a global theme manager
        
        # Apply styles
        graph_styler.apply_style(self.ax, self.fig, self.config, theme)

        # Setup interactions
        graph_interactor.setup_interaction(self.fig, self.ax, self.config)

        # Create line objects for each dataset
        for ds_config in self.config.get('datasets', []):
            ds_id = ds_config.get('id')
            if ds_id:
                style = ds_config.get('style', {})
                line, = self.ax.plot([], [],
                                     color=style.get('line_color', 'cyan'),
                                     linewidth=style.get('line_width', 1),
                                     label=ds_config.get('label', ds_id))
                self.lines[ds_id] = line
                self.x_data[ds_id] = deque(maxlen=self.config.get('buffer_size', 100))
                self.y_data[ds_id] = deque(maxlen=self.config.get('buffer_size', 100))

        if len(self.config.get('datasets', [])) > 1:
            self.ax.legend()

    def _on_dataset_var_change(self, dataset_id, *args):
        """Callback for when an individual dataset's StringVar changes."""
        if dataset_id not in self.dataset_vars:
            return
            
        csv_data = self.dataset_vars[dataset_id].get()
        try:
            x_values, y_values = [], []
            lines = csv_data.strip().split('\n')
            if lines and 'x' in lines[0].lower() and 'y' in lines[0].lower():
                lines = lines[1:]
            for line in lines:
                if not line.strip(): continue
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    x_values.append(float(parts[0]))
                    y_values.append(float(parts[1]))
            
            self.load_initial_data(dataset_id, x_values, y_values)
        except Exception as e:
            debug_logger(f"❌ Error processing CSV data for dataset '{dataset_id}': {e}", **_get_log_args())

    def _process_dataset_config(self):
        """Processes 'datasets', creates StringVars, and registers them for MQTT."""
        for ds_config in self.config.get('datasets', []):
            ds_id = ds_config.get('id')
            if ds_id:
                self.datasets_config[ds_id] = ds_config
                dataset_var = tk.StringVar()
                self.dataset_vars[ds_id] = dataset_var
                
                if self.state_mirror_engine:
                    dataset_path = f"{self.widget_id}/datasets/{ds_id}"
                    register_config = {
                        "type": "_PlotDataset",
                        "id": ds_id,
                        "value_default": ds_config.get("initial_csv_data", "")
                    }
                    self.state_mirror_engine.register_widget(dataset_path, dataset_var, self.base_mqtt_topic_from_path, register_config)
                    dataset_var.trace_add("write", lambda *args, ds_id=ds_id: self._on_dataset_var_change(ds_id, *args))
                    self.state_mirror_engine.initialize_widget_state(dataset_path)

    def _load_all_initial_data(self):
        """Loads initial data for all configured datasets by setting the StringVars."""
        for ds_id, ds_config in self.datasets_config.items():
            csv_data = ds_config.get('initial_csv_data')
            if csv_data and ds_id in self.dataset_vars:
                self.dataset_vars[ds_id].set(csv_data)

    def load_initial_data(self, dataset_id: str, x_values: List[float], y_values: List[float]):
        """Loads a complete set of initial data points."""
        if dataset_id not in self.lines: return
        graph_updater.load_initial_data(self.lines[dataset_id], self.x_data[dataset_id], self.y_data[dataset_id], x_values, y_values)
        graph_updater.autoscale_and_redraw(self.ax, self.canvas)

    def update_plot(self, dataset_id: str, x_new: float, y_new: float):
        """Updates a dataset with a new data point."""
        if dataset_id not in self.lines: return
        graph_updater.update_graph_data(self.lines[dataset_id], self.x_data[dataset_id], self.y_data[dataset_id], x_new, y_new)
        graph_updater.autoscale_and_redraw(self.ax, self.canvas)

    def clear_plot(self, dataset_id: str = None):
        """Clears data from a specific dataset or all datasets."""
        if dataset_id and dataset_id in self.lines:
            graph_updater.clear_plot_data(self.lines[dataset_id], self.x_data[dataset_id], self.y_data[dataset_id])
        else:
            for ds_id in self.lines:
                graph_updater.clear_plot_data(self.lines[ds_id], self.x_data[ds_id], self.y_data[ds_id])
        graph_updater.autoscale_and_redraw(self.ax, self.canvas)