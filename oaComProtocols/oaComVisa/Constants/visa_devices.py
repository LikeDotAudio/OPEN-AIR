# Constants/visa_devices.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Standard knowledge base for VISA model identification.

KNOWN_DEVICES = {
    "33220A": {"type": "Function Generator", "notes": "20 MHz Arbitrary Waveform"},
    "33210A": {"type": "Function Generator", "notes": "10 MHz Arbitrary Waveform"},
    "34401A": {"type": "Multimeter (DMM)", "notes": "6.5 Digit Benchtop Standard"},
    "54641D": {"type": "Oscilloscope", "notes": "Mixed Signal (2 Ana + 16 Dig)"},
    "DS1104Z": {"type": "Oscilloscope", "notes": "100 MHz, 4 Channel Digital"},
    "66000A": {"type": "Power Mainframe", "notes": "Modular System (8 Slots)"},
    "66101A": {"type": "DC Power Module", "notes": "8V / 16A (128W)"},
    "66102A": {"type": "DC Power Module", "notes": "20V / 7.5A (150W)"},
    "66103A": {"type": "DC Power Module", "notes": "35V / 4.5A (150W)"},
    "66104A": {"type": "DC Power Module", "notes": "60V / 2.5A (150W)"},
    "6060B": {"type": "Electronic Load", "notes": "DC Load (300 Watt)"},
    "3235": {"type": "Switch Unit", "notes": "High-perf Switching Matrix"},
    "3235A": {"type": "Switch Unit", "notes": "High-perf Switching Matrix"},
    "N9340B": {"type": "Spectrum Analyzer", "notes": "Handheld (100 kHz - 3 GHz)"},
}
