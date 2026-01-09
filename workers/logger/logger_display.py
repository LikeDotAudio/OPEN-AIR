# logger/logger_display.py
#
# This module handles displaying formatted log messages to the console or terminal.
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
import inspect  # Needed for context

# Assume these helpers and state are accessible or will be passed.
# For now, defining placeholders that will be imported/managed by logger.py


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
#     str: A cleaned and formatted string suitable for terminal display.
def _clean_context_string(c_file: str, c_func: str) -> str:
    """Placeholder for cleaning context string for display."""
    # In a real scenario, this would be imported from logger.py
    if c_file == "?" and c_func == "?":
        return ""
    clean_file = str(c_file).replace(".py", "").replace("_", " ")
    clean_func = str(c_func).replace("_", " ") if c_func != "?" else ""
    combined = f"{clean_file}🪿 {clean_func}"
    return f"{combined} "


# Formats and prints a debug message to the terminal.
# This function constructs a human-readable log entry, including timestamp, level,
# message, and context data, and prints it to the standard output,
# provided that `debug_to_terminal` is enabled in the configuration.
# Inputs:
#     timestamp (str): The timestamp of the log entry.
#     level (str): The log level (e.g., "❌", "🦆").
#     message (str): The core log message.
#     context_data (dict): A dictionary containing 'file' and 'function' information.
# Outputs:
#     None.
def display_debug_message_on_terminal(
    timestamp: str, level: str, message: str, context_data: dict
):
    """
    Formats and prints a debug message to the terminal if debug_to_terminal is enabled.
    """
    config_instance = _get_config_instance()
    if not config_instance.global_settings.get("debug_to_terminal", False):
        return  # Do not print if debug_to_terminal is False

    clean_context = _clean_context_string(
        context_data.get("file", "?"), context_data.get("function", "?")
    )
    clean_level = level.strip()
    # Using the provided timestamp directly
    print(f"{timestamp} {message} {clean_level} {clean_context}")


# Formats and prints a console or user-facing message to the terminal.
# This function adds a timestamp and a console icon to the message before printing
# it to the standard output, provided that `debug_to_terminal` is enabled in the configuration.
# Inputs:
#     message (str): The console message to display.
# Outputs:
#     None.
def display_console_message_on_terminal(message: str):
    """
    Formats and prints a console/user message to the terminal.
    """
    config_instance = _get_config_instance()
    if not config_instance.global_settings.get("debug_to_terminal", False):
        return  # Do not print if debug_to_terminal is False

    current_ts = f"{time.time():.6f}"
    print(f"{current_ts}🖥️{message}")