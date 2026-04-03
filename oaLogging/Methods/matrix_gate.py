# oaLogging/Methods/matrix_gate.py
# Author: Anthony Peter Kuzub
# Version: 20260401.1955.1
#
# Description: Surgical logging gates for the Hierarchical Debug Matrix.
# Optimized with native Rust oalogginggate_rs for nanosecond checks.

import functools
from typing import Any, Callable
from loguru import logger

# --- Native Rust Optimization ---
from .oaLoggingGate_rs.compiler_hook import build
try:
    build()
    import oalogginggate_rs
    RUST_ENABLED = True
except ImportError:
    # ⚠️ Fallback to Python if Rust is not compiled (not recommended for production)
    RUST_ENABLED = False
    logger.warning("⚠️ [LOGGING] oalogginggate_rs not found. Falling back to slow Python matrix checks.")
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
        from oaConfiguration.Managers.LoggingManager.manager import LoggingMatrixManager
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

def matrix_log(system: str, element: str, func_name: str, message: str, level: str = "DEBUG"):
    """
    Explicitly logs a message only if the matrix allows it.
    """
    if is_debug_allowed(system, element, func_name):
        from oaLogging.Core.logger import get_logger
        context_logger = get_logger(element.upper() if element else system.upper())
        log_func = getattr(context_logger.opt(depth=1), level.lower(), context_logger.debug)
        log_func(message)

# --- State Sync (Rust <-> Python) ---
def sync_gate_to_rust(system: str, element: str = None, enabled: bool = True):
    """Updates the Rust gate state."""
    if RUST_ENABLED:
        oalogginggate_rs.set_gate_state(system, element, enabled)
