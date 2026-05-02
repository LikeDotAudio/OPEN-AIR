# oaGui/Tests/test_registry_widget_store.py
# Author: Gemini CLI
# Version: 20260404.1.0
#
# Description: Unit tests for registry_widget_store.py

import unittest
from unittest.mock import MagicMock, patch

from oaGui.Hooks.registry.registry_widget_store import RegistryWidgetStore


class TestWidgetRegistry(unittest.TestCase):
    """Verifies that the widget registry correctly handles registration and discovery."""

    def setUp(self):
        """Reset the registry before each test."""
        RegistryWidgetStore._registry = {}
        RegistryWidgetStore._initialized = False

    def test_manual_registration(self):
        """OPERATE: Register a mock creator. CHECK: Verify it's retrieved correctly."""
        class MockCreator: pass

        RegistryWidgetStore.register("MockWidget")(MockCreator)

        self.assertEqual(RegistryWidgetStore.get_creator("MockWidget"), MockCreator)
        self.assertIn("MockWidget", RegistryWidgetStore.get_registry())

    def test_multiple_types_registration(self):
        """OPERATE: Register one creator for multiple types. CHECK: Verify all types work."""
        class MockCreator: pass

        RegistryWidgetStore.register("TypeA", "TypeB")(MockCreator)

        self.assertEqual(RegistryWidgetStore.get_creator("TypeA"), MockCreator)
        self.assertEqual(RegistryWidgetStore.get_creator("TypeB"), MockCreator)

    @patch('oaGui.FileReaders.scanner.folder_fast_io_utility.FastScanner.scan_directory')
    @patch('importlib.import_module')
    @patch('pathlib.Path.exists', return_value=True)
    def test_scan_widgets_discovery(self, mock_exists, mock_import, mock_scan):
        """OPERATE: Trigger auto-discovery. CHECK: Verify modules are imported."""
        mock_scan.return_value = [
            "/path/to/oaGuiElements/buttons/btn1.py",
            "/path/to/oaGuiElements/knobs/knb1.py"
        ]

        # We need to mock GLOBAL_PROJECT_ROOT as well for relpath
        with patch('oaGui.Hooks.registry.registry_widget_store.GLOBAL_PROJECT_ROOT', MagicMock()) as mock_root:
            mock_root.__str__.return_value = "/path/to"

            RegistryWidgetStore.scan_widgets()

            # Verify importlib was called for discovered modules
            # Note: The actual path depends on relpath calculation
            self.assertTrue(mock_import.called)
            self.assertTrue(RegistryWidgetStore._initialized)

if __name__ == '__main__':
    unittest.main()
