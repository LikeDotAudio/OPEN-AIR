# /home/anthony/Documents/OPEN-AIR/oaGui/Assets/right_50/bottom_90/4_Protocals/99_EMBER/Ember.py
# This file serves as a discovery point for the Ember+ GUI.
# The primary implementation logic resides in oaComProtocols.oaComEmber.Interface.gui_EMBER.

# Version: 20260407.1105.1
# Description: Ember+ Monitor & Control Hub Pointer.

# Import the actual GUI implementation class from its new location
from oaComProtocols.oaComEmber.Interface.gui_EMBER import EmberDashboardImplementation


class EmberDashboardGUI(EmberDashboardImplementation):
    """
    A wrapper class pointing to the Ember+ GUI implementation.
    This class is discovered by LoaderFacade and instantiated.
    It inherits directly from the implementation to maintain full functionality.
    """
    # No additional logic is needed here as we inherit the full implementation.
    # The __init__ and other methods are provided by EmberDashboardImplementation.
    pass

def get_gui_class():
    """
    Returns the GUI class for this module, which is the wrapper pointing
    to the actual implementation.
    This function is used by GUI discovery mechanisms.
    """
    return EmberDashboardGUI
