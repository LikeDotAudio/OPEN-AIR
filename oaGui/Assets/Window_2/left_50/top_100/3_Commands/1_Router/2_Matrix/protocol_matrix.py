# oaGui/Assets/Window_2/left_50/top_100/3_Commands/1_Router/2_Matrix/protocol_matrix.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Proxy frame for the ProtocolMatrix implementation.
# Delegates actual implementation to oaComBroker.Interface.

import tkinter as tk
from oaComBroker.Interface.protocol_matrix import ProtocolMatrix

class ProtocolMatrixProxy(ProtocolMatrix):
    """
    Asset-level proxy for the ProtocolMatrix.
    """
    pass

def get_gui_class():
    return ProtocolMatrixProxy
