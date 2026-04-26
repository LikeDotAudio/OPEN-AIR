# Methods/tune.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: Showtime/worker_showtime_tune.py

import inspect

# --- Standard Debug Logging Setup ---
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()  # Get the singleton instance

from oaGuiTelemetry.Methods.marker_logic import calculate_frequency_range


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
    matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "🟢️️️🟢 Initiating tuning request based on current selection.", level="DEBUG")

    if showtime_tab_instance.selected_device_button:
        # Case 1: A specific device is selected
        marker_data = showtime_tab_instance.selected_device_button.marker_data
        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, f"🔍 Device button selected. Tuning to center frequency of {marker_data.get('NAME', 'N/A')}.", level="DEBUG")
        ## Push_Marker_to_Center_Freq(mqtt_controller=showtime_tab_instance.mqtt_util, marker_data=marker_data)
    elif showtime_tab_instance.selected_group:
        # Case 2: A group is selected, but no device
        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, f"🔍 No device selected. Tuning to start/stop frequency of selected Group: {showtime_tab_instance.selected_group}.", level="DEBUG")
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
        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, f"🔍 No group selected. Tuning to start/stop frequency of selected Zone: {showtime_tab_instance.selected_zone}.", level="DEBUG")
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
        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "🔍 No filters selected. Tuning to start/stop frequency of all markers.", level="DEBUG")
        # UPDATED: Use the imported utility function
        min_freq, max_freq = calculate_frequency_range(
            showtime_tab_instance.marker_data
        )

        if min_freq is not None and max_freq is not None:
            mock_marker_data = {"FREQ_MHZ": (min_freq + max_freq) / 2}
            ## Push_Marker_to_Start_Stop_Freq(mqtt_controller=showtime_tab_instance.mqtt_util, marker_data=mock_marker_data, buffer=(max_freq - min_freq) * 1e6)
        else:
            logger.error("❌ Failed to tune: No valid frequencies found in marker data.")
