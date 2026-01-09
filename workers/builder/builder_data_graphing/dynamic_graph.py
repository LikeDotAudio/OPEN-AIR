# builder_data_graphing/dynamic_graph.py
#
# A Tkinter-compatible Matplotlib graph widget that dynamically renders
# plots with multiple datasets based on a JSON configuration.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1
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

    # Initializes the FluxPlotter widget.
    # This constructor sets up the Matplotlib figure and axes, initializes data structures
    # for plotting, processes dataset configurations, and loads any initial data.
    # Inputs:
    #     parent: The parent tkinter widget.
    #     config (Dict[str, Any]): A dictionary containing the configuration for the plot.
    #     base_mqtt_topic_from_path (str): The base MQTT topic for the widget.
    #     widget_id (str): The unique identifier for the widget.
    #     **kwargs: Additional keyword arguments including 'subscriber_router' and 'state_mirror_engine'.
    # Outputs:
    #     None.
    def __init__(
        self,
        parent,
        config: Dict[str, Any],
        base_mqtt_topic_from_path: str,
        widget_id: str,
        **kwargs,
    ):
        self.subscriber_router = kwargs.pop("subscriber_router", None)
        self.state_mirror_engine = kwargs.pop("state_mirror_engine", None)
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

        self.bind("<Configure>", self._on_resize)

    # Handles the resizing of the plot widget.
    # This method adjusts the size of the Matplotlib figure to match the new dimensions
    # of the Tkinter widget and triggers a redraw of the canvas.
    # Inputs:
    #     event: The tkinter Configure event object.
    # Outputs:
    #     None.
    def _on_resize(self, event):
        if hasattr(self, "fig"):
            w_pixels = event.width
            h_pixels = event.height
            dpi = self.fig.get_dpi()

            if dpi > 0 and w_pixels > 1 and h_pixels > 1:
                self.fig.set_size_inches(w_pixels / dpi, h_pixels / dpi)
                graph_updater.autoscale_and_redraw(self.ax, self.canvas)

    # Initializes core plot elements, including styling and interaction.
    # This method applies themes, sets up interactive features for the plot, and
    # creates the initial line objects for each dataset defined in the configuration.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def _initialize_plot_elements(self):
        """Initializes plot elements like lines, styles, and interactions."""
        theme = graph_styler.get_theme_style(
            "dark"
        )  # Or get from a global theme manager

        # Apply styles
        graph_styler.apply_style(self.ax, self.fig, self.config, theme)

        # Setup interactions
        graph_interactor.setup_interaction(self.fig, self.ax, self.config)

        # Create line objects for each dataset
        for ds_config in self.config.get("datasets", []):
            ds_id = ds_config.get("id")
            if ds_id:
                style = ds_config.get("style", {})
                (line,) = self.ax.plot(
                    [],
                    [],
                    color=style.get("line_color", "cyan"),
                    linewidth=style.get("line_width", 1),
                    label=ds_config.get("label", ds_id),
                )
                self.lines[ds_id] = line
                self.x_data[ds_id] = deque(maxlen=self.config.get("buffer_size", 100))
                self.y_data[ds_id] = deque(maxlen=self.config.get("buffer_size", 100))

        if len(self.config.get("datasets", [])) > 1:
            self.ax.legend()

    # Callback for when an individual dataset's StringVar changes.
    # This method is triggered when new CSV data for a dataset is received. It parses
    # the CSV, extracts x and y values, and loads this data into the plot.
    # Inputs:
    #     dataset_id (str): The ID of the dataset that changed.
    #     *args: Additional arguments from the StringVar trace.
    # Outputs:
    #     None.
    def _on_dataset_var_change(self, dataset_id, *args):
        """Callback for when an individual dataset's StringVar changes."""
        if dataset_id not in self.dataset_vars:
            return

        csv_data = self.dataset_vars[dataset_id].get()
        debug_logger(
            f"Processing CSV data for dataset '{dataset_id}':\n{csv_data}",
            **_get_log_args(),
        )
        try:
            x_values, y_values = [], []
            lines = csv_data.strip().split("\n")
            if lines and "x" in lines[0].lower() and "y" in lines[0].lower():
                lines = lines[1:]
            for line in lines:
                if not line.strip():
                    continue
                parts = line.strip().split(",")
                if len(parts) >= 2:
                    x_values.append(float(parts[0]))
                    y_values.append(float(parts[1]))

            debug_logger(f"Extracted x_values: {x_values}", **_get_log_args())
            debug_logger(f"Extracted y_values: {y_values}", **_get_log_args())
            self.load_initial_data(dataset_id, x_values, y_values)
        except Exception as e:
            debug_logger(
                f"❌ Error processing CSV data for dataset '{dataset_id}': {e}",
                **_get_log_args(),
            )

    # Processes the configuration for all datasets.
    # This method iterates through the dataset definitions in the plot's configuration,
    # creates tkinter StringVars for each, and registers them with the state management
    # engine for MQTT communication.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def _process_dataset_config(self):
        """Processes 'datasets', creates StringVars, and registers them for MQTT."""
        for ds_config in self.config.get("datasets", []):
            ds_id = ds_config.get("id")
            if ds_id:
                self.datasets_config[ds_id] = ds_config
                dataset_var = tk.StringVar()
                self.dataset_vars[ds_id] = dataset_var

                if self.state_mirror_engine:
                    dataset_path = f"{self.widget_id}/datasets/{ds_id}"
                    register_config = {
                        "type": "_PlotDataset",
                        "id": ds_id,
                        "value_default": ds_config.get("initial_csv_data", ""),
                    }
                    self.state_mirror_engine.register_widget(
                        dataset_path,
                        dataset_var,
                        self.base_mqtt_topic_from_path,
                        register_config,
                    )
                    dataset_var.trace_add(
                        "write",
                        lambda *args, ds_id=ds_id: self._on_dataset_var_change(
                            ds_id, *args
                        ),
                    )
                    self.state_mirror_engine.initialize_widget_state(dataset_path)

    # Loads initial data for all configured datasets.
    # This method populates the plot with any initial CSV data specified in the
    # configuration for each dataset by setting their corresponding StringVars.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def _load_all_initial_data(self):
        """Loads initial data for all configured datasets by setting the StringVars."""
        for ds_id, ds_config in self.datasets_config.items():
            csv_data = ds_config.get("initial_csv_data")
            if csv_data and ds_id in self.dataset_vars:
                self.dataset_vars[ds_id].set(csv_data)

    # Loads a complete set of initial data points for a specific dataset.
    # This method takes lists of x and y values and loads them into the plot for
    # the specified dataset, then triggers an autoscale and redraw.
    # Inputs:
    #     dataset_id (str): The ID of the dataset to load data into.
    #     x_values (List[float]): A list of x-axis values.
    #     y_values (List[float]): A list of y-axis values.
    # Outputs:
    #     None.
    def load_initial_data(
        self,
        dataset_id: str,
        x_values: List[float],
        y_values: List[float],
    ):
        """Loads a complete set of initial data points."""
        debug_logger(
            f"Loading initial data for dataset '{dataset_id}'", **_get_log_args()
        )
        if dataset_id not in self.lines:
            return
        graph_updater.load_initial_data(
            self.lines[dataset_id],
            self.x_data[dataset_id],
            self.y_data[dataset_id],
            x_values,
            y_values,
        )
        graph_updater.autoscale_and_redraw(self.ax, self.canvas)

    # Updates a specific dataset with a new data point.
    # This method adds a single new (x, y) data point to the specified dataset
    # and then triggers an autoscale and redraw of the plot.
    # Inputs:
    #     dataset_id (str): The ID of the dataset to update.
    #     x_new (float): The new x-axis value.
    #     y_new (float): The new y-axis value.
    # Outputs:
    #     None.
    def update_plot(self, dataset_id: str, x_new: float, y_new: float):
        """Updates a dataset with a new data point."""
        if dataset_id not in self.lines:
            return
        graph_updater.update_graph_data(
            self.lines[dataset_id],
            self.x_data[dataset_id],
            self.y_data[dataset_id],
            x_new,
            y_new,
        )
        graph_updater.autoscale_and_redraw(self.ax, self.canvas)

    # Clears data from one or all datasets on the plot.
    # This method can clear all data points from a specified dataset or from all
    # datasets if no specific dataset ID is provided.
    # Inputs:
    #     dataset_id (str, optional): The ID of the dataset to clear. If None, all datasets are cleared.
    # Outputs:
    #     None.
    def clear_plot(self, dataset_id: str = None):
        """Clears data from a specific dataset or all datasets."""
        if dataset_id and dataset_id in self.lines:
            graph_updater.clear_plot_data(
                self.lines[dataset_id], self.x_data[dataset_id], self.y_data[dataset_id]
            )
        else:
            for ds_id in self.lines:
                graph_updater.clear_plot_data(
                    self.lines[ds_id], self.x_data[ds_id], self.y_data[ds_id]
                )
        graph_updater.autoscale_and_redraw(self.ax, self.canvas)