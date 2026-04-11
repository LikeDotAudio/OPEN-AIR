# oaGui/Entry.py
# Author: Gemini (Collaborator)
# Version: 20260405.2215.1
#
# Description: Gatekeeper for the consolidated GUI Framework.
# Combines structural assembly, directory scanning, and layout parsing.

import sys
from pathlib import Path
from .Managers.gui_display import Application
from .Managers.gui_batch import GuiBatchBuilderMixin
from .Managers.gui_mqtt import GuiMqttManagerMixin
from .Core.layout_parser import LayoutParser
from .Core.directory import DirectoryBuilderMixin

__all__ = [
    "Application",
    "GuiBatchBuilderMixin",
    "GuiMqttManagerMixin",
    "LayoutParser",
    "DirectoryBuilderMixin"
]

def run_tests():
    """
    Standard test runner for the module.
    """
    import unittest
    import pathlib
    
    print(f"🔍 Discovering and running tests for oaGui...")
    test_dir = pathlib.Path(__file__).parent.parent / "Tests"
    if not test_dir.is_dir():
        print("❌ No 'Tests/' directory found.")
        return

    loader = unittest.TestLoader()
    suite = loader.discover(str(test_dir), pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

def start_gui():
    """Starts the main application GUI."""
    import tkinter as tk
    root = tk.Tk()
    root.title("OPEN-AIR GUI TESTER")
    root.geometry("1600x1000")
    
    app = Application(root, root=root)
    app.pack(fill="both", expand=True)
    
    root.mainloop()

if __name__ == "__main__":
    if "gui" in sys.argv:
        start_gui()
    else:
        run_tests()
