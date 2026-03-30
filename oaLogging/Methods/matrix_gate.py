# oaLogging/Methods/matrix_gate.py
# Author: Anthony Peter Kuzub
# Version: 20260329.2355.1
#
# Description: Surgical logging gates for the Hierarchical Debug Matrix.

import functools
from typing import Any, Callable
from loguru import logger

def is_debug_allowed(system: str, element: str = None, func_name: str = None) -> bool:
    """
    Asks the LoggingMatrixManager if a specific debug context is allowed to log.
    Fails safe (returns False) if the manager is unavailable.
    """
    try:
        from oaConfiguration.Managers.LoggingManager.manager import LoggingMatrixManager
        manager = LoggingMatrixManager.get_instance()
        return manager.is_debug_allowed(system, element, func_name)
    except Exception:
        # ⚡ FAIL-SAFE: If the matrix system is broken, we default to silent
        return False

def debug_matrix(system: str, element: str = None):
    """
    Decorator to gate an entire function's debug output via the matrix.
    Injects high-speed entry/exit logs if allowed.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            if is_debug_allowed(system, element, func_name):
                # Optionally log function entry with parameters
                # logger.opt(depth=1).debug(f"TRACE: Entering {func_name}")
                return func(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def matrix_log(system: str, element: str, func_name: str, message: str, level: str = "DEBUG"):
    """
    Explicitly logs a message only if the matrix allows it.
    """
    if is_debug_allowed(system, element, func_name):
        # Bind the specific context for this one-shot log
        from oaLogging.Core.logger import get_logger
        context_logger = get_logger(element.upper() if element else system.upper())
        # Use loguru level mapping
        log_func = getattr(context_logger.opt(depth=1), level.lower(), context_logger.debug)
        log_func(message)
