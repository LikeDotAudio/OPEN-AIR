# /home/anthony/Documents/OPEN-AIR/oaGui/Assets/Assets/right_50/bottom_90/55_OSC/gui_OSC.py
# This file serves as a discovery point for the OSC GUI.
# The primary implementation logic resides in oaComProtocols.oaComOSC.Interface.gui_OSC.

# Version: 20260405.2007.1 (date of refactor)
# Description: OSC Monitor & Control Hub Pointer.

# Import the actual GUI implementation class from its new location
from oaComProtocols.oaComOSC.Interface.gui_OSC import OscDashboardImplementation


class OscDashboardGUI(OscDashboardImplementation):
    """
    A wrapper class pointing to the OSC GUI implementation.
    This class is discovered by LoaderFacade and instantiated.
    It inherits directly from the implementation to maintain full functionality.
    """
    # No additional logic is needed here as we inherit the full implementation.
    # The __init__ and other methods are provided by OscDashboardImplementation.
    pass

def get_gui_class():
    """
    Returns the GUI class for this module, which is the wrapper pointing
    to the actual implementation.
    This function is used by GUI discovery mechanisms.
    """
    return OscDashboardGUI
