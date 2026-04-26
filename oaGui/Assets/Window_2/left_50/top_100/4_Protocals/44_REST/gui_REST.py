# /home/anthony/Documents/OPEN-AIR/oaGui/Assets/Assets/right_50/bottom_90/44_REST/gui_REST.py
# Author: Anthony Peter Kuzub
# Version: 20260405.2000.1
#
# Description: REST API Dashboard Wrapper.
# Logic has been moved to oaComProtocols.oaComREST.Interface.gui_REST.RestDashboard.

from oaComProtocols.oaComREST.Interface.gui_REST import RestDashboard


class RestMonitor(RestDashboard):
    """
    A local instance of the REST Dashboard plugin.
    This class is discovered by ModuleLoader and instantiated.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

def get_gui_class():
    return RestMonitor
