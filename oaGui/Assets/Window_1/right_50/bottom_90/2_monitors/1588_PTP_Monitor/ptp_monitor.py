# /home/anthony/Documents/OPEN-AIR/oaGui/Assets/Window_1/right_50/bottom_90/2_monitors/1588_PTP_Monitor/ptp_monitor.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1200.1
#
# Description: Display wrapper for the PTP Monitor.
# The primary implementation logic resides in oaPTP.Interface.ptp_monitor.

from oaPTP.Interface.ptp_monitor import PtpMonitor as PtpMonitorImplementation

class PtpMonitor(PtpMonitorImplementation):
    """
    A local instance of the PTP Monitor.
    This class is discovered by LoaderFacade and instantiated.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

def get_gui_class():
    return PtpMonitor
