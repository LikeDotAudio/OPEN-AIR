# /home/anthony/Documents/OPEN-AIR/oaGuiDefinitions/Assets/right_50/bottom_90/44_REST/__init__.py
# This __init__.py file acts as a pointer to the actual implementation of gui_REST.py
# located in the oaComREST module's Interface directory.

try:
    # Import the actual implementation from the new location
    from oaComREST.Interface.gui_REST import RestDashboard as OriginalRestDashboard
    from oaComREST.Interface.gui_REST import get_gui_class as original_get_gui_class

    # Re-export the class and function to maintain the original import path functionality
    class RestDashboard(OriginalRestDashboard):
        pass

    # Re-export the get_gui_class function
    def get_gui_class():
        return OriginalRestDashboard # Return the actual class

except ImportError as e:
    print(f"Error importing RestDashboard from oaComREST.Interface: {e}")
    print("Ensure oaComREST module and its Interface directory are correctly set up.")
    
    # Fallback or error handling if import fails
    class RestDashboard:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("RestDashboard could not be loaded. Please check module paths.")
            
    def get_gui_class():
        raise NotImplementedError("RestDashboard could not be loaded.")
