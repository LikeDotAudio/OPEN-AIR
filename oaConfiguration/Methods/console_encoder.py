import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Methods/console_encoder.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

"""
console_encoder.py - Console Output Encoding Configuration for OPEN-AIR.

Purpose:
This module ensures that the standard output (stdout) and standard error 
(stderr) streams are configured to use UTF-8 encoding. This is particularly 
critical on Windows systems to prevent crashes or garbled output when 
displaying Unicode characters (e.g., emojis or specialized symbols).

Primary Responsibilities:
- Detect the operating system and reconfigure console streams if necessary.
- Provide a robust fallback for older Python versions that lack stream 
  reconfiguration capabilities.

Assumptions and Constraints:
- Assumes that UTF-8 is the desired encoding for all console output.
- Reconfiguration is primarily targeted at Windows ('nt') environments.
- Requires Python 3.7+ for 'sys.stdout.reconfigure'; fallbacks are used for 
  older versions.
"""

import os
import sys

LOCAL_DEBUG = True

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()


def configure_console_encoding(): 
    """
    Configures the console streams to handle UTF-8 encoding.

    Parameters:
        None

    Returns:
        None. Success is indicated by the successful reconfiguration of 
        streams or a graceful skip if not applicable/available.

    Side Effects and Thread-Safety:
        - Modifies the global 'sys.stdout' and 'sys.stderr' stream 
          configurations.
        - This function is not thread-safe if called while other threads are 
          actively writing to console streams.
    """
    # Windows ('nt') often defaults to legacy encodings (like cp1252), which 
    # fail when encountering UTF-8 symbols used throughout the app.
    if os.name == "nt":
        try:
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "▶️ Entering configure_console_encoding.", "DEBUG")

            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "⚙️ Attempting to reconfigure stdout encoding to UTF-8.", "DEBUG")

            # UTF-8 reconfiguration prevents 'UnicodeEncodeError' when logging 
            # stylized status indicators.
            sys.stdout.reconfigure(encoding="utf-8")
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅ Successfully reconfigured stdout encoding.", "SUCCESS")

            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "⚙️ Attempting to reconfigure stderr encoding to UTF-8.", "DEBUG")
            sys.stderr.reconfigure(encoding="utf-8")
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅ Successfully reconfigured stderr encoding.", "SUCCESS")
        except AttributeError:
            # Older Python versions (pre-3.7) do not support .reconfigure().
            matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🟡 sys.stdout/stderr.reconfigure not available. Skipping.", "DEBUG")
            pass
        except Exception as e:
            if LOCAL_DEBUG:
                matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"⚠️ Exception during console encoding reconfiguration: {e}", "DEBUG")

    else:
        # POSIX systems typically default to UTF-8, making reconfiguration 
        # unnecessary and potentially disruptive.
        matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "⏩ Not on Windows ('nt').", "DEBUG")

    matrix_log("core", "system", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "✅ Exiting configure_console_encoding.", "SUCCESS")
