# /home/anthony/Documents/OPEN-AIR/oaGui/Assets/Assets/right_50/bottom_90/2_monitors/1588_PTP_Monitor/__init__.py
# This __init__.py file acts as a pointer to the actual implementation of ptp_monitor.py
# located in the oaPTP module's Interface directory.

try:
    # Import the actual implementation from the new location
    from oaPTP.Interface.ptp_monitor import PtpMonitor as OriginalPtpMonitor
    from oaPTP.Interface.ptp_monitor import get_gui_class as original_get_gui_class

    # Re-export the class and function to maintain the original import path functionality
    class PtpMonitor(OriginalPtpMonitor):
        pass

    # Re-export the get_gui_class function
    def get_gui_class():
        return OriginalPtpMonitor # Return the actual class

except ImportError as e:
    print(f"Error importing PtpMonitor from oaPTP.Interface: {e}")
    print("Ensure oaPTP module and its Interface directory are correctly set up.")

    # Fallback or error handling if import fails
    class PtpMonitor:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("PtpMonitor could not be loaded. Please check module paths.")

    def get_gui_class():
        raise NotImplementedError("PtpMonitor could not be loaded.")
