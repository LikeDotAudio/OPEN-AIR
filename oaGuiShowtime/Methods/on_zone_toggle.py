# Methods/on_zone_toggle.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: Showtime/worker_showtime_on_zone_toggle.py

import inspect

# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()  # Get the singleton instance

from oaGuiShowtime.Methods.tune import on_tune_request_from_selection


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
    matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, f"🟢️️️🔵 Zone toggle clicked for: {zone_name}. Current selection: {showtime_tab_instance.selected_zone}.", level="DEBUG")
    if showtime_tab_instance.selected_zone == zone_name:
        showtime_tab_instance.selected_zone = None
        showtime_tab_instance.selected_group = None
        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "🟢️️️🟡 Deselected Zone. Clearing Group selection.", level="DEBUG")
    else:
        showtime_tab_instance.selected_zone = zone_name
        showtime_tab_instance.selected_group = None
        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, f"🟢️️️🟢 Selected new Zone: {showtime_tab_instance.selected_zone}. Clearing Group selection.", level="DEBUG")

    showtime_tab_instance._create_zone_buttons()
    showtime_tab_instance._create_group_buttons()
    showtime_tab_instance._create_device_buttons()

    on_tune_request_from_selection(showtime_tab_instance)
