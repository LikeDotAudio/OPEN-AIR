# Methods/on_zone_toggle.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: Showtime/worker_showtime_on_zone_toggle.py

import inspect
import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from oaGuiShowtime.Methods.tune import on_tune_request_from_selection


# Handles the event when a zone toggle button is clicked in the Showtime tab.
# This function updates the `selected_zone` in the `showtime_tab_instance`,
# managing the selection state and clearing group selections when a new zone is toggled.
# It then refreshes the displayed zone, group, and device buttons, and triggers a tune request.
# Inputs:
#     showtime_tab_instance: An instance of the Showtime tab.
#     zone_name (str): The name of the zone that was toggled.
# Outputs:
#     None.
def on_zone_toggle(showtime_tab_instance, zone_name):
    if LOCAL_DEBUG: logger.debug(f"🟢️️️🔵 Zone toggle clicked for: {zone_name}. Current selection: {showtime_tab_instance.selected_zone}.")
    if showtime_tab_instance.selected_zone == zone_name:
        showtime_tab_instance.selected_zone = None
        showtime_tab_instance.selected_group = None
        if LOCAL_DEBUG: logger.debug("🟢️️️🟡 Deselected Zone. Clearing Group selection.")
    else:
        showtime_tab_instance.selected_zone = zone_name
        showtime_tab_instance.selected_group = None
        if LOCAL_DEBUG: logger.debug(f"🟢️️️🟢 Selected new Zone: {showtime_tab_instance.selected_zone}. Clearing Group selection.")

    showtime_tab_instance._create_zone_buttons()
    showtime_tab_instance._create_group_buttons()
    showtime_tab_instance._create_device_buttons()

    on_tune_request_from_selection(showtime_tab_instance)
