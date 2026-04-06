# /home/anthony/Documents/OPEN-AIR/oaGuiDefinitions/Assets/right_50/bottom_90/66_NMOS/01_Websockets/nmos_websockets.py
# This file serves as a discovery point for the NMOS WebSocket Manager GUI.
# The primary implementation logic resides in oaComNmos.Interface.nmos_websocket_manager_impl.

import tkinter as tk
# Import the actual GUI implementation class
from oaComNmos.Interface import NmosWebsocketManagerImplementation

class NmosWebsocketsGUI(NmosWebsocketManagerImplementation):
    """
    Wrapper class for the NMOS WebSocket Manager GUI.
    """
    pass

def get_gui_class():
    """
    Returns the GUI class for this module.
    Used by GUI discovery mechanisms.
    """
    return NmosWebsocketsGUI
