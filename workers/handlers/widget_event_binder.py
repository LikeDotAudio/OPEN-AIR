# workers/handlers/widget_event_binder.py
#
# Purpose: Attaches the "Trace" or "Command" to the TKinter widgets during build time.
# Key Function: bind_variable_trace(tk_var, callback) -> When tk_var changes, call the callback.

import tkinter as tk
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

current_version = "20251226.000000.1"


def bind_variable_trace(tk_var: tk.Variable, callback):
    """
    Attaches a 'write' trace to a TKinter variable.
    When the variable's value changes, the callback is invoked.
    """
    try:
        # The callback will receive three arguments from the trace, which we ignore with a lambda.
        tk_var.trace_add("write", lambda *args: callback())
        debug_logger(message=f"Trace added for variable {tk_var}", **_get_log_args())
    except Exception as e:
        debug_logger(
            message=f"❌ Error binding trace to variable {tk_var}: {e}",
            **_get_log_args(),
        )
