# markers/worker_marker_logic.py
#
# A utility module to contain core business logic functions related to marker data
# processing and calculation, ensuring separation of concerns (DOP 6.2).
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

import os
import inspect
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

# --- Graceful Dependency Importing ---
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

# --- Module Imports ---
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

# --- Global Scope Variables (as per Section 4.4) ---
current_version = "20251005.230247.1"
# The hash calculation drops the leading zero from the hour (23 -> 23)
current_version_hash = 20251005 * 230247 * 1
current_file = f"{os.path.basename(__file__)}"
LOCAL_DEBUG_ENABLE = False


# Calculates the minimum and maximum frequencies from a list of marker dictionaries.
# This function iterates through a list of marker data, extracts the 'FREQ_MHZ' value
# from each, and determines the overall minimum and maximum frequencies.
# Inputs:
#     marker_data_list (list): A list of dictionaries, where each dictionary represents a marker.
# Outputs:
#     tuple: A tuple containing (min_frequency, max_frequency) in MHz, or (None, None) if no valid frequencies are found or an error occurs.
def calculate_frequency_range(marker_data_list):
    # Calculates the minimum and maximum frequencies from a list of marker dictionaries.
    current_function_name = inspect.currentframe().f_code.co_name

    # [A brief, one-sentence description of the function's purpose.]
    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message=f"🟢️️️🟢 ➡️➡️ {current_function_name} to divine the full spectral range from {len(marker_data_list)} markers.",
            **_get_log_args(),
        )

    if not marker_data_list:
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🟢️️️🟡 The marker list is an empty void! Returning null range.",
                **_get_log_args(),
            )
        return None, None

    if not NUMPY_AVAILABLE:
        debug_logger(
            message="❌ Error: NumPy is required but not available. Cannot perform calculation."
        )
        return None, None

    try:
        freqs = []
        for marker in marker_data_list:
            try:
                # The canonical header for frequency is 'FREQ_MHZ'
                freqs.append(float(marker.get("FREQ_MHZ", 0)))
            except (ValueError, TypeError):
                continue

        if freqs:
            min_freq = np.min(freqs)
            max_freq = np.max(freqs)

            debug_logger(
                message=f"✅ Calculated range: {min_freq} MHz to {max_freq} MHz."
            )
            return min_freq, max_freq

        debug_logger(message="🟡 No valid frequencies found in marker data.")
        return None, None

    except Exception as e:
        debug_logger(message=f"❌ Error in {current_function_name}: {e}")
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"❌ Arrr, the code be capsized! Calculation failed: {e}",
                **_get_log_args(),
            )
        return None, None