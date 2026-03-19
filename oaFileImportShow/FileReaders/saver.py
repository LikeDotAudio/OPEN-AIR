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

import inspect
import os
import csv
from tkinter import filedialog

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from oaOchestration.Constants.project_paths import GLOBAL_PROJECT_ROOT

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
    from oaOchestration.Core.path_initializer import DATA_RUNNING_DIR
    target_path = DATA_RUNNING_DIR / "MARKERS.csv"

    logger.debug(f"💾 personal saving data to intermediate file: {target_path}. Headers: {tree_headers}, first row: {tree_data[0] if tree_data else 'N/A'}",
        file=os.path.basename(__file__),
        function=f"{current_function}",
    )

    try:
        with open(target_path, "w", newline="") as csvfile:
            # Use DictWriter to ensure only rows that match the headers are written
            writer = csv.DictWriter(csvfile, fieldnames=CANONICAL_HEADERS)

            # Use CANONICAL_HEADERS to ensure consistent output file
            writer.writeheader()
            writer.writerows(tree_data)

        if LOCAL_DEBUG: logger.debug(f"💾 Intermediate file saved as {target_path}")
    except Exception as e:
        if LOCAL_DEBUG:
            logger.exception("❌ Failed to save intermediate MARKERS.csv file. ")


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
        if LOCAL_DEBUG: logger.debug("🟢️️️🟡 'Save Open Air' action aborted: no data in treeview.", file=os.path.basename(__file__),
            function=f"{current_function}",
        )
        if LOCAL_DEBUG: logger.debug("▶️ Action: Save Markers as Open Air.csv. No data to save.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        initialfile="OpenAir.csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    if not file_path:
        if LOCAL_DEBUG: logger.debug("🟢️️️🟡 'Save Open Air' action cancelled by user.", file=os.path.basename(__file__),
            function=f"{current_function}",
        )
        return

    logger.debug(f"🟢️️️🟢 'Save Open Air' button clicked. Saving to: {file_path}",
        file=os.path.basename(__file__),
        function=f"{current_function}",
    )
    if LOCAL_DEBUG: logger.debug(f"▶️ Action: Saving Markers as Open Air.csv to {os.path.basename(file_path)}."
    )

    try:
        with open(file_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=tree_headers)
            writer.writeheader()
            writer.writerows(tree_data)

        if LOCAL_DEBUG: logger.success(f"✅ File saved successfully to {file_path}")
        if LOCAL_DEBUG: logger.success("✅ File saved successfully.", file=os.path.basename(__file__),
            function=f"{current_function}",
        )
    except Exception as e:
        if LOCAL_DEBUG:
            logger.exception("❌ Error saving Open Air CSV file",
                file=os.path.basename(__file__),
                function=f"{current_function}",
            )
            logger.exception("❌ Failed to save file. ")


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
