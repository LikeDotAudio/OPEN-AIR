# managers/Visa_Fleet_Manager/manager_visa_parse_idn.py
#
# Dedicated module for parsing the *IDN? string of VISA instruments.
#
# Author: Gemini Agent
#

import re  # Potentially needed for future IDN parsing, though not used in current simple version.


def parse_idn_string(idn_string):
    """
    Parses the standard *IDN? string into components.
    Expected format: MANUFACTURER,MODEL,SERIALNUMBER,FIRMWARE_VERSION
    Returns a dictionary with keys: manufacturer, model, serial_number, firmware.
    Returns None for any component if not found.
    """
    if not idn_string:
        return {
            "manufacturer": None,
            "model": None,
            "serial_number": None,
            "firmware": None,
        }

    parts = idn_string.strip().split(",")

    manufacturer = parts[0].strip() if len(parts) >= 1 and parts[0].strip() else None
    model = parts[1].strip() if len(parts) >= 2 and parts[1].strip() else None
    serial_number = parts[2].strip() if len(parts) >= 3 and parts[2].strip() else None
    firmware = parts[3].strip() if len(parts) >= 4 and parts[3].strip() else None

    # Basic cleanup for empty strings that might result from extra commas
    return {
        "manufacturer": manufacturer if manufacturer else None,
        "model": model if model else None,
        "serial_number": serial_number if serial_number else None,
        "firmware": firmware if firmware else None,
    }
