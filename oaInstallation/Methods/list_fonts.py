# Methods/list_fonts.py
# Author: Anthony Peter Kuzub
# Version: 20260314.003500.REV01
#
# Description: Utility to enumerate and display all available system font families.

"""
Primary Purpose:
This script provides a diagnostic utility for users to identify valid font names
supported by their current operating system environment.
"""

import sys
import tkinter as tk
from tkinter import font

# --- Constants ---
VERSION = "20260314.003500.REV01"
EXIT_CODE_UI_ERROR = 1

def list_fonts():
    """
    Retrieves and prints a sorted list of all available system font families.
    """
    try:
        # A root object is required to access the font subsystem.
        root = tk.Tk()
        # Ensure no window is physically mapped to the screen.
        root.withdraw()

        # Capture and sort for readability in the terminal.
        system_fonts = list(font.families())
        system_fonts.sort()

        print("\n=== Available System Fonts ===")
        for font_family in system_fonts:
            print(font_family)

        print("\n=== End of Font List ===")
        print(f"Total fonts found: {len(system_fonts)}")
        print("\nYou can use any of these names in your config.ini file "
              "under [Fonts].")

    except Exception as e:
        # Gravity of Errors: Fail hard if the UI environment is broken.
        print(f"Error listing fonts: {e}")
        sys.exit(EXIT_CODE_UI_ERROR)

if __name__ == "__main__":
    list_fonts()
