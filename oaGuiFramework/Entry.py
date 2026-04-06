# oaGuiFramework/Entry.py
# Author: Gemini (Collaborator)
# Version: 20260405.2215.1
#
# Description: Gatekeeper for the consolidated GUI Framework.
# Combines structural assembly, directory scanning, and layout parsing.

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
    import os
    import sys
    
    print(f"🔍 Discovering and running tests for oaGuiFramework...")
    test_dir = pathlib.Path(__file__).parent / "Tests"
    if not test_dir.is_dir():
        print("❌ No 'Tests/' directory found.")
        return

    loader = unittest.TestLoader()
    suite = loader.discover(str(test_dir), pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == "__main__":
    run_tests()
