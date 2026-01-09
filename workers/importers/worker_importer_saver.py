# importers/worker_importer_saver.py
#
# This module provides functions for saving marker data to CSV files, including an intermediate file and a user-specified 'OpenAir.csv'.
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

from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
import inspect
import os
import csv
import pathlib
from tkinter import filedialog
from managers.configini.config_reader import Config
from workers.setup.worker_project_paths import GLOBAL_PROJECT_ROOT

app_constants = Config.get_instance()  # Get the singleton instance

# Define the canonical headers
CANONICAL_HEADERS = ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]


# Saves the current marker data to an intermediate CSV file named 'MARKERS.csv' in the project's DATA directory.
# This function writes the provided headers and data to a CSV file, ensuring consistency
# with canonical headers and handling any existing data.
# Inputs:
#     tree_headers (list): A list of strings representing the CSV header row.
#     tree_data (list): A list of dictionaries, where each dictionary represents a row of data.
# Outputs:
#     None.
def save_intermediate_file(tree_headers, tree_data):
    # Saves the current tree data to a file named 'MARKERS.csv' in the DATA directory at the project root level.
    current_function = inspect.currentframe().f_code.co_name

    # ANCHOR FIX: Use the stable GLOBAL_PROJECT_ROOT now available.
    target_path = GLOBAL_PROJECT_ROOT / "DATA" / "MARKERS.csv"

    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message=f"💾🟢 Saving data to intermediate file: {target_path}. Headers: {tree_headers}, first row: {tree_data[0] if tree_data else 'N/A'}",
            file=os.path.basename(__file__),
            version=current_version,
            function=f"{current_function}",
        )

    try:
        with open(target_path, "w", newline="") as csvfile:
            # Use DictWriter to ensure only rows that match the headers are written
            writer = csv.DictWriter(csvfile, fieldnames=CANONICAL_HEADERS)

            # Use CANONICAL_HEADERS to ensure consistent output file
            writer.writeheader()
            writer.writerows(tree_data)

        debug_logger(message=f"💾 Intermediate file saved as {target_path}")
    except Exception as e:
        debug_logger(message=f"❌ Failed to save intermediate MARKERS.csv file. {e}")


# Saves the current marker data to a user-specified CSV file, defaulting to 'OpenAir.csv'.
# This function prompts the user to select a save location and filename, then writes
# the provided headers and data to a CSV file.
# Inputs:
#     tree_headers (list): A list of strings representing the CSV header row.
#     tree_data (list): A list of dictionaries, where each dictionary represents a row of data.
# Outputs:
#     None.
def save_open_air_file(tree_headers, tree_data):
    # Saves the current tree data to a file named 'OpenAir.csv' in the DATA directory.
    current_function = inspect.currentframe().f_code.co_name

    if not tree_headers or not tree_data:
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🟢️️️🟡 'Save Open Air' action aborted: no data in treeview.",
                file=os.path.basename(__file__),
                version=current_version,
                function=f"{current_function}",
            )
        debug_logger(message="▶️ Action: Save Markers as Open Air.csv. No data to save.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        initialfile="OpenAir.csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    if not file_path:
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🟢️️️🟡 'Save Open Air' action cancelled by user.",
                file=os.path.basename(__file__),
                version=current_version,
                function=f"{current_function}",
            )
        return

    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message=f"🟢️️️🟢 'Save Open Air' button clicked. Saving to: {file_path}",
            file=os.path.basename(__file__),
            version=current_version,
            function=f"{current_function}",
        )
    debug_logger(
        message=f"▶️ Action: Saving Markers as Open Air.csv to {os.path.basename(file_path)}."
    )

    try:
        with open(file_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=tree_headers)
            writer.writeheader()
            writer.writerows(tree_data)

        debug_logger(message=f"✅ File saved successfully to {file_path}")
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="✅ File saved successfully.",
                file=os.path.basename(__file__),
                version=current_version,
                function=f"{current_function}",
            )
    except Exception as e:
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"❌ Error saving Open Air CSV file: {e}",
                file=os.path.basename(__file__),
                version=current_version,
                function=f"{current_function}",
            )
        debug_logger(message=f"❌ Failed to save file. {e}")


# Saves the marker data from the importer tab instance to the intermediate 'MARKERS.csv' file.
# This utility function acts as a wrapper to call `save_intermediate_file` using the
# `tree_headers` and `tree_data` attributes of the provided importer tab instance.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
# Outputs:
#     None.
def save_markers_file_internally(importer_tab_instance):
    save_intermediate_file(
        importer_tab_instance.tree_headers, importer_tab_instance.tree_data
    )