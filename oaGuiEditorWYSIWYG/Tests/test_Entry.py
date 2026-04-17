# oaGuiEditorWYSIWYG/Tests/test_Entry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.1
#
# Description: Unit tests for the oaGuiEditorWYSIWYG entry point.

import unittest
import tkinter as tk
from oaGuiEditorWYSIWYG.Entry import launch_editor
from oaGuiEditorWYSIWYG.Managers.wysiwyg_editor import WysiwygEditor

class TestWysiwygEditorEntry(unittest.TestCase):
    """
    Tests the initialization and basic functionality of the WYSIWYG Editor.
    Follows the F.I.R.S.T principles and BUILD-OPERATE-CHECK pattern.
    """

    def setUp(self):
        """BUILD: Create the root Tkinter window for testing."""
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        """Cleanup: Destroy the root window after each test."""
        self.root.destroy()

    def test_module_loads_correctly(self):
        """OPERATE & CHECK: Verify the module can be loaded and initialized."""
        # BUILD
        # (root created in setUp)

        # OPERATE
        # We try to create an instance with is_standalone=True so it uses our root
        editor = launch_editor(self.root, is_standalone=True)

        # CHECK
        self.assertIsNotNone(editor, "Editor instance should not be None")
        self.assertEqual(editor.parent, self.root, "Editor parent should be the test root")
        self.assertTrue(hasattr(editor, 'window'), "Editor should have a window attribute")
        
        # Verify core components are initialized
        self.assertTrue(hasattr(editor, 'json_tab'), "Editor should have a structure tab (JsonTree)")
        self.assertTrue(hasattr(editor, 'code_tab'), "Editor should have a JSON code tab")
        self.assertTrue(hasattr(editor, 'props_tab'), "Editor should have a properties tab")
        self.assertTrue(hasattr(editor, 'grab_tab'), "Editor should have a library tab")

if __name__ == '__main__':
    unittest.main()
