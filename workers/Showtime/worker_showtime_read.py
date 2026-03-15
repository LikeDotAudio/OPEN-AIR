# Showtime/worker_showtime_read.py
#
# This module provides the logic for loading marker data from a file into the Showtime tab, preparing it for display and interaction.
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

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from workers.importers.worker_importer_loader import maker_file_check_for_markers_file


# Loads marker data from the 'MARKERS.csv' file into the Showtime tab instance.
# This function checks for the existence of `MARKERS.csv`, reads its content,
# and converts it into a list of dictionaries. This processed data is then
# stored in the `showtime_tab_instance` for further grouping, sorting, and display.
# Inputs:
#     showtime_tab_instance: An instance of the Showtime tab.
# Outputs:
#     None.
def load_marker_data(showtime_tab_instance):
    if LOCAL_DEBUG: logger.debug("🟢️️️🟢 Loading raw marker data from file.")

    raw_headers, raw_data = maker_file_check_for_markers_file()

    if not raw_data:
        showtime_tab_instance.marker_data = []
        showtime_tab_instance.column_headers = []
        if LOCAL_DEBUG: logger.debug("🟡 No marker data found in MARKERS.csv. No buttons will be created.")
        return

    showtime_tab_instance.marker_data = [
        dict(zip(raw_headers, row)) for row in raw_data if len(row) == len(raw_headers)
    ]
    showtime_tab_instance.column_headers = raw_headers

    if LOCAL_DEBUG: logger.success(f"✅ Loaded {len(showtime_tab_instance.marker_data)} rows. Converted to dictionaries for sorting and display.")
