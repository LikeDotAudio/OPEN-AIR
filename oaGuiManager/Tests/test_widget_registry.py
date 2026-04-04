# oaGuiManager/Tests/test_widget_registry.py
# Author: Gemini CLI
# Version: 20260404.1.0
#
# Description: Unit tests for widget_registry.py

import unittest
from unittest.mock import MagicMock, patch
import os
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

class TestWidgetRegistry(unittest.TestCase):
    """Verifies that the widget registry correctly handles registration and discovery."""

    def setUp(self):
        """Reset the registry before each test."""
        WidgetRegistry._registry = {}
        WidgetRegistry._initialized = False

    def test_manual_registration(self):
        """OPERATE: Register a mock creator. CHECK: Verify it's retrieved correctly."""
        class MockCreator: pass
        
        WidgetRegistry.register("MockWidget")(MockCreator)
        
        self.assertEqual(WidgetRegistry.get_creator("MockWidget"), MockCreator)
        self.assertIn("MockWidget", WidgetRegistry.get_registry())

    def test_multiple_types_registration(self):
        """OPERATE: Register one creator for multiple types. CHECK: Verify all types work."""
        class MockCreator: pass
        
        WidgetRegistry.register("TypeA", "TypeB")(MockCreator)
        
        self.assertEqual(WidgetRegistry.get_creator("TypeA"), MockCreator)
        self.assertEqual(WidgetRegistry.get_creator("TypeB"), MockCreator)

    @patch('oaGuiManager.Core.fast_scanner.FastScanner.scan_directory')
    @patch('importlib.import_module')
    @patch('pathlib.Path.exists', return_value=True)
    def test_scan_widgets_discovery(self, mock_exists, mock_import, mock_scan):
        """OPERATE: Trigger auto-discovery. CHECK: Verify modules are imported."""
        mock_scan.return_value = [
            "/path/to/oaGuiElements/buttons/btn1.py",
            "/path/to/oaGuiElements/knobs/knb1.py"
        ]
        
        # We need to mock GLOBAL_PROJECT_ROOT as well for relpath
        with patch('oaGuiManager.Core.factory.widget_registry.GLOBAL_PROJECT_ROOT', MagicMock()) as mock_root:
            mock_root.__str__.return_value = "/path/to"
            
            WidgetRegistry.scan_widgets()
            
            # Verify importlib was called for discovered modules
            # Note: The actual path depends on relpath calculation
            self.assertTrue(mock_import.called)
            self.assertTrue(WidgetRegistry._initialized)

if __name__ == '__main__':
    unittest.main()
