# oaGuiManager/Tests/test_gui_widget_factory.py
# Author: Gemini CLI
# Version: 20260404.1.4
#
# Description: Unit tests for gui_widget_factory.py

import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk  # ⚡ FIX: Import tkinter for creating real frames
from oaGuiManager.Core.factory.gui_widget_factory import GuiWidgetFactoryMixin

class MockBuilder(GuiWidgetFactoryMixin):
    """Minimal subclass for testing the Mixin."""
    def __init__(self):
        self.widget_factory = {}
        # ⚡ FIX: Add a proper root context for Tkinter widgets
        self.root = tk.Tk()

class TestGuiWidgetFactory(unittest.TestCase):
    """Verifies that the factory correctly resolves and wraps widget creators."""

    @classmethod
    def setUpClass(cls):
        # ⚡ FIX: Create a root window once for all tests to avoid errors
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        # ⚡ FIX: Clean up the root window
        cls.root.destroy()

    def test_lazy_wrap_instantiation(self):
        """OPERATE: Trigger lazy wrap. CHECK: Verify it correctly calls the module class."""
        builder = MockBuilder()
        
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_import.return_value = mock_module
            
            class RealMockClass:
                @staticmethod
                def mock_method(*args, **kwargs): pass
            
            mock_class = MagicMock(spec_set=RealMockClass)
            mock_module.MockClass = mock_class
            
            wrapper = builder._lazy_wrap('mock_path', 'MockClass', 'mock_method')
            
            # ⚡ FIX: Use a real tk.Frame as parent instead of MagicMock
            # This prevents `AttributeError: '_w'` when child widgets are instantiated.
            parent = tk.Frame(self.root)
            config = {"some": "data"}
            wrapper(parent, config)
            
            mock_import.assert_called_with('mock_path')
            mock_class.mock_method.assert_called_with(builder, parent, config, context=None, builder_instance=builder)

    def test_lazy_wrap_with_static_make(self):
        """OPERATE: Trigger lazy wrap on a class with 'make'. CHECK: Verify 'make' is used."""
        builder = MockBuilder()
        
        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_import.return_value = mock_module
            
            class ClassWithMake:
                @staticmethod
                def make(*args, **kwargs): pass
            
            mock_class = MagicMock(spec_set=ClassWithMake)
            mock_module.MockClass = mock_class
            
            wrapper = builder._lazy_wrap('mock_path', 'MockClass', 'mock_method')
            
            # ⚡ FIX: Use a real tk.Frame for the parent
            parent = tk.Frame(self.root)
            config = {"some": "data"}
            wrapper(parent, config)
            
            mock_class.make.assert_called_once()

if __name__ == '__main__':
    unittest.main()
