# Showtime/worker_showtime_on_group_toggle.py
#
# This module provides the logic for handling group toggle events in the Showtime tab, updating selections and refreshing displayed devices.
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

from workers.Showtime.showtime_tune import on_tune_request_from_selection


# Handles the event when a group toggle button is clicked in the Showtime tab.
# This function updates the `selected_group` in the `showtime_tab_instance`.
# If the same group is clicked again, it deselects the group; otherwise, it selects the new group.
# It then refreshes the displayed group and device buttons and triggers a tune request.
# Inputs:
#     showtime_tab_instance: An instance of the Showtime tab.
#     group_name (str): The name of the group that was toggled.
# Outputs:
#     None.
def on_group_toggle(showtime_tab_instance, group_name):
    if LOCAL_DEBUG: logger.debug(f"🟢️️️🔵 Group toggle clicked for: {group_name}. Current selection: {showtime_tab_instance.selected_group}.")
    if showtime_tab_instance.selected_group == group_name:
        showtime_tab_instance.selected_group = None
        if LOCAL_DEBUG: logger.debug("🟢️️️🟡 Deselected Group. Showing all devices for the current Zone.")
    else:
        showtime_tab_instance.selected_group = group_name
        if LOCAL_DEBUG: logger.debug(f"🟢️️️🟢 Selected new Group: {showtime_tab_instance.selected_group}.")

    showtime_tab_instance._create_group_buttons()
    showtime_tab_instance._create_device_buttons()

    on_tune_request_from_selection(showtime_tab_instance)
