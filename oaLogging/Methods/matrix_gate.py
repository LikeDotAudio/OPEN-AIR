# oaLogging/Methods/matrix_gate.py
# Author: Anthony Peter Kuzub
# Version: 20260401.1955.1
#
# Description: Surgical logging gates for the Hierarchical Debug Matrix.
# Optimized with native Rust oalogginggate_rs for nanosecond checks.

import functools
from collections.abc import Callable

from loguru import logger

# --- Native Rust Optimization ---
try:
    from oaRustCore import oa_logging_gate_rs as oalogginggate_rs
    RUST_ENABLED = True
except ImportError:
    # ⚠️ Fallback to Python if Rust is not compiled (not recommended for production)
    RUST_ENABLED = False
    logger.warning("⚠️ [LOGGING] oalogginggate_rs not found in oaRustCore. Falling back to slow Python matrix checks.")
except Exception as e:
    RUST_ENABLED = False
    logger.error(f"❌ [LOGGING] Rust gate initialization failed: {e}")

def is_debug_allowed(system: str, element: str = None, func_name: str = None) -> bool:
    """
    Asks the LoggingMatrixManager (via Rust or Python) if a specific debug context is allowed to log.
    """
    if RUST_ENABLED:
        return oalogginggate_rs.is_debug_allowed(system, element, func_name)

    # --- Python Fallback Logic ---
    try:
        from oaConfigurationManager.Managers.LoggingManager.manager import LoggingMatrixManager
        manager = LoggingMatrixManager.get_instance()
        return manager.is_debug_allowed(system, element, func_name)
    except Exception:
        return False

def debug_matrix(system: str, element: str = None):
    """
    Decorator to gate an entire function's debug output via the matrix.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            if is_debug_allowed(system, element, func_name):
                return func(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def matrix_log(system: str, element: str = None, func_name: str = None,
               message: str = "", level: str = "DEBUG"):
    """
    Surgical entry point for the Hierarchical Debug Matrix.
    """
    gravity = level.upper()

    # 1. Master Logic: Check if the matrix allows this context
    allowed = is_debug_allowed(system, element, func_name)

    # 2. Gatekeeper: Allow if matrix permits, OR if it's a critical log (WARNING+)
    if allowed or gravity in ["WARNING", "ERROR", "CRITICAL"]:
        pass
    else:
        # INFO/SUCCESS/DEBUG/TRACE and not allowed
        return

    from oaLogging.Core.logger import get_logger

    # Determine the primary category/emoji for the logger
    if system.lower() == "comms" and element:
        # Special case for comms, use 📡 emoji and the element
        context_logger = get_logger(element, emoji_prefix="📡")
    elif system.lower() == "comms" and not element:
        # Fallback for comms without element
        context_logger = get_logger("COMMS", emoji_prefix="📡")
    else:
        # Use system as the category and get its emoji
        context_logger = get_logger(system)

    # Use .opt(depth=1) to ensure the caller's filename/line is preserved
    # Ensure category_name is available for consistency with direct logger calls
    bound_logger = context_logger.opt(depth=1)
    if element:
        bound_logger = bound_logger.bind(category_name=element.upper())
    else:
        bound_logger = bound_logger.bind(category_name=system.upper())

    log_func = getattr(bound_logger, level.lower(), bound_logger.debug)
    log_func(message)

# --- State Sync (Rust <-> Python) ---
def set_master_toggle(enabled: bool):
    """Updates the global master toggle in Rust."""
    if RUST_ENABLED:
        oalogginggate_rs.set_master_toggle(enabled)

def sync_gate_to_rust(system: str, element: str = None, enabled: bool = True):
    """Updates the Rust gate state."""
    if RUST_ENABLED:
        oalogginggate_rs.set_gate_state(system, element, enabled)
