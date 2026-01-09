# Showtime/worker_showtime_group.py
#
# This module processes and groups marker data by Zone, Group, and Device for display in the Showtime tab.
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
from collections import defaultdict
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance


# Processes and groups marker data by Zone, Group, and Device.
# This function iterates through the raw marker data, organizes it into a nested
# dictionary structure based on Zone and Group, and then sorts devices within each group
# by their Name.
# Inputs:
#     showtime_tab_instance: An instance of the Showtime tab, containing `marker_data`.
# Outputs:
#     None.
def process_and_sort_markers(showtime_tab_instance):
    current_function = inspect.currentframe().f_code.co_name
    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message="🟢️️️🔵 Processing and sorting marker data by Zone, Group, and Device.",
            **_get_log_args()
        )

    showtime_tab_instance.grouped_markers = defaultdict(lambda: defaultdict(list))

    for row in showtime_tab_instance.marker_data:
        zone = row.get("ZONE", "N/A")
        group = row.get("GROUP", "N/A")
        showtime_tab_instance.grouped_markers[zone][group].append(row)

    for zone, groups in showtime_tab_instance.grouped_markers.items():
        for group, devices in groups.items():
            devices.sort(key=lambda x: x.get("NAME", ""))

    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message="✅ Markers grouped and sorted successfully.", **_get_log_args()
        )