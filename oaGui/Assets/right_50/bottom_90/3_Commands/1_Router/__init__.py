# /home/anthony/Documents/OPEN-AIR/oaGui/Assets/Assets/right_50/bottom_90/3_Command_Router/__init__.py
# This __init__.py file acts as a pointer to the actual implementation of command_router.py
# located in the oaComBroker module's Interface directory.

try:
    # Import the actual implementation from the new location
    from oaComBroker.Interface.command_router import CommandRouter as OriginalCommandRouter
    from oaComBroker.Interface.command_router import get_gui_class as original_get_gui_class

    # Re-export the class and function to maintain the original import path functionality
    class CommandRouter(OriginalCommandRouter):
        pass

    # Re-export the get_gui_class function
    def get_gui_class():
        return OriginalCommandRouter # Return the actual class

except ImportError as e:
    print(f"Error importing CommandRouter from oaComBroker.Interface: {e}")
    print("Ensure oaComBroker module and its Interface directory are correctly set up.")
    
    # Fallback or error handling if import fails
    class CommandRouter:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("CommandRouter could not be loaded. Please check module paths.")
            
    def get_gui_class():
        raise NotImplementedError("CommandRouter could not be loaded.")
