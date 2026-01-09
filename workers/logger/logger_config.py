# logger/logger_config.py
#
# This module provides a function to configure the application's logging system.
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

import pathlib
from workers.logger.logger import set_log_directory


# Configures the application's logger with a specified data directory.
# This function sets the log output directory and logs a debug message indicating
# that the logger has been configured.
# Inputs:
#     data_dir (str): The path to the data directory where log files will be stored.
#     _func (function): A function used for logging debug messages.
# Outputs:
#     None.
def configure_logger(data_dir, _func):
    # Configure the logger with the correct
    set_log_directory(pathlib.Path(data_dir) / "debug")
    _func("DEBUG: Logger configured via workers.logger.logger.set_log_directory.")