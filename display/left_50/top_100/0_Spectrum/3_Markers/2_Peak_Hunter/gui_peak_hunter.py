# display/left_50/top_100/0_Spectrum Analizer/3_markers/2_peak_hunter/gui_peak_hunter.py
#
# This file (gui_peak_hunter.py) provides the MarkerPeakHunterGUI component for the Peak Hunter tab.
# Now patched to handle ModuleLoader arguments safely!
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
# Version: 20251229.1700.1

import os
import inspect
import datetime
import tkinter as tk
from tkinter import ttk
import pathlib
from tkinter import filedialog
import pandas as pd  # Explicit import for data handling

# --- Module Imports ---
from managers.configini.config_reader import Config
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

# Import CSV export utility - Wrapping in try/except in case it's missing during refactor
try:
    from workers.exporters.worker_file_csv_export import CsvExportUtility

    CSV_EXPORT_AVAILABLE = True
except ImportError:
    CSV_EXPORT_AVAILABLE = False

# Globals
app_constants = Config.get_instance()  # Get the singleton instance
current_version = "20251229.1700.1"
current_version_hash = 32806991192

# --- Global Scope Variables ---
current_file_path = pathlib.Path(__file__).resolve()
# Robust project root detection:
# Assuming structure: ProjectRoot/display/left_50/top_100/0_Spectrum Analizer/3_markers/2_peak_hunter/gui_peak_hunter.py
# That is 7 levels deep.
project_root = current_file_path.parents[6]
current_file = str(current_file_path.relative_to(project_root)).replace("\\", "/")


class MarkerPeakHunterGUI(ttk.Frame):
    """
    The main GUI class for the Peak Hunter tab.
    """

    def __init__(self, parent, json_path=None, config=None, **kwargs):
        """
        Initialize the Marker Peak Hunter GUI.

        Args:
            parent: The parent widget.
            json_path (str, optional): Path to config file (passed by ModuleLoader).
            config (dict, optional): Configuration dictionary (passed by ModuleLoader).
            **kwargs: Additional keyword arguments for the Frame.
        """
        # 1. Initialize Parent Frame (Cleanly!)
        super().__init__(parent, **kwargs)

        # 2. Absorb Arguments (The Critical Fix!)
        self.json_path = json_path
        self.config_data = config if config else {}

        # 3. Extract Core Dependencies
        self.state_mirror_engine = self.config_data.get("state_mirror_engine")
        self.subscriber_router = self.config_data.get("subscriber_router")

        # Initialize helper classes
        if CSV_EXPORT_AVAILABLE:
            self.csv_export_util = CsvExportUtility(self.print_to_gui)
        else:
            self.csv_export_util = None

        # 4. Initialize UI
        self._init_ui()

    def print_to_gui(self, message):
        """Prints a message to the console."""
        print(message)

    def _init_ui(self):
        current_function_name = inspect.currentframe().f_code.co_name

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🖥️🟢 Initializing the MarkerPeakHunterGUI.", **_get_log_args()
            )

        try:
            # --- Main Layout ---

            # Top Control Bar
            self.control_frame = ttk.Frame(self)
            self.control_frame.pack(side="top", fill="x", padx=5, pady=5)

            self.refresh_btn = ttk.Button(
                self.control_frame, text="🔄 Refresh Peaks", command=self.refresh_data
            )
            self.refresh_btn.pack(side="left", padx=5)

            self.export_btn = ttk.Button(
                self.control_frame, text="💾 Export CSV", command=self.export_to_csv
            )
            self.export_btn.pack(side="left", padx=5)
            if not CSV_EXPORT_AVAILABLE:
                self.export_btn.config(state="disabled")

            # Data Table (Treeview)
            self.tree_frame = ttk.Frame(self)
            self.tree_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)

            # Scrollbars
            self.tree_scroll_y = ttk.Scrollbar(self.tree_frame, orient="vertical")
            self.tree_scroll_x = ttk.Scrollbar(self.tree_frame, orient="horizontal")

            # Define Columns
            self.columns = ("ID", "Frequency (MHz)", "Amplitude (dBm)", "Device")
            self.commands_table = ttk.Treeview(
                self.tree_frame,
                columns=self.columns,
                show="headings",
                yscrollcommand=self.tree_scroll_y.set,
                xscrollcommand=self.tree_scroll_x.set,
            )

            self.tree_scroll_y.config(command=self.commands_table.yview)
            self.tree_scroll_x.config(command=self.commands_table.xview)

            self.tree_scroll_y.pack(side="right", fill="y")
            self.tree_scroll_x.pack(side="bottom", fill="x")
            self.commands_table.pack(side="left", fill="both", expand=True)

            # Setup Headings
            for col in self.columns:
                self.commands_table.heading(
                    col, text=col, command=lambda c=col: self.sort_column(c, False)
                )
                self.commands_table.column(col, width=120, anchor="center")

            # Bind Double Click
            self.commands_table.bind("<Double-1>", self.on_item_double_click)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message="✅ MarkerPeakHunterGUI initialized successfully! It works!",
                    **_get_log_args(),
                )

        except Exception as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌🔴 Arrr, the code be capsized! The error be: {e}",
                    **_get_log_args(),
                )
            # Display error on GUI
            tk.Label(self, text=f"Initialization Error: {e}", fg="red").pack()

    def refresh_data(self):
        """
        Placeholder: logic to fetch peak data from State Mirror or File.
        """
        # TODO: Connect to actual data source
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🔄 Refreshing Peak Hunter Data... (Mock Data Loaded)",
                **_get_log_args(),
            )

        # Clear current
        for i in self.commands_table.get_children():
            self.commands_table.delete(i)

        # Mock Data
        mock_data = [
            (1, 101.5, -45.2, "Radio A"),
            (2, 433.92, -60.1, "Remote"),
            (3, 915.0, -55.8, "LoRa"),
            (4, 2400.5, -30.0, "WiFi"),
        ]

        for item in mock_data:
            self.commands_table.insert("", "end", values=item)

    def sort_column(self, col, reverse):
        """Sorts the Treeview column."""
        l = [
            (self.commands_table.set(k, col), k)
            for k in self.commands_table.get_children("")
        ]
        try:
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.commands_table.move(k, "", index)

        self.commands_table.heading(
            col, command=lambda: self.sort_column(col, not reverse)
        )

    def on_item_double_click(self, event):
        """Handle double click on a row."""
        item_id = self.commands_table.identify_row(event.y)
        if item_id:
            values = self.commands_table.item(item_id, "values")
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(message=f"🎯 Peak Selected: {values}", **_get_log_args())
            # Logic to tune radio to this frequency would go here

    def export_to_csv(self):
        """
        Opens a file dialog and exports the current data from the table to a CSV file.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        if not self.csv_export_util:
            return

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🖥️🔵 Preparing to export table data to CSV.", **_get_log_args()
            )

        try:
            file_path = filedialog.asksaveasfilename(
                initialdir=os.getcwd(),
                title="Save Table Data as CSV",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                defaultextension=".csv",
            )

            if file_path:
                data = []
                headers = self.columns
                for item_id in self.commands_table.get_children():
                    row_values = self.commands_table.item(item_id, "values")
                    row_dict = dict(zip(headers, row_values))
                    data.append(row_dict)

                self.csv_export_util.export_data_to_csv(data=data, file_path=file_path)

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"✅ Data exported successfully to {file_path}",
                        **_get_log_args(),
                    )

        except Exception as e:
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"❌🔴 Arrr, the code be capsized! The error be: {e}",
                    **_get_log_args(),
                )
