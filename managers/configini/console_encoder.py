# managers/configini/console_encoder.py

import os
import sys
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance
from workers.logger.logger import debug_logger  # import  debug_logger
from workers.logger.log_utils import _get_log_args  # Import _get_log_args


def configure_console_encoding():  # Removed _func and debug_log_func arguments
    # This block ensures the console can handle UTF-8 characters, preventing encoding errors.
    if os.name == "nt":
        try:
            debug_logger(
                message="▶️ Entering configure_console_encoding.", **_get_log_args()
            )

            debug_logger(
                message="⚙️ Attempting to reconfigure stdout encoding to UTF-8.",
                **_get_log_args(),
            )

            sys.stdout.reconfigure(encoding="utf-8")
            debug_logger(
                message="✅ Successfully reconfigured stdout encoding.",
                **_get_log_args(),
            )

            debug_logger(
                message="⚙️ Attempting to reconfigure stderr encoding to UTF-8.",
                **_get_log_args(),
            )
            sys.stderr.reconfigure(encoding="utf-8")
            debug_logger(
                message="✅ Successfully reconfigured stderr encoding.",
                **_get_log_args(),
            )
        except AttributeError:
            debug_logger(
                message="🟡 sys.stdout/stderr.reconfigure not available (likely older Python version). Skipping.",
                **_get_log_args(),
            )
            # Fallback for older Python versions that don't have reconfigure
            pass
        except Exception as e:
            debug_logger(
                message=f"⚠️ Exception during console encoding reconfiguration: {e}",
                **_get_log_args(),
            )
            # Log the exception but continue if possible

    else:
        debug_logger(
            message="⏩ Not on Windows ('nt'), skipping console encoding reconfiguration.",
            **_get_log_args(),
        )

    debug_logger(message="✅ Exiting configure_console_encoding.", **_get_log_args())
