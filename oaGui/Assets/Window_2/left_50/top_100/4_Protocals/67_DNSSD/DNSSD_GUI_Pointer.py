# /home/anthony/Documents/OPEN-AIR/oaGui/Assets/right_50/bottom_90/4_Protocals/67_DNSSD/DNSSD_GUI_Pointer.py
# Author: Gemini (Collaborator)
# Version: 20260414.1600.1
# Description: DNSSD Monitor & Control Hub Pointer.

# Import the actual GUI implementation class from its new location
from oaComProtocols.oaComDNSSD.Interface.dashboard_gui import ProtocolDashboard


class DNSSDGUI(ProtocolDashboard):
    """
    A wrapper class pointing to the DNSSD GUI implementation.
    This class is discovered by ModuleLoader and instantiated.
    It inherits directly from the implementation to maintain full functionality.
    """
    # No additional logic is needed here as we inherit the full implementation.
    # The __init__ and other methods are provided by ProtocolDashboard.
    pass

def get_gui_class():
    """
    Returns the GUI class for this module, which is the wrapper pointing
    to the actual implementation.
    This function is used by GUI discovery mechanisms.
    """
    return DNSSDGUI
