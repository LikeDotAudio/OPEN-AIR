# Methods/on_marker_button_click.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: Showtime/worker_showtime_on_marker_button_click.py

import inspect
import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from oaGuiShowtime.Methods.tune import on_tune_request_from_selection


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
