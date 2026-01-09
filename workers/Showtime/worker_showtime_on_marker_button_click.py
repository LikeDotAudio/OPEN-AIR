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
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.Showtime.worker_showtime_tune import on_tune_request_from_selection


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
    current_function = inspect.currentframe().f_code.co_name
    if showtime_tab_instance.LOCAL_DEBUG_ENABLE:
        debug_logger(
            message="🟢️️️🔵 Device button clicked. Toggling selection.", **_get_log_args()
        )
    marker_data = button.marker_data

    if showtime_tab_instance.selected_device_button == button:
        showtime_tab_instance.selected_device_button.config(style="Custom.TButton")
        showtime_tab_instance.selected_device_button = None
        debug_logger(
            message=f"🟡 Deselected device: {marker_data.get('NAME', 'N/A')}.",
            **_get_log_args(),
        )
    else:
        if showtime_tab_instance.selected_device_button:
            showtime_tab_instance.selected_device_button.config(style="Custom.TButton")

        showtime_tab_instance.selected_device_button = button
        showtime_tab_instance.selected_device_button.config(
            style="Custom.Selected.TButton"
        )
        debug_logger(
            message=f"✅ Selected device: {marker_data.get('NAME', 'N/A')} at {marker_data.get('FREQ_MHZ', 'N/A')} MHz.",
            **_get_log_args(),
        )

    on_tune_request_from_selection(showtime_tab_instance)