# logger/log_utils.py
#
# Utility to capture the context (File, Function, Version) of a log call.
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

# Removed: from managers.configini.config_reader import Config (This import caused the circular dependency)


# Inspects the call stack to retrieve contextual information for logging.
# This function dynamically captures the filename, function name, and
# 'current_version' from the caller's frame, providing valuable metadata for log entries.
# Inputs:
#     None.
# Outputs:
#     dict: A dictionary containing 'file', 'function', and 'version' of the caller,
#           or fallback values if information cannot be retrieved.
def _get_log_args():
    """
    Inspects the call stack to retrieve the filename, function name,
    and 'current_version' of the caller.
    This function should NOT access configuration directly to avoid circular imports.
    Configuration details that might be needed should be passed as arguments
    if absolutely necessary, or handled by the calling context.
    """
    # Removed: app_constants = Config.get_instance() (This call caused the infinite loop)

    try:
        frame = inspect.currentframe().f_back
        if frame:
            # Safely get filename, defaulting to '?' if not available
            filename = (
                os.path.basename(frame.f_code.co_filename)
                if frame.f_code.co_filename
                else "?"
            )
            # Safely get function name, defaulting to '?' if not available
            function_name = frame.f_code.co_name if frame.f_code.co_name else "?"
            # Safely get version from globals, defaulting if not available
            version = (
                frame.f_globals.get("current_version", "Unknown_Ver")
                if frame.f_globals
                else "Unknown_Ver"
            )

            return {"file": filename, "version": version, "function": function_name}
    except Exception as e:
        # In case of any error during frame inspection, return a safe error context.
        # Ideally, errors during logging setup should be handled robustly,
        # but for now, we'll return a fallback.
        return {
            "file": "unknown_file",
            "version": "unknown_ver",
            "function": "unknown_func",
            "error": str(e),
        }
    # Fallback return if no frame is found or other unexpected issue occurs
    return {"file": "unknown", "version": "unknown", "function": "unknown"}


# The 'debug_log' function present in the original log_utils.py also imported
# Config and used app_constants. To prevent further circular issues and
# simplify, this function and its dependencies are removed.
# If this function's logic is critical, it requires refactoring to accept
# configuration as an argument or be called in a context where config is available
# without causing a loop. For now, we assume it's not essential for the primary fix.