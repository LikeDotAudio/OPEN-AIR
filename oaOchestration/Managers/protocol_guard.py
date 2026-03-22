# Managers/protocol_guard.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import functools
from oaLogging.Core.logger import router_logger

def protocol_guard(protocol_name):
    """
    Decorator to wrap protocol dispatch methods in a standardized try/except block.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Format a consistent error log for the protocol failure
                router_logger.error(f"{protocol_name}🚫🛑 [ERROR] Dispatch Failure: {e}")
                # We return None or False depending on the function's expected return on failure
                return None
        return wrapper
    return decorator
