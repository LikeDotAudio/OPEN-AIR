# Showtime/worker_showtime_on_marker_button_click.py
#
# This module provides the logic for handling clicks on marker (device) buttons in the Showtime tab, updating selections and triggering tune requests.
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


# Handles the event when a marker (device) button is clicked in the Showtime tab.
# This function manages the selection state of device buttons, updating their
# visual style to indicate selection/deselection, and triggers a tune request
# based on the currently selected device.
# Inputs:
#     showtime_tab_instance: An instance of the Showtime tab.
#     button: The button widget that was clicked, containing `marker_data`.
# Outputs:
#     None.
def on_marker_button_click(showtime_tab_instance, button):
    if LOCAL_DEBUG: logger.debug("🟢️️️🔵 Device button clicked. Toggling selection.")
    marker_data = button.marker_data

    if showtime_tab_instance.selected_device_button == button:
        showtime_tab_instance.selected_device_button.config(style="Custom.TButton")
        showtime_tab_instance.selected_device_button = None
        if LOCAL_DEBUG: logger.debug(f"🟡 Deselected device: {marker_data.get('NAME', 'N/A')}.")
    else:
        if showtime_tab_instance.selected_device_button:
            showtime_tab_instance.selected_device_button.config(style="Custom.TButton")

        showtime_tab_instance.selected_device_button = button
        showtime_tab_instance.selected_device_button.config(
            style="Custom.Selected.TButton"
        )
        if LOCAL_DEBUG: logger.success(f"✅ Selected device: {marker_data.get('NAME', 'N/A')} at {marker_data.get('FREQ_MHZ', 'N/A')} MHz.")

    on_tune_request_from_selection(showtime_tab_instance)
