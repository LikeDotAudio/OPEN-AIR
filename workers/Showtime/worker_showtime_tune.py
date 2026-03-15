# Showtime/worker_showtime_tune.py
#
# This module provides the logic for tuning an instrument based on marker selections (individual devices, groups, or zones) made in the Showtime tab.
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

from workers.markers.worker_marker_logic import calculate_frequency_range


# Tunes the instrument based on the current marker selections in the Showtime tab.
# This function determines the tuning action based on whether a specific device,
# a group, a zone, or no filter is selected. It calculates the appropriate
# frequency range and sends tuning commands to the instrument via MQTT.
# Inputs:
#     showtime_tab_instance: An instance of the Showtime tab, containing current selections and marker data.
# Outputs:
#     None.
def on_tune_request_from_selection(showtime_tab_instance):
    """
    Tunes the instrument based on the current selections.
    """
    if LOCAL_DEBUG: logger.debug("🟢️️️🟢 Initiating tuning request based on current selection.")

    if showtime_tab_instance.selected_device_button:
        # Case 1: A specific device is selected
        marker_data = showtime_tab_instance.selected_device_button.marker_data
        if LOCAL_DEBUG: logger.debug(f"🔍 Device button selected. Tuning to center frequency of {marker_data.get('NAME', 'N/A')}.")
        ## Push_Marker_to_Center_Freq(mqtt_controller=showtime_tab_instance.mqtt_util, marker_data=marker_data)
    elif showtime_tab_instance.selected_group:
        # Case 2: A group is selected, but no device
        if LOCAL_DEBUG: logger.debug(f"🔍 No device selected. Tuning to start/stop frequency of selected Group: {showtime_tab_instance.selected_group}.")
        group_devices = showtime_tab_instance.grouped_markers[
            showtime_tab_instance.selected_zone
        ][showtime_tab_instance.selected_group]
        # UPDATED: Use the imported utility function
        min_freq, max_freq = calculate_frequency_range(group_devices)

        if min_freq is not None and max_freq is not None:
            mock_marker_data = {"FREQ_MHZ": (min_freq + max_freq) / 2}
            ## Push_Marker_to_Start_Stop_Freq(mqtt_controller=showtime_tab_instance.mqtt_util, marker_data=mock_marker_data, buffer=(max_freq - min_freq) * 1e6)
        else:
            logger.error("❌ Failed to tune: No valid frequencies found in selected group.")

    elif showtime_tab_instance.selected_zone:
        # Case 3: A zone is selected, but no group or device
        if LOCAL_DEBUG: logger.debug(f"🔍 No group selected. Tuning to start/stop frequency of selected Zone: {showtime_tab_instance.selected_zone}.")
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
            logger.error("❌ Failed to tune: No valid frequencies found in selected zone.")
    else:
        # Case 4: No filters selected, tune to all markers
        if LOCAL_DEBUG: logger.debug("🔍 No filters selected. Tuning to start/stop frequency of all markers.")
        # UPDATED: Use the imported utility function
        min_freq, max_freq = calculate_frequency_range(
            showtime_tab_instance.marker_data
        )

        if min_freq is not None and max_freq is not None:
            mock_marker_data = {"FREQ_MHZ": (min_freq + max_freq) / 2}
            ## Push_Marker_to_Start_Stop_Freq(mqtt_controller=showtime_tab_instance.mqtt_util, marker_data=mock_marker_data, buffer=(max_freq - min_freq) * 1e6)
        else:
            logger.error("❌ Failed to tune: No valid frequencies found in marker data.")
