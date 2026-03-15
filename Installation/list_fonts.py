# Installation/list_fonts.py
#
# Utility to enumerate and display all available system font families.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your
# specific application can be negotiated. There is no charge to use, modify,
# or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260314.003500.REV01

"""
Primary Purpose:
This script provides a diagnostic utility for users to identify valid font names
supported by their current operating system environment. The output is intended
to be used when configuring the [Fonts] section of the application's
'config.ini' file.

Hard Constraints:
- Graphical Dependency: Requires 'tkinter' to be installed and accessible.
- Display Requirement: Assumes an active X11 or Wayland session (or equivalent)
  to initialize the Tkinter root object.
"""

import tkinter as tk
from tkinter import font
import sys

def list_fonts():
    """
    Retrieves and prints a sorted list of all available system font families.

    Lead with action: Initializes a transient Tkinter environment to query the
    underlying windowing system's font registry.

    Inputs:
        None.

    Outputs:
        None. Displays results via standard output. The process exits with 
        code 1 if the graphical environment cannot be initialized.

    Side Effects:
        - Instantiates and immediately withdraws a 'tk.Tk' root window.
        - Writes multiple lines to the standard output stream.
    
    Thread Safety:
        Not thread-safe. Must be executed on the main thread to satisfy 
        Tkinter's event loop requirements.
    """
    try:
        # A root object is required to access the font subsystem.
        root = tk.Tk()
        # Ensure no window is physically mapped to the screen.
        root.withdraw() 
        
        # Capture and sort for readability in the terminal.
        fonts = list(font.families())
        fonts.sort()
        
        print("\n=== Available System Fonts ===")
        for f in fonts:
            print(f)
            
        print("\n=== End of Font List ===")
        print(f"Total fonts found: {len(fonts)}")
        print("\nYou can use any of these names in your config.ini file "
              "under [Fonts].")
        
    except Exception as e:
        # Gravity of Errors: Fail hard if the UI environment is broken.
        print(f"Error listing fonts: {e}")
        sys.exit(1)

if __name__ == "__main__":
    list_fonts()
