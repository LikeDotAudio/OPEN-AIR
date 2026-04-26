# 70_AES70/AES70.py
# This file serves as a discovery point for the AES70 GUI.
# The primary implementation logic resides in oaComProtocols.oaComAES70.Interface.gui_AES70.

# Version: 20260407.1001.1
# Description: AES70 Monitor & Control Hub Pointer.

# Import the actual GUI implementation class from its new location
from oaComProtocols.oaComAES70.Interface.gui_AES70 import Aes70DashboardImplementation


class Aes70DashboardGUI(Aes70DashboardImplementation):
    """
    A wrapper class pointing to the AES70 GUI implementation.
    This class is discovered by ModuleLoader and instantiated.
    It inherits directly from the implementation to maintain full functionality.
    """
    # No additional logic is needed here as we inherit the full implementation.
    # The __init__ and other methods are provided by Aes70DashboardImplementation.
    pass

def get_gui_class():
    """
    Returns the GUI class for this module, which is the wrapper pointing
    to the actual implementation.
    This function is used by GUI discovery mechanisms.
    """
    return Aes70DashboardGUI
