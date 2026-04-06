# /home/anthony/Documents/OPEN-AIR/oaGuiDefinitions/Assets/right_50/bottom_90/11_SNMP/5_Verify_MIB/snmp_verify_mib.py
# This file serves as a discovery point for the SNMP Verify MIB GUI.
# The primary implementation logic resides in oaComSNMP.Interface.snmp_verify_mib_impl.

# Version: 20260405.YYYY.R (date of refactor)
# Description: SNMP Verify MIB GUI Pointer.

import tkinter as tk
# Import the actual GUI implementation class from its new location
from oaComSNMP.Interface.snmp_verify_mib_impl import SnmpVerifyWithMibImplementation

class SnmpVerifyWithMibGUI(SnmpVerifyWithMibImplementation):
    """
    A wrapper class pointing to the SNMP Verify MIB GUI implementation.
    This class is discovered by ModuleLoader and instantiated.
    It inherits directly from the implementation to maintain full functionality.
    """
    # No additional logic is needed here as we inherit the full implementation.
    # The __init__ and other methods are provided by SnmpVerifyWithMibImplementation.
    pass

def get_gui_class():
    """
    Returns the GUI class for this module, which is the wrapper pointing
    to the actual implementation.
    This function is used by GUI discovery mechanisms.
    """
    return SnmpVerifyWithMibGUI
