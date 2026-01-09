# logger/logger_writer.py
#
# This module handles writing formatted log messages to files on disk, including a general log and a dedicated error log.
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
from datetime import datetime
import inspect  # Needed for context

# Assume these helpers and state are accessible or will be passed.
# For now, defining placeholders that will be imported/managed by logger.py
_log_directory = None


# Placeholder function to retrieve the global configuration instance.
# In a fully integrated system, this would typically import and return the
# `Config` singleton. For early initialization or isolated testing, it provides
# a dummy configuration with sensible defaults.
# Inputs:
#     None.
# Outputs:
#     Config: The global configuration instance or a dummy configuration.
def _get_config_instance():
    """Placeholder for getting the global config instance."""
    # In a real scenario, this would be imported from managers.configini.config_reader
    # and managed by the main logger.py
    from managers.configini.config_reader import Config

    if Config._instance is None:

        class DummyConfig:
            PERFORMANCE_MODE = False

            @property
            def global_settings(self):
                # Sensible defaults if config isn't ready
                return {
                    "debug_to_terminal": True,
                    "debug_to_file": False,
                    "debug_enabled": False,
                }

        return DummyConfig()
    return Config._instance


# Placeholder function for cleaning and formatting context strings for display.
# This function prepares file and function names for consistent logging output,
# replacing underscores and adding formatting.
# Inputs:
#     c_file (str): The raw file name from the log context.
#     c_func (str): The raw function name from the log context.
# Outputs:
#     str: A cleaned and formatted string suitable for file writing.
def _clean_context_string(c_file: str, c_func: str) -> str:
    """Placeholder for cleaning context string for display."""
    # In a real scenario, this would be imported from logger.py
    if c_file == "?" and c_func == "?":
        return ""
    clean_file = str(c_file).replace(".py", "").replace("_", " ")
    clean_func = str(c_func).replace("_", " ") if c_func != "?" else ""
    combined = f"{clean_file}🪿 {clean_func}"
    return f"{combined} "


# Sets the log output directory for the writer module and creates it if it doesn't exist.
# This function initializes the global log directory where all log files will be stored.
# Inputs:
#     directory (str): The path to the log directory.
# Outputs:
#     None.
def set_log_directory_for_writer(directory: str):
    """
    Sets the log directory for the writer module and creates it if it doesn't exist.
    """
    global _log_directory
    _log_directory = directory

    if not os.path.exists(_log_directory):
        try:
            os.makedirs(_log_directory)
            # Log creation to console if possible, as writer might not have buffer
            print(f"📁 Log directory created for writer: {_log_directory}")
        except OSError as e:
            print(f"❌ Error creating log directory for writer: {e}")


# Writes a general log message to a timestamped log file.
# This function formats a log entry, including timestamp, level, message, and context data,
# and appends it to a general log file. It filters out specific message types
# (e.g., Watchdog/Heartbeat messages) to keep the general log cleaner.
# Inputs:
#     timestamp (str): The timestamp of the log entry.
#     level (str): The log level.
#     message (str): The core log message.
#     context_data (dict): A dictionary containing additional context data.
#     log_file_timestamp (str): A timestamp used in the log file's name.
# Outputs:
#     None.
def write_log_to_file(
    timestamp: str,
    level: str,
    message: str,
    context_data: dict,
    log_file_timestamp: str,
):
    """
    Writes a general log message to a timestamped file.
    Filters out Watchdog/Heartbeat messages.
    """
    global _log_directory
    if not _log_directory:
        print("❌ Logger writer: Log directory not set. Cannot write to file.")
        return

    config_instance = _get_config_instance()
    if not config_instance.global_settings.get("debug_to_file", False):
        return  # Do not write to file if debug_to_file is False

    # Filter out specific messages from the file log
    if "Watchdog" in message or "System Heartbeat" in message:
        return

    try:
        # Filename format: 📍🐛YYYYMMDDHHMMSS.log
        log_filename = f"📍🐛{log_file_timestamp}.log"
        file_path = os.path.join(_log_directory, log_filename)

        c_file = context_data.get("file", "?")
        c_func = context_data.get("function", "?")
        clean_context = _clean_context_string(c_file, c_func)
        clean_level = level.strip()

        log_entry = f"{timestamp} {message} {clean_level} {clean_context}"

        # Append extra context data if available
        extras = {
            k: v for k, v in context_data.items() if k not in ["file", "function"]
        }
        if extras:
            log_entry += f" 🧩 {extras}"

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

    except Exception as e:
        # Fallback to console printing if file writing fails critically
        print(f"❌ Critical Failure writing to log file: {e}")


# Writes an error log message to a dedicated 'ERRORS.log' file.
# This function formats an error log entry, including timestamp, level, message,
# and context data, and appends it to a specific error log file,
# provided that file logging is enabled.
# Inputs:
#     timestamp (str): The timestamp of the log entry.
#     level (str): The log level (expected to be an error level).
#     message (str): The core error message.
#     context_data (dict): A dictionary containing additional context data.
# Outputs:
#     None.
def write_log_to_error_file(
    timestamp: str, level: str, message: str, context_data: dict
):
    """
    Writes an error log message to a dedicated ERRORS.log file.
    """
    global _log_directory
    if not _log_directory:
        print("❌ Logger writer: Log directory not set. Cannot write to error log.")
        return

    config_instance = _get_config_instance()
    if not config_instance.global_settings.get("debug_to_file", False):
        return  # Do not write to error log if debug_to_file is False

    try:
        error_log_filename = "ERRORS.log"
        file_path = os.path.join(_log_directory, error_log_filename)

        c_file = context_data.get("file", "?")
        c_func = context_data.get("function", "?")
        clean_context = _clean_context_string(c_file, c_func)
        clean_level = level.strip()

        log_entry = f"{timestamp}{message} {clean_level} {clean_context}"

        extras = {
            k: v for k, v in context_data.items() if k not in ["file", "function"]
        }
        if extras:
            log_entry += f" 🧩 {extras}"

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

    except Exception as e:
        # Fallback to console printing if error log writing fails critically
        print(f"❌ Critical Failure writing to error log: {e}")