# oaGui/Assets/right_50/bottom_90/3_Commands/1_Router/2_Matrix/protocol_matrix.py
# Author: Anthony Peter Kuzub
# Version: 20260406.2005.1
#
# Description: Modular Protocol Router Interface Matrix.
# This file serves as a pointer to the ProtocolMatrix implementation 
# in the oaComBroker module.

try:
    from oaComBroker.Interface.protocol_matrix import ProtocolMatrix as OriginalProtocolMatrix
    
    class ProtocolMatrix(OriginalProtocolMatrix):
        """
        A local instance of the Protocol Router Interface Matrix.
        This class is discovered by ModuleLoader and instantiated.
        """
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)

    def get_gui_class():
        return ProtocolMatrix

except ImportError as e:
    import tkinter as tk
    class ProtocolMatrix(tk.Frame):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)
            tk.Label(self, text=f"Error loading ProtocolMatrix: {e}", fg="red").pack()
            
    def get_gui_class():
        return ProtocolMatrix
