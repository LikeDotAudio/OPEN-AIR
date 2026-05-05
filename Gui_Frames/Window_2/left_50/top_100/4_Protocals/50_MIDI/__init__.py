# /home/anthony/Documents/OPEN-AIR/oaGui/Assets/Assets/right_50/bottom_90/50_MIDI/__init__.py
# This __init__.py file acts as a pointer to the actual implementation of midi.py
# located in the oaComProtocols.oaComMidi module's Interface directory.

try:
    # Import the actual implementation from the new location
    from oaComProtocols.oaComMidi.Interface import MidiDashboard as OriginalMidiDashboard
    from oaComProtocols.oaComMidi.Interface import get_input_gui as original_get_gui_class

    # Re-export the class and function to maintain the original import path functionality
    class MidiMonitor(OriginalMidiDashboard):
        pass

    # Re-export the get_gui_class function
    def get_gui_class():
        return original_get_gui_class() # Return the actual class

except ImportError as e:
    print(f"Error importing MidiMonitor from oaComProtocols.oaComMidi.Interface: {e}")
    print("Ensure oaComProtocols.oaComMidi module and its Interface directory are correctly set up.")

    # Fallback or error handling if import fails
    class MidiMonitor:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("MidiMonitor could not be loaded. Please check module paths.")

    def get_gui_class():
        raise NotImplementedError("MidiMonitor could not be loaded.")
