# /home/anthony/Documents/OPEN-AIR/oaGuiDefinitions/Assets/right_50/bottom_90/2138_SMPTE_2138/__init__.py
# This __init__.py file acts as a pointer to the actual implementation of smpte2138_monitor.py
# located in the oaComSMPTE2138 module's Interface directory.

try:
    # Import the actual implementation from the new location
    from oaComSMPTE2138.Interface.smpte2138_monitor import SMPTE2138Monitor as OriginalSMPTE2138Monitor
    from oaComSMPTE2138.Interface.smpte2138_monitor import get_gui_class as original_get_gui_class

    # Re-export the class and function to maintain the original import path functionality
    class SMPTE2138Monitor(OriginalSMPTE2138Monitor):
        pass

    # Re-export the get_gui_class function
    def get_gui_class():
        return OriginalSMPTE2138Monitor # Return the actual class

except ImportError as e:
    print(f"Error importing SMPTE2138Monitor from oaComSMPTE2138.Interface: {e}")
    print("Ensure oaComSMPTE2138 module and its Interface directory are correctly set up.")
    
    # Fallback or error handling if import fails
    class SMPTE2138Monitor:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("SMPTE2138Monitor could not be loaded. Please check module paths.")
            
    def get_gui_class():
        raise NotImplementedError("SMPTE2138Monitor could not be loaded.")
