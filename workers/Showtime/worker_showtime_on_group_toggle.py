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
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance
from workers.Showtime.worker_showtime_tune import on_tune_request_from_selection


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
    current_function = inspect.currentframe().f_code.co_name
    if app_constants.global_settings["debug_enabled"]:  # Use app_constants
        debug_logger(
            message=f"🟢️️️🔵 Group toggle clicked for: {group_name}. Current selection: {showtime_tab_instance.selected_group}.",
            **_get_log_args(),
        )
    if showtime_tab_instance.selected_group == group_name:
        showtime_tab_instance.selected_group = None
        if app_constants.global_settings["debug_enabled"]:  # Use app_constants
            debug_logger(
                message="🟢️️️🟡 Deselected Group. Showing all devices for the current Zone.",
                **_get_log_args(),
            )
    else:
        showtime_tab_instance.selected_group = group_name
        if app_constants.global_settings["debug_enabled"]:  # Use app_constants
            debug_logger(
                message=f"🟢️️️🟢 Selected new Group: {showtime_tab_instance.selected_group}.",
                **_get_log_args(),
            )

    showtime_tab_instance._create_group_buttons()
    showtime_tab_instance._create_device_buttons()

    on_tune_request_from_selection(showtime_tab_instance)