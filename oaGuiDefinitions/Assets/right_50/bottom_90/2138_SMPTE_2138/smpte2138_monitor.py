# /home/anthony/Documents/OPEN-AIR/oaGuiDefinitions/Assets/right_50/bottom_90/2138_SMPTE_2138/smpte2138_monitor.py
# This file serves as a discovery point for the SMPTE2138 GUI.
# The primary implementation logic resides in oaComSMPTE2138.Interface.smpte2138_monitor.

# Version: 20260405.2005.1 (date of refactor)
# Description: SMPTE2138 Monitor GUI Pointer.

import tkinter as tk
# Import the actual GUI implementation class from its new location
from oaComSMPTE2138.Interface.smpte2138_monitor import SMPTE2138MonitorImplementation

class SMPTE2138MonitorGUI(SMPTE2138MonitorImplementation):
    """
    A wrapper class pointing to the SMPTE2138 Monitor GUI implementation.
    This class is discovered by ModuleLoader and instantiated.
    It inherits directly from the implementation to maintain full functionality.
    """
    # No additional logic is needed here as we inherit the full implementation.
    # The __init__ and other methods are provided by SMPTE2138MonitorImplementation.
    pass

def get_gui_class():
    """
    Returns the GUI class for this module, which is the wrapper pointing
    to the actual implementation.
    This function is used by GUI discovery mechanisms.
    """
    return SMPTE2138MonitorGUI
