# 50_MIDI/midi.py
# Author: Anthony Peter Kuzub
# Version: 20260323.Refactored.3
#
# Description: MIDI Dashboard Wrapper. 
# Logic has been moved to oaComMidi/Interface/midi_dashboard.py.

import tkinter as tk
from oaComMidi.Interface import MidiDashboard

class MidiMonitor(MidiDashboard):
    """
    A local instance of the MIDI Dashboard plugin.
    This class is discovered by ModuleLoader and instantiated.
    """
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
