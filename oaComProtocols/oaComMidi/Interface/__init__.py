# Interface/__init__.py
# Author: Anthony Peter Kuzub
# Version: 20260406.1955.1
#
# Description: MIDI Interface Package split into Input and Output.

from .Input.midi_dashboard import MidiDashboard
from .Input.midi_keyboard import MidiKeyboard, get_midi_color
from .Input.midi import get_gui_class as get_input_gui
from .Output.midi_output import MidiOutput
from .Output.midi_output import get_gui_class as get_output_gui
from .Output.midi_output_generator import MidiOutputGenerator

__all__ = [
    "MidiDashboard", 
    "MidiKeyboard", 
    "get_midi_color", 
    "get_input_gui", 
    "MidiOutput", 
    "get_output_gui", 
    "MidiOutputGenerator"
]
