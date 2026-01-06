# workers/worker_project_paths.py
#
# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# As the current hour is 20, no change is needed.

Current_Date = 20251129  ##Update on the day the change was made
Current_Time = 120000  ## update at the time it was edited and compiled
Current_iteration = 1  ## a running version number - incriments by one each time

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = Current_Date * Current_Time * Current_iteration


# A utility module for defining all application file paths relative to the project root,
# ensuring consistent file access across all sub-modules.
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
#
# Version 20251013.212800.2

import os
import inspect
import pathlib
import sys


# --- Global Scope Variables (as per your instructions) ---
current_version = "20251013.212800.2"
# The hash calculation drops the leading zero from the hour (e.g., 083015 becomes 83015).
# The current time is 21:36:17
current_version_hash = 20251013 * 212800 * 2
current_file = f"{os.path.basename(__file__)}"

# --- Global Path Anchor ---
# In main.py, GLOBAL_PROJECT_ROOT is defined as the parent of the script being executed.
# Since this file is within the 'workers' directory, we must ascend one level up to the project root.
try:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running as a bundled executable
        GLOBAL_PROJECT_ROOT = pathlib.Path(sys.executable).parent
    else:
        # Running from source
        GLOBAL_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
except Exception as e:
    # Use a simple print or standard fallback in case of a critical error, but do NOT use debug_log here.
    print(f"❌ Critical Error establishing GLOBAL_PROJECT_ROOT in {current_file}: {e}")
    GLOBAL_PROJECT_ROOT = pathlib.Path(".")


# --- Core Project Paths (Relative to GLOBAL_PROJECT_ROOT) ---

# FIX: Correctly constructs path relative to the project root.
MARKERS_JSON_PATH = GLOBAL_PROJECT_ROOT / "DATA" / "MARKERS.json"
MARKERS_CSV_PATH = GLOBAL_PROJECT_ROOT / "DATA" / "MARKERS.csv"
DEVICE_STATE_SNAPSHOT_PATH = GLOBAL_PROJECT_ROOT / "DATA" / "device_state_snapshot.json"
YAKETY_YAK_REPO_PATH = GLOBAL_PROJECT_ROOT / "DATA" / "YAKETYYAK.json"
PRESET_REPO_PATH = GLOBAL_PROJECT_ROOT / "DATA" / "PRESET.csv"


def get_absolute_path(relative_path: str):
    """
    Utility function to return an absolute path for a string relative to the project root.
    """
    # [A brief, one-sentence description of the function's purpose.]
    current_function_name = inspect.currentframe().f_code.co_name

    # DELETED: debug_logger(message=f"🟢️️️🟢 Resolving path for: {relative_path}", ...)

    try:
        absolute_path = GLOBAL_PROJECT_ROOT / relative_path
        # DELETED: debug_logger(message=f"✅ Resolved Path: {absolute_path}")
        return absolute_path

    except Exception as e:
        # DELETED:  and debug_log calls for error handling
        print(f"❌ Error in {current_function_name}: {e}")
        return pathlib.Path(relative_path)  # Return a relative path as a fallback
