# oaComProtocols.oaComMidi/Methods/midi_engine.py
# Author: Anthony Peter Kuzub
# Version: 20260331.1730.2
#
# Description: Pure Rust MIDI Engine (No Python fallback).
from oaRustCore.oa_midi_engine_rs import MidiEngine as RustMidiEngine

LOCAL_DEBUG = False

class MidiEngine:
    """
    High-performance MIDI Engine using Rust midir backend.
    MANDATORY Rust implementation.
    """
    def __init__(self):
        if LOCAL_DEBUG:
            print("🎹🛠️🔗 [MIDI] Using PURE RUST engine.")
        self._engine = RustMidiEngine()

    def list_inputs(self):
        return self._engine.list_inputs()

    def list_outputs(self):
        return self._engine.list_outputs()

    def open_input(self, port_index: int):
        return self._engine.open_input(port_index)

    def get_events(self):
        """Polls for buffered MIDI events."""
        return self._engine.get_buffered_events()

    def close(self):
        self._engine.close()
