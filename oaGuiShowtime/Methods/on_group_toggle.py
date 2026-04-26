# Methods/on_group_toggle.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: Showtime/worker_showtime_on_group_toggle.py

import inspect

# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()  # Get the singleton instance

from oaGuiShowtime.Methods.tune import on_tune_request_from_selection


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
    matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, f"🟢️️️🔵 Group toggle clicked for: {group_name}. Current selection: {showtime_tab_instance.selected_group}.", level="DEBUG")
    if showtime_tab_instance.selected_group == group_name:
        showtime_tab_instance.selected_group = None
        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "🟢️️️🟡 Deselected Group. Showing all devices for the current Zone.", level="DEBUG")
    else:
        showtime_tab_instance.selected_group = group_name
        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, f"🟢️️️🟢 Selected new Group: {showtime_tab_instance.selected_group}.", level="DEBUG")

    showtime_tab_instance._create_group_buttons()
    showtime_tab_instance._create_device_buttons()

    on_tune_request_from_selection(showtime_tab_instance)
