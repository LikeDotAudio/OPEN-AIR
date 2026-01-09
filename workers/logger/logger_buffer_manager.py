# logger/logger_buffer_manager.py
#
# Manages the log message buffer for the application's logging system.
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
import time
from datetime import datetime

# Global buffer to hold messages before the log directory is set.
_log_buffer = []


# Adds a log message to the global buffer.
# This function is used to store log entries temporarily when the main logging
# system (e.g., file writer) is not yet fully initialized.
# Inputs:
#     timestamp (str): The timestamp of the log entry.
#     level (str): The log level (e.g., "INFO", "WARNING").
#     message (str): The log message itself.
#     context_data (dict): A dictionary containing additional context for the log.
# Outputs:
#     None.
def add_to_buffer(timestamp: str, level: str, message: str, context_data: dict):
    """Adds a log message to the buffer."""
    global _log_buffer
    _log_buffer.append((timestamp, level, message, context_data))


# Retrieves all buffered log messages and clears the buffer.
# This function is typically called once the main logging system is initialized,
# allowing all previously buffered messages to be processed.
# Inputs:
#     None.
# Outputs:
#     list: A list of buffered log entries, where each entry is a tuple.
def get_buffer_and_clear():
    """
    Retrieves the current buffer contents and then clears it.
    Returns:
        list: A list of buffered log entries.
    """
    global _log_buffer
    buffer_contents = _log_buffer
    _log_buffer = []
    return buffer_contents


# Checks if the log buffer is currently empty.
# Inputs:
#     None.
# Outputs:
#     bool: True if the buffer contains no messages, False otherwise.
def is_buffer_empty():
    """Checks if the log buffer is currently empty."""
    return not _log_buffer