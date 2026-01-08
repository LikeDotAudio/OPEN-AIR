# Visa_Fleet_Manager/manager_visa_known_types.py
#
# Centralized knowledge base for known VISA instrument types and their notes.
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
# Version 20250821.200641.1

# Maps Model Number -> {Type, Notes}
KNOWN_DEVICES = {
    # =========================================================================
    #  HP / AGILENT / KEYSIGHT (The Standard)
    # =========================================================================
    
# --- Digital Multimeters (DMM) ---
    "34401A": {"type": "DMM", "notes": "6.5 Digit Benchtop Standard (Legacy)"},
    "34410A": {"type": "DMM", "notes": "6.5 Digit High Performance"},
    "34411A": {"type": "DMM", "notes": "6.5 Digit Enhanced Performance"},
    "34420A": {"type": "DMM", "notes": "Nano-volt / Micro-ohm Meter"},
    "34450A": {"type": "DMM", "notes": "5.5 Digit Dual Display"},
    "34460A": {"type": "DMM", "notes": "6.5 Digit Truevolt (Basic)"},
    "34461A": {"type": "DMM", "notes": "6.5 Digit Truevolt (34401A Replacement)"},
    "34465A": {"type": "DMM", "notes": "6.5 Digit Performance Truevolt"},
    "34470A": {"type": "DMM", "notes": "7.5 Digit Truevolt"},
    "3458A":  {"type": "DMM", "notes": "8.5 Digit Industrial Standard"},
    "U1272A": {"type": "DMM", "notes": "Handheld 4.5 Digit, Water/Dust Resistant"},

    # --- Oscilloscopes ---
    "54622D": {"type": "Oscilloscope", "notes": "Mixed Signal (2+16 Chan, 100MHz)"},
    "54641D": {"type": "Oscilloscope", "notes": "Mixed Signal (2+16 Chan, 350MHz)"},
    "DS1104Z": {"type": "Oscilloscope", "notes": "100 MHz, 4 Channel (Rigol, often mixed in labs)"}, # Kept from your list
    "DSOX1102G": {"type": "Oscilloscope", "notes": "70/100 MHz 2 Ch + Gen (InfiniiVision 1000X)"},
    "DSOX2002A": {"type": "Oscilloscope", "notes": "70 MHz 2 Ch (InfiniiVision 2000X)"},
    "MSOX3014T": {"type": "Oscilloscope", "notes": "100 MHz 4+16 Ch Touch (InfiniiVision 3000T)"},
    "DSOX4024A": {"type": "Oscilloscope", "notes": "200 MHz 4 Ch (InfiniiVision 4000X)"},
    "DSOS054A": {"type": "Oscilloscope", "notes": "500 MHz 4 Ch (Infiniium S-Series)"},
    "DSOS104A": {"type": "Oscilloscope", "notes": "1 GHz 4 Ch (Infiniium S-Series)"},
    "DSO9064A": {"type": "Oscilloscope", "notes": "600 MHz 4 Ch (Infiniium 9000)"},
    "DSO9104A": {"type": "Oscilloscope", "notes": "1 GHz 4 Ch (Infiniium 9000)"},
    "Z204": {"type": "Oscilloscope", "notes": "Generic Z-Series Reference"},

    # --- Function / Waveform Generators ---
    "33120A": {"type": "Generator", "notes": "15 MHz Function/Arb (Classic)"},
    "33210A": {"type": "Generator", "notes": "10 MHz Function/Arb"},
    "33220A": {"type": "Generator", "notes": "20 MHz Function/Arb"},
    "33250A": {"type": "Generator", "notes": "80 MHz Function/Arb"},
    "33509B": {"type": "Generator", "notes": "20 MHz 1-Ch Trueform"},
    "33510B": {"type": "Generator", "notes": "20 MHz 2-Ch Trueform"},
    "33521B": {"type": "Generator", "notes": "30 MHz 1-Ch Trueform"},
    "33522B": {"type": "Generator", "notes": "30 MHz 2-Ch Trueform"},
    "33611A": {"type": "Generator", "notes": "80 MHz 1-Ch Trueform"},
    "33612A": {"type": "Generator", "notes": "80 MHz 2-Ch Trueform"},
    "33621A": {"type": "Generator", "notes": "120 MHz 1-Ch Trueform"},
    "33622A": {"type": "Generator", "notes": "120 MHz 2-Ch Trueform"},

    # --- Power Supplies (Bench & System) ---
    "E3610A": {"type": "Power", "notes": "30W Bench (8V/3A or 15V/2A)"},
    "E3615A": {"type": "Power", "notes": "60W Bench (20V/3A)"},
    "E3620A": {"type": "Power", "notes": "Dual Output 50W (25V/1A x2)"},
    "E3630A": {"type": "Power", "notes": "Triple Output 35W (6V, +20V, -20V)"},
    "E3631A": {"type": "Power", "notes": "Triple Output 80W Programmable"},
    "E3632A": {"type": "Power", "notes": "120W Programmable (15V/7A or 30V/4A)"},
    "E3633A": {"type": "Power", "notes": "200W Programmable (8V/20A or 20V/10A)"},
    "E3634A": {"type": "Power", "notes": "200W Programmable (25V/7A or 50V/4A)"},
    "E3640A": {"type": "Power", "notes": "30W Programmable (8V/3A or 20V/1.5A)"},
    "E3646A": {"type": "Power", "notes": "Dual 60W Programmable"},
    "E36300 Series": {"type": "Power", "notes": "Triple Output Low Noise (Modern E3631A)"},
    "N6700C": {"type": "Power", "notes": "Low-Profile Modular Mainframe (400W)"},
    "N6701C": {"type": "Power", "notes": "Low-Profile Modular Mainframe (600W)"},
    "N6702C": {"type": "Power", "notes": "Low-Profile Modular Mainframe (1200W)"},
    "66000A": {"type": "Power", "notes": "Modular System Mainframe (8 Slots)"},
    "66101A": {"type": "Power", "notes": "Module 8V / 16A (128W)"},
    "66102A": {"type": "Power", "notes": "Module 20V / 7.5A (150W)"},
    "66103A": {"type": "Power", "notes": "Module 35V / 4.5A (150W)"},
    "66104A": {"type": "Power", "notes": "Module 60V / 2.5A (150W)"},
    "6632B":  {"type": "Power", "notes": "100W System Supply (20V/5A)"},
    "6032A":  {"type": "Power", "notes": "1000W Autoranging (60V/50A)"},
    
    # --- Electronic Loads ---
    "6060B":  {"type": "Load", "notes": "DC Electronic Load (300W, 60V, 60A)"},
    "6063B":  {"type": "Load", "notes": "DC Electronic Load (250W, 240V, 10A)"},
    "N3300A": {"type": "Load", "notes": "Modular Load Mainframe (1800W)"},
    "EL30000": {"type": "Load", "notes": "Bench DC Electronic Load (Modern)"},

    # --- Spectrum & Signal Analyzers ---
    "8560A":  {"type": "Spectrum", "notes": "Portable 2.9 GHz (Legacy)"},
    "8560E":  {"type": "Spectrum", "notes": "Portable 2.9 GHz (Enhanced)"},
    "8561E":  {"type": "Spectrum", "notes": "Portable 6.5 GHz"},
    "8563E":  {"type": "Spectrum", "notes": "Portable 26.5 GHz"},
    "8566B":  {"type": "Spectrum", "notes": "High Perf 22 GHz (The 'Beast')"},
    "8590 Series": {"type": "Spectrum", "notes": "Low Cost Portable (Legacy)"},
    "E4401B": {"type": "Spectrum", "notes": "ESA-E Series 1.5 GHz"},
    "E4407B": {"type": "Spectrum", "notes": "ESA-E Series 26.5 GHz"},
    "N9000B": {"type": "Spectrum", "notes": "CXA Signal Analyzer"},
    "N9010B": {"type": "Spectrum", "notes": "EXA Signal Analyzer"},
    "N9020B": {"type": "Spectrum", "notes": "MXA Signal Analyzer"},
    "N9030B": {"type": "Spectrum", "notes": "PXA Signal Analyzer (High Performance)"},
    "N9040B": {"type": "Spectrum", "notes": "UXA Signal Analyzer (Ultra Performance)"},
    "N9340B": {"type": "Spectrum", "notes": "Handheld (100 kHz - 3 GHz)"},
    "N9912A": {"type": "Spectrum", "notes": "FieldFox RF Analyzer (4 GHz)"},
    "N9918A": {"type": "Spectrum", "notes": "FieldFox RF Analyzer (26.5 GHz)"},

    # --- Vector Network Analyzers (VNA) ---
    "8753E":  {"type": "VNA", "notes": "RF VNA 3/6 GHz (Classic)"},
    "8720ES": {"type": "VNA", "notes": "Microwave VNA 20 GHz"},
    "E5061B": {"type": "VNA", "notes": "ENA Series (Low Frequency/RF)"},
    "E5071C": {"type": "VNA", "notes": "ENA Series (RF 20 GHz)"},
    "E8361C": {"type": "VNA", "notes": "PNA Series (67 GHz)"},
    "N5221B": {"type": "VNA", "notes": "PNA Series (13.5 GHz)"},
    "N5222B": {"type": "VNA", "notes": "PNA Series (26.5 GHz)"},
    "N5245B": {"type": "VNA", "notes": "PNA-X Series (50 GHz, 2/4 Port)"},

    # --- Frequency Counters ---
    "53131A": {"type": "Counter", "notes": "Universal Counter (225 MHz, 10 digit/s)"},
    "53132A": {"type": "Counter", "notes": "Universal Counter (225 MHz, 12 digit/s)"},
    "53181A": {"type": "Counter", "notes": "RF Counter (225 MHz, 10 digit/s)"},
    "53220A": {"type": "Counter", "notes": "350 MHz Universal (Modern)"},
    "53230A": {"type": "Counter", "notes": "350 MHz Universal (High Precision)"},

    # --- Data Acquisition / Switching ---
    "34970A": {"type": "DAQ", "notes": "Data Acq / Switch Unit (Serial/GPIB)"},
    "34972A": {"type": "DAQ", "notes": "Data Acq / Switch Unit (USB/LAN)"},
    "DAQ970A": {"type": "DAQ", "notes": "Data Acq System (Next Gen)"},
    "34980A": {"type": "DAQ", "notes": "Multifunction Switch/Measure (8-slot)"},
    "3235":   {"type": "Router", "notes": "High-perf Switching Matrix"},
    "3235A":  {"type": "Router", "notes": "High-perf Switching Matrix"},

    # --- Source Measure Units (SMU) ---
    "B2901A": {"type": "SMU", "notes": "Precision SMU (1 Ch, 100fA)"},
    "B2902A": {"type": "SMU", "notes": "Precision SMU (2 Ch, 100fA)"},
    "B2912A": {"type": "SMU", "notes": "Precision SMU (2 Ch, 10fA)"},
    "E5270B": {"type": "SMU", "notes": "8-Slot Precision Measurement Mainframe"},

    # =========================================================================
    #  RIGOL (Budget / Education / Entry Lab)
    # =========================================================================

    # --- Oscilloscopes ---
    "DS1054Z": {"type": "Oscilloscope", "notes": "50 MHz 4 Ch (The 'Hobbyist Standard')"},
    "DS1104Z": {"type": "Oscilloscope", "notes": "100 MHz 4 Ch Digital"},
    "MSO5074": {"type": "Oscilloscope", "notes": "70 MHz 4 Ch Mixed Signal (Touch)"},
    "DS7014":  {"type": "Oscilloscope", "notes": "100 MHz 4 Ch Performance"},
    "DHO804":  {"type": "Oscilloscope", "notes": "70 MHz 4 Ch (12-bit High Res)"},
    
    # --- Function Generators ---
    "DG1022Z": {"type": "Generator", "notes": "25 MHz 2 Ch Arbitrary"},
    "DG4102":  {"type": "Generator", "notes": "100 MHz 2 Ch Arbitrary"},
    "DG812":   {"type": "Generator", "notes": "10 MHz 1 Ch (Basic)"},

    # --- Power Supplies ---
    "DP832":   {"type": "Power", "notes": "Triple Output (30V/3A x2, 5V/3A)"},
    "DP832A":  {"type": "Power", "notes": "Triple Output (High Accuracy Color)"},
    "DP711":   {"type": "Power", "notes": "Single Output 30V/5A"},

    # --- Spectrum Analyzers ---
    "DSA815-TG": {"type": "Spectrum", "notes": "1.5 GHz Analyzer + Tracking Gen"},
    "DSA832":    {"type": "Spectrum", "notes": "3.2 GHz Spectrum Analyzer"},
    
    # --- DMMs ---
    "DM3058":  {"type": "DMM", "notes": "5.5 Digit Benchtop"},
    "DM3068":  {"type": "DMM", "notes": "6.5 Digit Benchtop"},

    # =========================================================================
    #  TEKTRONIX / KEITHLEY (Industrial / Research)
    # =========================================================================

    # --- Oscilloscopes (Tek) ---
    "TDS2024C": {"type": "Oscilloscope", "notes": "200 MHz 4 Ch (Legacy Workhorse)"},
    "TBS1052B": {"type": "Oscilloscope", "notes": "50 MHz 2 Ch (Basic)"},
    "TBS2000B": {"type": "Oscilloscope", "notes": "Digital Storage Scope (Modern Basic)"},
    "MDO3014":  {"type": "Oscilloscope", "notes": "Mixed Domain (Scope + Spectrum)"},
    "MDO4000C": {"type": "Oscilloscope", "notes": "High Perf Mixed Domain"},
    "MSO54":    {"type": "Oscilloscope", "notes": "5 Series Mixed Signal (8 FlexCh)"},
    "MSO24":    {"type": "Oscilloscope", "notes": "2 Series Handheld/Bench (Battery)"},

    # --- DMMs / SMUs (Keithley) ---
    "2000":     {"type": "DMM", "notes": "6.5 Digit Multimeter (Legacy)"},
    "DMM6500":  {"type": "DMM", "notes": "6.5 Digit Touchscreen"},
    "2400":     {"type": "SMU", "notes": "SourceMeter (200V, 1A, 20W)"},
    "2450":     {"type": "SMU", "notes": "SourceMeter Touch (200V, 1A, 20W)"},
    "2602B":    {"type": "SMU", "notes": "System SourceMeter (Dual Channel)"},

    # --- Generators ---
    "AFG1022":  {"type": "Generator", "notes": "25 MHz 2 Ch Arbitrary"},
    "AFG3102":  {"type": "Generator", "notes": "100 MHz 2 Ch Dual (Classic)"},
    "AFG31000": {"type": "Generator", "notes": "Advanced High Perf Arb Gen"},

    # =========================================================================
    #  ROHDE & SCHWARZ (Precision RF / European)
    # =========================================================================

    # --- Oscilloscopes ---
    "HMO1002": {"type": "Oscilloscope", "notes": "Mixed Signal 50-100MHz (Legacy Hameg)"},
    "RTB2002": {"type": "Oscilloscope", "notes": "70-300 MHz 2 Ch (10-bit ADC)"},
    "RTB2004": {"type": "Oscilloscope", "notes": "70-300 MHz 4 Ch (10-bit ADC)"},
    "RTM3004": {"type": "Oscilloscope", "notes": "100-1000 MHz 4 Ch (10-bit ADC)"},
    "RTH1002": {"type": "Oscilloscope", "notes": "Scope Rider Handheld (Isolated)"},
    "MXO4":    {"type": "Oscilloscope", "notes": "Next Gen High Speed Scope"},

    # --- Spectrum Analyzers ---
    "FPC1000": {"type": "Spectrum", "notes": "Entry Spectrum Analyzer (1-3 GHz)"},
    "FPC1500": {"type": "Spectrum", "notes": "Spectrum Analyzer + Vector Network"},
    "FSH4":    {"type": "Spectrum", "notes": "Handheld Spectrum Analyzer"},
    "FSV3000": {"type": "Spectrum", "notes": "Signal and Spectrum Analyzer"},

    # --- Power Supplies ---
    "HMP2020": {"type": "Power", "notes": "Dual Output High Perf (188W)"},
    "HMP4040": {"type": "Power", "notes": "Quad Output High Perf (384W)"},
    "NGL200":  {"type": "Power", "notes": "Precision Power Supply (Linear)"},
    "NGM200":  {"type": "Power", "notes": "Precision Power Supply (High Speed)"},
}
