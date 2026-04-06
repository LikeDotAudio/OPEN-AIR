# /home/anthony/Documents/OPEN-AIR/oaGuiDefinitions/Assets/right_50/bottom_90/50_MIDI/midi.py
# This file contains the actual implementation of MidiMonitor.py.
# It is now located here for GUI discovery purposes, but the primary
# implementation logic resides in oaComMidi.Interface.midi.

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

def get_gui_class():
    return MidiMonitor
