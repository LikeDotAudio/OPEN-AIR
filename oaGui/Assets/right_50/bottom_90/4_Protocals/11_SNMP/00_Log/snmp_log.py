# /home/anthony/Documents/OPEN-AIR/oaGui/Assets/Assets/right_50/bottom_90/11_SNMP/00_Log/snmp_log.py
# This file serves as a discovery point for the SNMP Log GUI.
# The primary implementation logic resides in oaComProtocols.oaComSNMP.Interface.snmp_log_impl.

# Version: 20260405.YYYY.R (date of refactor)
# Description: SNMP Log GUI Pointer.

import tkinter as tk
# Import the actual GUI implementation class from its new location
from oaComProtocols.oaComSNMP.Interface.snmp_log_impl import SnmpLogImplementation

class SnmpLogGUI(SnmpLogImplementation):
    """
    A wrapper class pointing to the SNMP Log GUI implementation.
    This class is discovered by ModuleLoader and instantiated.
    It inherits directly from the implementation to maintain full functionality.
    """
    # No additional logic is needed here as we inherit the full implementation.
    # The __init__ and other methods are provided by SnmpLogImplementation.
    pass

def get_gui_class():
    """
    Returns the GUI class for this module, which is the wrapper pointing
    to the actual implementation.
    This function is used by GUI discovery mechanisms.
    """
    return SnmpLogGUI
