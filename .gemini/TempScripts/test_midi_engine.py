import sys
import os

# Ensure the project root is in sys.path
sys.path.append("/home/anthony/Documents/OPEN-AIR")

from oaComMidi.Methods.midi_engine import MidiEngine

def test_midi_engine():
    engine = MidiEngine()
    try:
        inputs = engine.list_inputs()
        outputs = engine.list_outputs()
        print(f"MIDI Inputs: {inputs}")
        print(f"MIDI Outputs: {outputs}")
        print("✅ SUCCESS: MIDI Engine initialized and listed ports.")
    except Exception as e:
        print(f"❌ FAILURE: MIDI Engine failed to list ports: {e}")

if __name__ == "__main__":
    test_midi_engine()
