# workers/Showtime/worker_showtime_tune.py
#
# A complete and comprehensive pre-amble that describes the file and the functions within.
# The purpose is to provide clear documentation and versioning.
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

import inspect
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

## from workers.active.worker_active_marker_tune_and_collect import Push_Marker_to_Center_Freq, Push_Marker_to_Start_Stop_Freq
from workers.markers.worker_marker_logic import calculate_frequency_range
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

LOCAL_DEBUG_ENABLE = False


def on_tune_request_from_selection(showtime_tab_instance):
    """
    Tunes the instrument based on the current selections.
    """
    current_function = inspect.currentframe().f_code.co_name
    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message="🟢️️️🟢 Initiating tuning request based on current selection.",
            **_get_log_args(),
        )

    if showtime_tab_instance.selected_device_button:
        # Case 1: A specific device is selected
        marker_data = showtime_tab_instance.selected_device_button.marker_data
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔍 Device button selected. Tuning to center frequency of {marker_data.get('NAME', 'N/A')}.",
                **_get_log_args(),
            )
        ## Push_Marker_to_Center_Freq(mqtt_controller=showtime_tab_instance.mqtt_util, marker_data=marker_data)
    elif showtime_tab_instance.selected_group:
        # Case 2: A group is selected, but no device
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔍 No device selected. Tuning to start/stop frequency of selected Group: {showtime_tab_instance.selected_group}.",
                **_get_log_args(),
            )
        group_devices = showtime_tab_instance.grouped_markers[
            showtime_tab_instance.selected_zone
        ][showtime_tab_instance.selected_group]
        # UPDATED: Use the imported utility function
        min_freq, max_freq = calculate_frequency_range(group_devices)

        if min_freq is not None and max_freq is not None:
            mock_marker_data = {"FREQ_MHZ": (min_freq + max_freq) / 2}
            ## Push_Marker_to_Start_Stop_Freq(mqtt_controller=showtime_tab_instance.mqtt_util, marker_data=mock_marker_data, buffer=(max_freq - min_freq) * 1e6)
        else:
            debug_logger(
                message="❌ Failed to tune: No valid frequencies found in selected group.",
                **_get_log_args(),
            )

    elif showtime_tab_instance.selected_zone:
        # Case 3: A zone is selected, but no group or device
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔍 No group selected. Tuning to start/stop frequency of selected Zone: {showtime_tab_instance.selected_zone}.",
                **_get_log_args(),
            )
        all_zone_devices = []
        for group_name in showtime_tab_instance.grouped_markers[
            showtime_tab_instance.selected_zone
        ]:
            all_zone_devices.extend(
                showtime_tab_instance.grouped_markers[
                    showtime_tab_instance.selected_zone
                ][group_name]
            )
        # UPDATED: Use the imported utility function
        min_freq, max_freq = calculate_frequency_range(all_zone_devices)

        if min_freq is not None and max_freq is not None:
            mock_marker_data = {"FREQ_MHZ": (min_freq + max_freq) / 2}
            ## Push_Marker_to_Start_Stop_Freq(mqtt_controller=showtime_tab_instance.mqtt_util, marker_data=mock_marker_data, buffer=(max_freq - min_freq) * 1e6)
        else:
            debug_logger(
                message="❌ Failed to tune: No valid frequencies found in selected zone.",
                **_get_log_args(),
            )
    else:
        # Case 4: No filters selected, tune to all markers
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🔍 No filters selected. Tuning to start/stop frequency of all markers.",
                **_get_log_args(),
            )
        # UPDATED: Use the imported utility function
        min_freq, max_freq = calculate_frequency_range(
            showtime_tab_instance.marker_data
        )

        if min_freq is not None and max_freq is not None:
            mock_marker_data = {"FREQ_MHZ": (min_freq + max_freq) / 2}
            ## Push_Marker_to_Start_Stop_Freq(mqtt_controller=showtime_tab_instance.mqtt_util, marker_data=mock_marker_data, buffer=(max_freq - min_freq) * 1e6)
        else:
            debug_logger(
                message="❌ Failed to tune: No valid frequencies found in marker data.",
                **_get_log_args(),
            )
