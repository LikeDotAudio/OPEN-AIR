# /home/anthony/Documents/OPEN-AIR/oaGuiDefinitions/Assets/right_50/bottom_90/66_NMOS/02_Connection/nmos_connection.py
# This file serves as a discovery point for the NMOS Connection Monitor GUI.
# The primary implementation logic resides in oaComNmos.Interface.nmos_connection_monitor_impl.

import tkinter as tk
# Import the actual GUI implementation class
from oaComNmos.Interface import NmosConnectionMonitorImplementation

class NmosConnectionGUI(NmosConnectionMonitorImplementation):
    """
    Wrapper class for the NMOS Connection Monitor GUI.
    """
    pass

def get_gui_class():
    """
    Returns the GUI class for this module.
    Used by GUI discovery mechanisms.
    """
    return NmosConnectionGUI
