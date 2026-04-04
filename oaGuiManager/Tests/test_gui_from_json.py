# oaGuiManager/Tests/test_gui_from_json.py
# Author: Gemini CLI
# Version: 20260404.1.0
#
# Description: Unit tests for gui_from_json.py (UniversalGuiLoader)

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
import pathlib
from oaGuiManager.Core.loader.gui_from_json import UniversalGuiLoader

class TestUniversalGuiLoader(unittest.TestCase):
    """Verifies that the Universal GUI Loader correctly instantiates and builds the UI."""

    def setUp(self):
        """Build test objects and mock services."""
        self.mock_parent = MagicMock(spec=tk.Frame)
        self.mock_parent.cget.return_value = "#2b2b2b"
        self.mock_parent.winfo_toplevel.return_value = MagicMock()
        
        self.test_json_path = "oaGuiManager/Tests/Assets/sample.json"
        self.mock_config = {"app_instance": MagicMock()}

    @patch('oaGuiBuilder.Workers.builder.DynamicGuiBuilder')
    @patch('pathlib.Path.exists', return_value=True)
    def test_initialization_and_build(self, mock_exists, mock_builder_class):
        """OPERATE: Instantiate Loader. CHECK: Verify it sets up and starts the builder."""
        mock_builder = MagicMock()
        mock_builder_class.return_value = mock_builder
        
        loader = UniversalGuiLoader(self.mock_parent, self.test_json_path, self.mock_config)
        
        # Trigger the async build manually
        loader._construct_dynamic_gui()
        
        # Verify DynamicGuiBuilder was instantiated
        mock_builder_class.assert_called_once()
        args, kwargs = mock_builder_class.call_args
        self.assertEqual(kwargs['json_path'], str(pathlib.Path(self.test_json_path)))
        self.assertEqual(kwargs['tab_name'], "SAMPLE")
        
        # Verify it was gridded and started
        mock_builder.grid.assert_called_once()
        mock_builder.start.assert_called_once()

    @patch('pathlib.Path.exists', return_value=False)
    def test_missing_blueprint_error(self, mock_exists):
        """OPERATE: Trigger build with missing file. CHECK: Verify error handling."""
        loader = UniversalGuiLoader(self.mock_parent, self.test_json_path, self.mock_config)
        
        # Trigger build
        with patch.object(loader, '_handle_build_error') as mock_handle:
            loader._construct_dynamic_gui()
            mock_handle.assert_called_once()

if __name__ == '__main__':
    unittest.main()
