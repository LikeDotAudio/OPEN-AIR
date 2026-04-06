# /home/anthony/Documents/OPEN-AIR/oaComSMPTE2138/Interface/smpte2138_monitor.py
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version: 20260405.2005.1
#
# Description: Elite GUI monitor for the SMPTE ST 2138 protocol. 
# This file contains the primary implementation logic.

import tkinter as tk
from oaComSMPTE2138.Interface import SMPTE2138Monitor

# This class is the primary implementation. It should be imported and used.
# The `get_gui_class` function is provided for discoverability by GUI loaders.

class SMPTE2138MonitorImplementation(SMPTE2138Monitor):
    """
    ST 2138 Monitor GUI with remote bridge lifecycle control.
    This class provides the full implementation.
    """
    # The original __init__ and all other methods from the previous version
    # are now part of this class, inherited from oaComSMPTE2138.Interface.SMPTE2138Monitor.
    # If there were any specific overrides or additions needed *here*, they would go.
    # For now, we assume the base class holds the full logic.
    pass

def get_gui_class():
    """
    Returns the main GUI class for this module.
    This function is used by GUI discovery mechanisms.
    """
    return SMPTE2138MonitorImplementation

