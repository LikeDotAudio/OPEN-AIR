# /home/anthony/Documents/OPEN-AIR/oaGui/Assets/Assets/right_50/bottom_90/66_NMOS/00_Commands/nmos_commands.py
# This file serves as a discovery point for the NMOS Commands & Events GUI.
# The primary implementation logic resides in oaComProtocols.oaComNmos.Interface.nmos_commands_monitor_impl.

import tkinter as tk
# Import the actual GUI implementation class
from oaComProtocols.oaComNmos.Interface import NmosCommandsMonitorImplementation

class NmosCommandsGUI(NmosCommandsMonitorImplementation):
    """
    Wrapper class for the NMOS Commands GUI.
    """
    pass

def get_gui_class():
    """
    Returns the GUI class for this module.
    Used by GUI discovery mechanisms.
    """
    return NmosCommandsGUI
