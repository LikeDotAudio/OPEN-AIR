# oaGui/Tests/test_json_gui_host.py
# Author: Gemini CLI
# Version: 20260404.1.5
#
# Description: Unit tests for json_gui_host.py (JsonGuiHost)

import pathlib
import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

# Import the class to be patched where it's used
# Import the module under test first
from oaGui.FileReaders.loader.json_gui_host import JsonGuiHost


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

    # Patch LoaderOrchestrator within the module where it's used: json_gui_host.py
    @patch('oaGui.FileReaders.loader.json_gui_host.LoaderOrchestrator')
    @patch.object(pathlib.Path, 'exists', return_value=True)
    def test_initialization_and_build(self, mock_exists, mock_builder_class):
        """OPERATE: Instantiate Loader. CHECK: Verify it sets up and starts the builder."""
        # unittest.mock passes patches in REVERSE order of decorators (bottom to top).
        # So mock_exists is argument 1, mock_builder_class is argument 2.
        # My previous assumption "top-most is first" was WRONG for unittest.mock.
        # Bottom-most decorator is FIRST argument.

        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder

        loader = JsonGuiHost(self.root, self.test_json_path_success, self.mock_config)

        # Trigger the async build manually
        loader._construct_dynamic_gui()

        # Verify LoaderOrchestrator was instantiated
        mock_builder_class.assert_called_once()

        # Verify it was gridded and started
        mock_builder.grid.assert_called_once()
        mock_builder.start.assert_called_once()

        loader.destroy()

    @patch.object(pathlib.Path, 'exists', return_value=False)
    @patch('oaGui.FileReaders.loader.json_gui_host.LoaderOrchestrator')
    def test_missing_blueprint_error(self, mock_builder_class, mock_exists):
        """OPERATE: Trigger build with missing file. CHECK: Verify error handling."""
        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder

        loader = JsonGuiHost(self.root, self.test_json_path_fail, self.mock_config)

        # Trigger build
        with patch.object(loader, '_handle_build_error') as mock_handle:
            loader._construct_dynamic_gui()
            mock_handle.assert_called_once()
            loader.destroy()

if __name__ == '__main__':
    unittest.main()
