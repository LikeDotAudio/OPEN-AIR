# Methods/clear_group_buttons.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: Showtime/worker_showtime_clear_group_buttons.py

import inspect
import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance


# Clears all dynamically generated group buttons from the Showtime tab's group frame.
# This function iterates through all child widgets of the `group_frame` and destroys them,
# effectively removing all previously created group buttons.
# Inputs:
#     showtime_tab_instance: An instance of the Showtime tab, which contains the `group_frame`.
# Outputs:
#     None.
def clear_group_buttons(showtime_tab_instance):
    if LOCAL_DEBUG: logger.debug("🟢️️️🔵 Clearing group buttons.")
    for widget in showtime_tab_instance.group_frame.winfo_children():
        widget.destroy()
