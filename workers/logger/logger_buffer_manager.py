# workers/logger/logger_buffer_manager.py
# Manages the log message buffer.

import os
import time
from datetime import datetime

# Global buffer to hold messages before the log directory is set.
_log_buffer = []


def add_to_buffer(timestamp: str, level: str, message: str, context_data: dict):
    """Adds a log message to the buffer."""
    global _log_buffer
    _log_buffer.append((timestamp, level, message, context_data))


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


def is_buffer_empty():
    """Checks if the log buffer is currently empty."""
    return not _log_buffer
