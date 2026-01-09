# handlers/widget_event_binder.py
#
# This module provides utility functions for binding callbacks to Tkinter variables, enabling real-time event handling.
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
import tkinter as tk
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

current_version = "20251226.000000.1"


# Attaches a 'write' trace to a Tkinter variable.
# This function registers a callback to be invoked whenever the value of the
# provided Tkinter variable changes. This is typically used to trigger actions
# or updates in response to GUI element state modifications.
# Inputs:
#     tk_var (tk.Variable): The Tkinter variable to bind the trace to.
#     callback (function): The function to be called when the variable changes.
# Outputs:
#     None.
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