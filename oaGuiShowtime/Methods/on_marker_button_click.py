# Methods/on_marker_button_click.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: Showtime/worker_showtime_on_marker_button_click.py

import inspect

# --- Standard Debug Logging Setup ---
from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

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
    matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "🟢️️️🔵 Device button clicked. Toggling selection.", level="DEBUG")
    marker_data = button.marker_data

    if showtime_tab_instance.selected_device_button == button:
        showtime_tab_instance.selected_device_button.config(style="Custom.TButton")
        showtime_tab_instance.selected_device_button = None
        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, f"🟡 Deselected device: {marker_data.get('NAME', 'N/A')}.", level="DEBUG")
    else:
        if showtime_tab_instance.selected_device_button:
            showtime_tab_instance.selected_device_button.config(style="Custom.TButton")

        showtime_tab_instance.selected_device_button = button
        showtime_tab_instance.selected_device_button.config(
            style="Custom.Selected.TButton"
        )
        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, f"✅ Selected device: {marker_data.get('NAME', 'N/A')} at {marker_data.get('FREQ_MHZ', 'N/A')} MHz.", level="SUCCESS")

    on_tune_request_from_selection(showtime_tab_instance)
