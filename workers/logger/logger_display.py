# workers/logger/logger_display.py
# Handles displaying log messages to the console/terminal.

import os
import time
import inspect  # Needed for context

# Assume these helpers and state are accessible or will be passed.
# For now, defining placeholders that will be imported/managed by logger.py


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


def _clean_context_string(c_file: str, c_func: str) -> str:
    """Placeholder for cleaning context string for display."""
    # In a real scenario, this would be imported from logger.py
    if c_file == "?" and c_func == "?":
        return ""
    clean_file = str(c_file).replace(".py", "").replace("_", " ")
    clean_func = str(c_func).replace("_", " ") if c_func != "?" else ""
    combined = f"{clean_file}🪿 {clean_func}"
    return f"{combined} "


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


def display_console_message_on_terminal(message: str):
    """
    Formats and prints a console/user message to the terminal.
    """
    config_instance = _get_config_instance()
    if not config_instance.global_settings.get("debug_to_terminal", False):
        return  # Do not print if debug_to_terminal is False

    current_ts = f"{time.time():.6f}"
    print(f"{current_ts}🖥️{message}")
