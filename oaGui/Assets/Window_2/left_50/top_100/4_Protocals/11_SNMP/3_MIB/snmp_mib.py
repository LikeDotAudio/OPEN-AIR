# /home/anthony/Documents/OPEN-AIR/oaGui/Assets/Assets/right_50/bottom_90/11_SNMP/3_MIB/snmp_mib.py
# This file serves as a discovery point for the SNMP MIB GUI.
# The primary implementation logic resides in oaComProtocols.oaComSNMP.Interface.snmp_mib_impl.

# Version: 20260405.YYYY.R (date of refactor)
# Description: SNMP MIB GUI Pointer.

# Import the actual GUI implementation class from its new location
from oaComProtocols.oaComSNMP.Interface.snmp_mib_impl import SnmpMibImplementation


class SnmpMibGUI(SnmpMibImplementation):
    """
    A wrapper class pointing to the SNMP MIB GUI implementation.
    This class is discovered by LoaderFacade and instantiated.
    It inherits directly from the implementation to maintain full functionality.
    """
    # No additional logic is needed here as we inherit the full implementation.
    # The __init__ and other methods are provided by SnmpMibImplementation.
    pass

def get_gui_class():
    """
    Returns the GUI class for this module, which is the wrapper pointing
    to the actual implementation.
    This function is used by GUI discovery mechanisms.
    """
    return SnmpMibGUI
