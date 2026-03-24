# Methods/widget_event_binder.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: handlers/widget_event_binder.py

import tkinter as tk

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

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
        # ⚡ OPTIMIZATION: Disabled logging for trace addition as it spams thousands of lines during GUI build.
        #     logger.debug(f"Trace added for variable {tk_var}")
    except Exception as e:
        if LOCAL_DEBUG:
            logger.exception("❌ Error binding trace to variable {tk_var}")
