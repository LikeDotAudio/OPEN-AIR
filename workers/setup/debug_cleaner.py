# setup/debug_cleaner.py
#
# This module provides a function to clear the debug directory of log files.
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
from workers.logger.logger import debug_logger  # import  debug_logger
from workers.logger.log_utils import _get_log_args  # Import _get_log_args


# Clears all files within the debug log directory.
# This function is used to remove old log files and ensure a clean slate for debugging
# purposes. It attempts to delete all files in the specified debug directory.
# Inputs:
#     data_dir (str): The base data directory where the 'debug' subdirectory is located.
# Outputs:
#     None.
def clear_debug_directory(data_dir):  # Removed _func argument
    debug_logger(message="▶️ Entering clear_debug_directory.", **_get_log_args())
    # Clear debug directory
    debug_dir = os.path.join(data_dir, "debug")
    if os.path.exists(debug_dir):
        debug_logger(
            message=f"🔍 Debug directory found: {debug_dir}. Proceeding to clear contents.",
            **_get_log_args(),
        )
        try:
            filenames = os.listdir(debug_dir)  # Get list of files before deletion
            debug_logger(
                message=f"🔍 Found {len(filenames)} items in debug directory.",
                **_get_log_args(),
            )
            for filename in filenames:
                file_path = os.path.join(debug_dir, filename)
                try:
                    debug_logger(
                        message=f"🗑️ Attempting to delete: {file_path}",
                        **_get_log_args(),
                    )
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        debug_logger(
                            message=f"🗑️ Successfully deleted: {file_path}",
                            **_get_log_args(),
                        )
                except Exception as e:
                    debug_logger(
                        message=f"❌ Failed to delete {file_path}. Reason: {e}",
                        **_get_log_args(),
                    )
            debug_logger(
                message="🧹 Finished clearing debug directory.", **_get_log_args()
            )
        except Exception as e:
            debug_logger(
                message=f"❌ Error listing or deleting files in {debug_dir}. Reason: {e}",
                **_get_log_args(),
            )

    else:
        debug_logger(
            message=f"⏩ Debug directory not found: {debug_dir}. Skipping clear.",
            **_get_log_args(),
        )