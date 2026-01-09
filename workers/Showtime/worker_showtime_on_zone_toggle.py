# Showtime/worker_showtime_on_zone_toggle.py
#
# This module provides the logic for handling zone toggle events in the Showtime tab, updating selections and refreshing displayed groups/devices.
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
    current_function = inspect.currentframe().f_code.co_name
    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message=f"🟢️️️🔵 Zone toggle clicked for: {zone_name}. Current selection: {showtime_tab_instance.selected_zone}.",
            **_get_log_args(),
        )
    if showtime_tab_instance.selected_zone == zone_name:
        showtime_tab_instance.selected_zone = None
        showtime_tab_instance.selected_group = None
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🟢️️️🟡 Deselected Zone. Clearing Group selection.",
                **_get_log_args(),
            )
    else:
        showtime_tab_instance.selected_zone = zone_name
        showtime_tab_instance.selected_group = None
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🟢️️️🟢 Selected new Zone: {showtime_tab_instance.selected_zone}. Clearing Group selection.",
                **_get_log_args(),
            )

    showtime_tab_instance._create_zone_buttons()
    showtime_tab_instance._create_group_buttons()
    showtime_tab_instance._create_device_buttons()

    on_tune_request_from_selection(showtime_tab_instance)