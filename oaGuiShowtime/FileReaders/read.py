# FileReaders/read.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: Showtime/worker_showtime_read.py

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import os

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from oaFileImportShow.FileReaders.loader import maker_file_check_for_markers_file


# Loads marker data from the 'MARKERS.csv' file into the Showtime tab instance.
# This function checks for the existence of `MARKERS.csv`, reads its content,
# and converts it into a list of dictionaries. This processed data is then
# stored in the `showtime_tab_instance` for further grouping, sorting, and display.
# Inputs:
#     showtime_tab_instance: An instance of the Showtime tab.
# Outputs:
#     None.
def load_marker_data(showtime_tab_instance):
    matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "🟢️️️🟢 Loading raw marker data from file.", level="DEBUG")

    raw_headers, raw_data = maker_file_check_for_markers_file()

    if not raw_data:
        showtime_tab_instance.marker_data = []
        showtime_tab_instance.column_headers = []
        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "🟡 No marker data found in MARKERS.csv. No buttons will be created.", level="DEBUG")
        return

    showtime_tab_instance.marker_data = [
        dict(zip(raw_headers, row)) for row in raw_data if len(row) == len(raw_headers)
    ]
    showtime_tab_instance.column_headers = raw_headers

    matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, f"✅ Loaded {len(showtime_tab_instance.marker_data)} rows. Converted to dictionaries for sorting and display.", level="SUCCESS")
