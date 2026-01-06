# workers/logger/logger.py
# Main orchestrator for the logging system.
# Author: Anthony Peter Kuzub
# Description: Handles logging with a temporal buffer for pre-initialization messages.
# Version: 20251226.004000.8

import os
import time
import inspect
from datetime import datetime

# Import functions from the specialized modules
from workers.logger.logger_buffer_manager import (
    add_to_buffer,
    get_buffer_and_clear,
    is_buffer_empty,
)
from workers.logger.logger_writer import (
    write_log_to_file,
    write_log_to_error_file,
    set_log_directory_for_writer,
)
from workers.logger.logger_display import (
    display_debug_message_on_terminal,
    display_console_message_on_terminal,
)

# --- GLOBALS (Managed by this main logger module) ---
_log_directory = None
_config_instance_cache = None
_log_file_timestamp = None


def _get_config_instance():
    """
    Retrieves the global configuration instance.
    Uses a cache to avoid repeated lookups.
    Handles cases where the Config object might not be fully initialized yet.
    """
    global _config_instance_cache
    if _config_instance_cache is None:
        try:
            from managers.configini.config_reader import Config

            # If Config._instance is still None, it means Config is not yet fully initialized.
            # Use sensible defaults in this very early stage.
            if Config._instance is None:

                class DummyConfig:
                    PERFORMANCE_MODE = False

                    @property
                    def global_settings(self):
                        return {
                            "debug_to_terminal": True,
                            "debug_to_file": False,
                            "debug_enabled": False,
                        }  # Sensible defaults

                _config_instance_cache = DummyConfig()
            else:
                _config_instance_cache = Config._instance
        except ImportError:
            # Fallback if config_reader is not available at all
            class DummyConfig:
                PERFORMANCE_MODE = False

                @property
                def global_settings(self):
                    return {
                        "debug_to_terminal": True,
                        "debug_to_file": False,
                        "debug_enabled": False,
                    }

            _config_instance_cache = DummyConfig()

    # Ensure that if the real config has been initialized later, we return that.
    try:
        from managers.configini.config_reader import Config

        if Config._instance is not None:
            return Config._instance
    except ImportError:
        pass  # Config not available, return cached dummy if any.

    return _config_instance_cache


def _clean_context_string(c_file: str, c_func: str) -> str:
    """
    Helper to strip .py, remove underscores, and remove whitespace from file/function names.
    Input: "my_script.py", "my_func"
    Output: "myscript🪿 myfunc "
    """
    if c_file == "?" and c_func == "?":
        return ""

    # Clean file name: remove .py, replace _ with space
    clean_file = str(c_file).replace(".py", "").replace("_", " ")

    # Clean function name: replace _ with space
    clean_func = str(c_func).replace("_", " ") if c_func != "?" else ""

    # Combine with a separator and a trailing space for formatting
    combined = f"{clean_file}🪿 {clean_func}"
    return f"{combined} "


def set_log_directory(directory: str):
    """
    Sets the global log directory. This action also triggers flushing
    any buffered messages to their destinations (terminal, file, error log)
    based on current configuration.
    """
    global _log_directory, _log_file_timestamp
    _log_directory = directory
    if _log_file_timestamp is None:
        _log_file_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Delegate directory creation to the writer module.
    set_log_directory_for_writer(_log_directory)

    # 🧪 FLUSH THE BUFFER if there are any messages
    if not is_buffer_empty():
        buffered_messages = get_buffer_and_clear()
        # Log this action using the logger itself
        debug_logger(
            message=f"🧪  Flushing {len(buffered_messages)} buffered messages to the timeline!",
            **_get_log_args(),
        )

        config_instance = _get_config_instance()

        for timestamp, level, message, context_data in buffered_messages:
            is_error = "ERROR" in message or "❌" in message

            # 1. Display on terminal
            if config_instance.global_settings.get("debug_to_terminal", False):
                display_debug_message_on_terminal(
                    timestamp, level, message, context_data
                )

            # 2. Write to regular log file
            if config_instance.global_settings.get("debug_to_file", False):
                write_log_to_file(
                    timestamp, level, message, context_data, _log_file_timestamp
                )

            # 3. Write to error log file if it's an error
            if is_error and config_instance.global_settings.get("debug_to_file", False):
                write_log_to_error_file(timestamp, level, message, context_data)


def debug_logger(message: str, **kwargs):
    """
    Public interface for logging debug messages.
    Determines if messages should be buffered or processed immediately based on
    whether the log directory has been set. Delegates to specialized modules
    for display, file writing, and error logging.

    Args:
        message (str): The log message content.
        **kwargs: Optional keyword arguments, typically including caller context
                  (e.g., file, function, version) passed from _get_log_args().
    """
    config_instance = _get_config_instance()

    # SILENCE: If PERFORMANCE_MODE is enabled, completely stop debug logging.
    # if config_instance.PERFORMANCE_MODE:
    #    return

    # Generate timestamp immediately for consistency across handlers.
    current_ts = f"{time.time():.6f}"

    # Determine log level.
    is_error = "ERROR" in message or "❌" in message
    level = "❌" if is_error else "🦆"

    # Gather caller context (file, function, version) for detailed logging.
    # We inspect the frame *before* this function call.
    frame = inspect.currentframe().f_back
    caller_file = os.path.basename(frame.f_code.co_filename) if frame else "?"
    caller_func = frame.f_code.co_name if frame else "?"
    # Assuming 'current_version' might be a global in the main script context.
    caller_version = (
        frame.f_globals.get("current_version", "Unknown_Ver")
        if frame
        else "Unknown_Ver"
    )

    # Prepare context data, prioritizing explicit kwargs over derived caller info.
    context_data_for_log = {
        "file": kwargs.get("file", caller_file),
        "function": kwargs.get("function", caller_func),
        "version": kwargs.get("version", caller_version),
    }
    # Explicitly remove 'file', 'function', 'version' from kwargs before updating
    # to prevent potential multiple value errors if they were passed via **_get_log_args().
    filtered_kwargs = {
        k: v for k, v in kwargs.items() if k not in ["file", "function", "version"]
    }
    context_data_for_log.update(filtered_kwargs)

    # --- Routing Logic ---
    if _log_directory is None:
        # PHASE 1: Buffering. Log directory not set yet, so buffer messages.
        add_to_buffer(current_ts, level, message, context_data_for_log)
    else:
        # PHASE 2: Immediate Processing. Log directory is set. Process logs now.

        # 1. Display on terminal if enabled.
        if config_instance.global_settings.get("debug_to_terminal", False):
            display_debug_message_on_terminal(
                current_ts, level, message, context_data_for_log
            )

        # 2. Write to regular log file if enabled.
        if config_instance.global_settings.get("debug_to_file", False):
            write_log_to_file(
                current_ts, level, message, context_data_for_log, _log_file_timestamp
            )

        # 3. Write to error log file if it's an error and file logging is enabled.
        if is_error and config_instance.global_settings.get("debug_to_file", False):
            write_log_to_error_file(current_ts, level, message, context_data_for_log)


def console_log(message: str):
    """
    Public interface for logging general console/user messages.
    These messages are primarily intended for terminal display.
    """
    config_instance = _get_config_instance()

    # Console logs are typically only displayed on the terminal.
    if config_instance.global_settings.get("debug_to_terminal", False):
        display_console_message_on_terminal(message)

    # Note: Original implementation did not write console_log to files.
    # If file logging for console messages is desired, add logic here.


# --- Alias for compatibility ---
debug_log = debug_logger

# Helper function to get log arguments, assumed to be available from workers.utils.log_utils
# This is a common pattern for logging and helps pass context automatically.
# If workers.utils.log_utils is not available, this will need to be implemented here
# or passed manually in kwargs.
try:
    # Attempt to import the utility function for automatic context gathering
    from workers.logger.log_utils import _get_log_args
except ImportError:
    # Define a fallback if log_utils is not found or not importable
    def _get_log_args():
        # This fallback might not capture as much context as the real one.
        # It tries to mimic the original structure by inspecting the call stack.
        import inspect

        frame = inspect.currentframe().f_back
        if frame:
            return {
                "file": (
                    os.path.basename(frame.f_code.co_filename)
                    if frame.f_code.co_filename
                    else "?"
                ),
                "version": frame.f_globals.get("current_version", "Unknown_Ver"),
            }
        return {"file": "?", "version": "Unknown_Ver"}  # Default if no frame is found
