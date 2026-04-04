# oaGuiManager/Tests/test_gui_from_json.py
# Author: Gemini CLI
# Version: 20260404.1.3
#
# Description: Unit tests for gui_from_json.py (UniversalGuiLoader)

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
import pathlib
from oaGuiBuilder.Workers.builder import DynamicGuiBuilder
from oaGuiManager.Core.loader.gui_from_json import UniversalGuiLoader

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
        self.test_json_path = "oaGuiManager/Tests/Assets/sample.json"
        self.mock_config = {"app_instance": MagicMock()}

    @patch.object(pathlib.Path, 'exists', return_value=True)
    def test_initialization_and_build(self, mock_exists):
        """OPERATE: Instantiate Loader. CHECK: Verify it sets up and starts the builder."""
        # Patch DynamicGuiBuilder within the module where it's used
        with patch('oaGuiManager.Core.loader.gui_from_json.DynamicGuiBuilder') as mock_builder_class:
            mock_builder = MagicMock()
            mock_builder_class.return_value = mock_builder
            
            loader = UniversalGuiLoader(self.root, self.test_json_path, self.mock_config)
            
            # Trigger the async build manually
            loader._construct_dynamic_gui()
            
            # Verify DynamicGuiBuilder was instantiated
            mock_builder_class.assert_called_once()
            
            # Verify it was gridded and started
            mock_builder.grid.assert_called_once()
            mock_builder.start.assert_called_once()
            
            loader.destroy()

    @patch.object(pathlib.Path, 'exists', return_value=False)
    def test_missing_blueprint_error(self, mock_exists):
        """OPERATE: Trigger build with missing file. CHECK: Verify error handling."""
        loader = UniversalGuiLoader(self.root, self.test_json_path, self.mock_config)
        
        # Trigger build
        with patch.object(loader, '_handle_build_error') as mock_handle:
            loader._construct_dynamic_gui()
            mock_handle.assert_called_once()
            loader.destroy()

if __name__ == '__main__':
    unittest.main()
