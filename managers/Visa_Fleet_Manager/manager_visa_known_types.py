# managers/Visa_Fleet_Manager/manager_visa_known_types.py
#
# Centralized knowledge base for known VISA instrument types and their notes.
#
# Author: Gemini Agent
#

# Maps Model Number -> {Type, Notes}
KNOWN_DEVICES = {
    "33220A": {"type": "Generator", "notes": "20 MHz Arbitrary Waveform"},
    "33210A": {"type": "Generator", "notes": "10 MHz Arbitrary Waveform"},
    "34401A": {"type": "DMM", "notes": "6.5 Digit Benchtop Standard"},
    "54641D": {"type": "Oscilloscope", "notes": "Mixed Signal (2 Ana + 16 Dig)"},
    "DS1104Z": {"type": "Oscilloscope", "notes": "100 MHz, 4 Channel Digital"},
    "66000A": {"type": "Power", "notes": "Modular System (8 Slots)"},
    "66101A": {"type": "Power", "notes": "8V / 16A (128W)"},
    "66102A": {"type": "Power", "notes": "20V / 7.5A (150W)"},
    "66103A": {"type": "Power", "notes": "35V / 4.5A (150W)"},
    "66104A": {"type": "Power", "notes": "60V / 2.5A (150W)"},
    "6060B": {"type": "Load", "notes": "DC Load (300 Watt)"},
    "3235": {"type": "Router", "notes": "High-perf Switching Matrix"},
    "3235A": {"type": "Router", "notes": "High-perf Switching Matrix"},
    "N9340B": {"type": "Spectrum", "notes": "Handheld (100 kHz - 3 GHz)"},
}
