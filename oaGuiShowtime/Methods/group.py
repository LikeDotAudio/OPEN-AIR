# Showtime/worker_showtime_group.py
#
# This module processes and groups marker data by Zone, Group, and Device for display in the Showtime tab.
# Refactored for Modular SRP: Separates Grouping logic from Sorting logic.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version 20250821.200641.1

import inspect
from collections import defaultdict
import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
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
    if LOCAL_DEBUG: logger.debug("🟢 [DATA] Grouping marker data by Zone and Group.")
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
    if LOCAL_DEBUG: logger.debug("🔵 [DATA] Sorting markers by Device Name.")
    for zone, groups in grouped_markers.items():
        for group, devices in groups.items():
            devices.sort(key=lambda x: x.get("NAME", ""))

def process_and_sort_markers(showtime_tab_instance):
    """
    ⚡ ORCHESTRATOR: Coordinates the grouping and sorting pipeline.
    Refactored for Modular SRP.
    """
    if LOCAL_DEBUG: logger.info("🟢️️️🔵 Starting marker processing pipeline.")

    # SRP REFACTOR: Step 1 - Grouping
    showtime_tab_instance.grouped_markers = group_markers(showtime_tab_instance.marker_data)

    # SRP REFACTOR: Step 2 - Sorting
    sort_markers(showtime_tab_instance.grouped_markers)

    if LOCAL_DEBUG: logger.success("✅ Markers grouped and sorted successfully.")
