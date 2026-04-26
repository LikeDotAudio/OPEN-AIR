import inspect

# Methods/marker_logic.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: A utility module to contain core business logic functions related to marker data
import os

from oaLogging.Methods.matrix_gate import matrix_log

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

# --- Graceful Dependency Importing ---
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

# --- Global Scope Variables (as per Section 4.4) ---
current_version = "20251005.230247.1"
# The hash calculation drops the leading zero from the hour (23 -> 23)
current_version_hash = 20251005 * 230247 * 1
current_file = f"{os.path.basename(__file__)}"


# Calculates the minimum and maximum frequencies from a list of marker dictionaries.
# This function iterates through a list of marker data, extracts the 'FREQ_MHZ' value
# Inputs:
#     marker_data_list (list): A list of dictionaries, where each dictionary represents a marker.
# Outputs:
#     tuple: A tuple containing (min_frequency, max_frequency) in MHz, or (None, None) if no valid frequencies are found or an error occurs.
def calculate_frequency_range(marker_data_list):
    # Calculates the minimum and maximum frequencies from a list of marker dictionaries.
    current_function_name = inspect.currentframe().f_code.co_name

    # [A brief, one-sentence description of the function's purpose.]
    matrix_log("ui", "telemetry", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🟢️️️🟢 ➡️➡️ {current_function_name} to divine the full spectral range from {len(marker_data_list)} markers.", "DEBUG")

    if not marker_data_list:
        matrix_log("ui", "telemetry", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🟢️️️🟡 The marker list is an empty void! Returning null range.", "DEBUG")
        return None, None

    if not NUMPY_AVAILABLE:
        logger.error("❌ Error: NumPy is required but not available. Cannot perform calculation.")
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

            matrix_log("ui", "telemetry", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"✅ Calculated range: {min_freq} MHz to {max_freq} MHz.", "SUCCESS")
            return min_freq, max_freq

        matrix_log("ui", "telemetry", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🟡 No valid frequencies found in marker data.", "DEBUG")
        return None, None

    except Exception:
        if LOCAL_DEBUG:
            logger.exception("❌ Error in {current_function_name}")
        if LOCAL_DEBUG:
            logger.exception("❌ Arrr, the code be capsized! Calculation failed")
        return None, None
