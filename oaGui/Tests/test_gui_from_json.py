# oaGui/Tests/test_gui_from_json.py
# Author: Gemini CLI
# Version: 20260404.1.5
#
# Description: Unit tests for gui_from_json.py (UniversalGuiLoader)

import pathlib
import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

# Import the class to be patched where it's used
# Import the module under test first
from oaGui.FileReaders.gui_from_json import UniversalGuiLoader


class TestUniversalGuiLoader(unittest.TestCase):
    """Verifies that the Universal GUI Loader correctly instantiates and builds the UI."""

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        """Build test objects and mock services."""
        self.test_json_path_success = "oaGui/Tests/Assets/sample.json"
        self.test_json_path_fail = "oaGui/Tests/Assets/nonexistent.json"
        self.mock_config = {"app_instance": MagicMock()}

    # Patch DynamicGuiBuilder within the module where it's used: gui_from_json.py
    @patch('oaGui.FileReaders.universal_gui_loader.DynamicGuiBuilder')
    @patch.object(pathlib.Path, 'exists', return_value=True)
    def test_initialization_and_build(self, mock_exists, mock_builder_class):
        """OPERATE: Instantiate Loader. CHECK: Verify it sets up and starts the builder."""
        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder

        loader = UniversalGuiLoader(self.root, self.test_json_path_success, self.mock_config)

        # Trigger the async build manually
        loader._construct_dynamic_gui()

        # Verify DynamicGuiBuilder was instantiated
        mock_builder_class.assert_called_once()

        # Verify it was gridded and started
        mock_builder.grid.assert_called_once()
        mock_builder.start.assert_called_once()

        loader.destroy()

    @patch.object(pathlib.Path, 'exists', return_value=False)
    # Patch DynamicGuiBuilder within the module where it's used: gui_from_json.py
    @patch('oaGui.FileReaders.universal_gui_loader.DynamicGuiBuilder')
    def test_missing_blueprint_error(self, mock_builder_class, mock_exists):
        """OPERATE: Trigger build with missing file. CHECK: Verify error handling."""
        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder

        loader = UniversalGuiLoader(self.root, self.test_json_path_fail, self.mock_config)

        # Trigger build
        with patch.object(loader, '_handle_build_error') as mock_handle:
            loader._construct_dynamic_gui()
            mock_handle.assert_called_once()
            loader.destroy()

if __name__ == '__main__':
    unittest.main()
