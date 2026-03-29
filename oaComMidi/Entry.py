# oaComMidi/Entry.py
#
# The sole orchestrator and public gatekeeper for the MIDI Communication Module.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260328.1410.1

"""
oaComMidi/Entry.py - The sole orchestrator for the MIDI Communication Module.
"""

from .Managers.midi_manager import MidiManager
from .Core.midi_port_controller import MIDIPortController
from .Core.midi_hardware_lock import MIDIHardwareLock
from .Core.midi_protocol_mapper import MIDIProtocolMapper
from .Interface.midi_dashboard import MidiDashboard

_instance = None

def get_manager(state_cache_manager=None, run_bridge=True):
    global _instance
    if _instance is None:
        _instance = MidiManager(
            state_cache_manager=state_cache_manager, 
            run_bridge=run_bridge
        )
    return _instance

def start():
    manager = get_manager()
    manager.start()

def stop():
    manager = get_manager()
    manager.stop()

def status():
    manager = get_manager()
    return manager.get_port_info()

__all__ = [
    "MidiManager",
    "MIDIPortController",
    "MIDIHardwareLock",
    "MIDIProtocolMapper",
    "MidiDashboard",
    "get_manager",
    "start",
    "stop",
    "status"
]
