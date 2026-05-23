# oaGui/Methods/entry/gui_starter.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Orchestrates the initialization and launch of the main Tkinter application.

import tkinter as tk

from oaGui.Managers.display.engine_gui_display import EngineGuiDisplay


def launch_main_gui_application():
    """
    Initializes and starts the main application GUI loop.
    Creates root window, instantiates display, and enters mainloop.
    """
    root = tk.Tk()
    root.title("OPEN-AIR GUI TESTER")
    root.geometry("1600x1000")

    app = EngineGuiDisplay(root, root=root)
    app.pack(fill="both", expand=True)

    root.mainloop()
