# /home/anthony/Documents/OPEN-AIR/oaGui/Assets/Assets/right_50/bottom_90/55_OSC/__init__.py
# This __init__.py file acts as a pointer to the actual implementation of gui_OSC.py
# located in the oaComProtocols.oaComOSC module's Interface directory.

try:
    # Import the actual implementation from the new location
    from oaComProtocols.oaComOSC.Interface.gui_OSC import OscDashboard as OriginalOscDashboard
    from oaComProtocols.oaComOSC.Interface.gui_OSC import get_gui_class as original_get_gui_class

    # Re-export the class and function to maintain the original import path functionality
    class OscDashboard(OriginalOscDashboard):
        pass

    # Re-export the get_gui_class function
    def get_gui_class():
        return OriginalOscDashboard # Return the actual class

except ImportError as e:
    print(f"Error importing OscDashboard from oaComProtocols.oaComOSC.Interface: {e}")
    print("Ensure oaComProtocols.oaComOSC module and its Interface directory are correctly set up.")
    
    # Fallback or error handling if import fails
    class OscDashboard:
        def __init__(Slef, *args, **kwargs):
            raise NotImplementedError("OscDashboard could not be loaded. Please check module paths.")
            
    def get_gui_class():
        raise NotImplementedError("OscDashboard could not be loaded.")
