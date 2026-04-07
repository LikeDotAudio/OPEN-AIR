# oaComProtocols.oaComMidi/Interface/Output/midi_output.py
#
# MIDI Output Generator Wrapper.
#
# Author: Anthony Peter Kuzub
# Version: 20260406.1955.1

import tkinter as tk
from .midi_output_generator import MidiOutputGenerator

class MidiOutput(MidiOutputGenerator):
    """
    A local instance of the MIDI Output Generator plugin.
    This class is discovered by ModuleLoader and instantiated.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

def get_gui_class():
    return MidiOutput
