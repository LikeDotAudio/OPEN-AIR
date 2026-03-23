# oaLogging/Methods/error_handling.py
# Author: Gemini (Collaborator)
# Version: 20260323.1620.1
#
# Description: Vocal Error Handling Methods for OPEN-AIR.

"""
error_handling.py - Utilities for robust yet vocal error management.

Responsibilities:
    - Provides decorators to wrap risky code blocks with vocal logging.
    - Implements standardized "Red Screen of Warning" triggers for UI failures.
    - Ensures all exceptions are captured with full forensic detail (tracebacks).
"""

import functools
import traceback
from typing import Any, Callable, Optional, Type
from oaLogging.Core.logger import FAILURE_LOGGER, get_emoji

def vocal_failure_handler(
    message: str = "Critical Failure Detected",
    category: str = "SYSTEM",
    fallback: Any = None,
    re_raise: bool = False,
    widget: Any = None
):
    """
    Decorator for robust yet vocal error handling.

    Lead with action: Wraps a function in a try-except block that logs
    failures vocally and optionally displays them on a UI widget.

    Args:
        message (str): Contextual message to log on failure.
        category (str): Subsystem category for the log.
        fallback (Any): Value to return if the function fails (if re_raise is False).
        re_raise (bool): Whether to re-propagate the exception after logging.
        widget (Any): Optional Tkinter widget to display a 'Red Screen of Warning'.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 1. Capture forensic detail
                tb = traceback.format_exc()
                error_msg = f"❌🔴 [FAILURE] {message} in '{func.__name__}': {e}"
                
                # 2. Vocal Logging
                FAILURE_LOGGER.bind(category=f"{get_emoji('FAILURE')} {category}").error(
                    f"{error_msg}\n\n🕵️ FORENSIC TRACE:\n{tb}"
                )
                
                # 3. Visual 'Red Screen of Warning' (if widget provided)
                if widget and hasattr(widget, 'config') and widget.winfo_exists():
                    try:
                        widget.config(
                            text=f"❌ CRITICAL FAILURE\n\n{message}\n{e}",
                            foreground="red",
                            font=("Consolas", 10, "bold"),
                            justify="center"
                        )
                    except:
                        pass # Don't let the warning trigger itself fail
                
                if re_raise:
                    raise e
                return fallback
        return wrapper
    return decorator

def vocal_capture(category: str, message: str = "Error captured"):
    """
    Standardized function to vocally log an exception that has already been caught.
    
    Usage:
        try: ...
        except Exception as e:
            vocal_capture("MQTT", "Failed to connect to broker")
    """
    tb = traceback.format_exc()
    FAILURE_LOGGER.bind(category=f"{get_emoji('FAILURE')} {category}").error(
        f"❌🔴 [VOCAL CAPTURE] {message}\n\n🕵️ FORENSIC TRACE:\n{tb}"
    )
