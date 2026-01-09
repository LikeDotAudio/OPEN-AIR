# setup/path_initializer.py
#
# This module initializes global project paths, including the project root and data directory, and adds them to the system path.
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
import sys
import pathlib
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance
from workers.logger.logger import debug_logger  # import  debug_logger
from workers.logger.log_utils import _get_log_args  # Import _get_log_args

GLOBAL_PROJECT_ROOT = None
DATA_DIR = None


# Initializes global project paths and adds the project root to `sys.path`.
# This function determines the absolute root path of the project and constructs
# the path to the DATA directory. It ensures that the project's root is in `sys.path`
# for proper module imports.
# Inputs:
#     None.
# Outputs:
#     tuple: A tuple containing (GLOBAL_PROJECT_ROOT, DATA_DIR) Path objects.
def initialize_paths():  # Removed _func argument
    global GLOBAL_PROJECT_ROOT, DATA_DIR

    # --- GLOBAL PATH ANCHOR (CRITICAL FIX: Ensure this runs first!) ---
    # This defines the absolute, true root path of the project, irrespective of the CWD.
    GLOBAL_PROJECT_ROOT = (
        pathlib.Path(__file__).resolve().parent.parent.parent
    )  # Adjust path for setup directory
    debug_logger(
        message=f"📁 GLOBAL_PROJECT_ROOT set to {GLOBAL_PROJECT_ROOT}",
        **_get_log_args(),
    )
    # Add the project's root directory to the system path to allow for imports from
    # all sub-folders (e.g., 'configuration' and 'display'). This is a robust way to handle imports.
    if str(GLOBAL_PROJECT_ROOT) not in sys.path:
        sys.path.append(str(GLOBAL_PROJECT_ROOT))
    debug_logger(
        message=f"⚙️ sys.path updated. Current sys.path: {sys.path}", **_get_log_args()
    )

    # --- Set DATA_DIR ---
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running as a bundled executable
        DATA_DIR = os.path.join(os.path.dirname(sys.executable), "DATA")
    else:
        DATA_DIR = os.path.join(GLOBAL_PROJECT_ROOT, "DATA")

    return GLOBAL_PROJECT_ROOT, DATA_DIR