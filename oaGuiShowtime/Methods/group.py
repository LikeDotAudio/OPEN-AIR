# Methods/group.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: This module processes and groups marker data by Zone, Group, and Device for display in the Showtime tab.

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from collections import defaultdict
import os

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

def group_markers(raw_marker_data):
    """
    ⚡ DATA TRANSFORMATION: Organizes raw list into nested Zone/Group dictionary.
    Inputs:
        raw_marker_data (list): Raw list of marker dictionaries.
    Returns:
        defaultdict: Nested structure {zone: {group: [markers]}}
    """
    matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "🟢 [DATA] Grouping marker data by Zone and Group.", level="DEBUG")
    grouped = defaultdict(lambda: defaultdict(list))
    for row in raw_marker_data:
        zone = row.get("ZONE", "N/A")
        group = row.get("GROUP", "N/A")
        grouped[zone][group].append(row)
    return grouped

def sort_markers(grouped_markers):
    """
    ⚡ DATA ORDERING: Alphabetically sorts devices within each group.
    Inputs:
        grouped_markers (dict): The nested structure to sort.
    """
    matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "🔵 [DATA] Sorting markers by Device Name.", level="DEBUG")
    for zone, groups in grouped_markers.items():
        for group, devices in groups.items():
            devices.sort(key=lambda x: x.get("NAME", ""))

def process_and_sort_markers(showtime_tab_instance):
    """
    ⚡ ORCHESTRATOR: Coordinates the grouping and sorting pipeline.
    Refactored for Modular SRP.
    """
    matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "🟢️️️🔵 Starting marker processing pipeline.", level="INFO")

    # SRP REFACTOR: Step 1 - Grouping
    showtime_tab_instance.grouped_markers = group_markers(showtime_tab_instance.marker_data)

    # SRP REFACTOR: Step 2 - Sorting
    sort_markers(showtime_tab_instance.grouped_markers)

    matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "✅ Markers grouped and sorted successfully.", level="SUCCESS")
