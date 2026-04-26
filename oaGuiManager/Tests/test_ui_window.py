# oaGuiManager/Tests/test_ui_window.py
# Author: Gemini CLI
# Version: 20260404.1.0
#
# Description: Unit tests for ui_window.py

import unittest
from unittest.mock import MagicMock, patch

from oaGuiManager.Core.ui_window import UIWindowManager


class TestUIWindowManager(unittest.TestCase):
    """Verifies that the main UI window is correctly initialized and configured."""

    @patch('tkinter.Tk')
    def test_create_root_window_configures_styling(self, mock_tk_class):
        """OPERATE: Create root window. CHECK: Verify styling and title are applied."""
        mock_root = MagicMock()
        mock_tk_class.return_value = mock_root

        root = UIWindowManager.create_root_window()

        # Verify base styling
        mock_root.configure.assert_called_with(bg="#2b2b2b")
        mock_root.title.assert_called_with("OPEN-AIR (Partitioned UI)")

        # Verify options are added
        mock_root.option_add.assert_any_call("*Background", "#2b2b2b")
        mock_root.option_add.assert_any_call("*Foreground", "#dcdcdc")

        # Verify minimum size
        mock_root.minsize.assert_called_with(800, 600)

        # Verify withdraw is not called
        mock_root.withdraw.assert_not_called()

    @patch('tkinter.Tk')
    @patch('sys.platform', 'linux')
    def test_create_root_window_does_not_maximize_immediately_on_linux(self, mock_tk_class):
        """OPERATE: Create window on Linux. CHECK: Verify zoomed attribute is NOT set yet."""
        mock_root = MagicMock()
        mock_tk_class.return_value = mock_root

        UIWindowManager.create_root_window()

        # Should NOT be called in create_root_window anymore
        for call in mock_root.attributes.call_args_list:
            if "-zoomed" in str(call):
                self.fail("attributes('-zoomed', True) should not be called in create_root_window")

    @patch('sys.platform', 'linux')
    def test_reveal_main_window_maximizes_on_linux(self):
        """OPERATE: Reveal window on Linux. CHECK: Verify zoomed attribute is set."""
        mock_root = MagicMock()
        mock_splash = MagicMock()

        UIWindowManager.reveal_main_window(mock_root, mock_splash, False)

        mock_root.attributes.assert_called_with("-zoomed", True)
        mock_root.deiconify.assert_called_once()
        mock_splash.hide.assert_called_once()

if __name__ == '__main__':
    unittest.main()
