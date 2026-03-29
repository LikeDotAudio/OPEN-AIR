import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk
# Set a path for logs before other imports
import os
os.environ['OPEN_AIR_LOG_PATH'] = '/tmp/open_air_tests'

from oaGuiElements.Core.utils.slider_value.slider_value import BuilderSliderValueCreator

class TestSliderValueCreator(unittest.TestCase):

    def setUp(self):
        """Set up for the test"""
        self.patchers = []
        try:
            # Attempt to create a real Tk root
            self.root = tk.Tk()
            self.root.withdraw()
            # Verify we can actually create widgets
            tk.Frame(self.root).destroy()
        except Exception:
            # Fall back to mocking if Tkinter is not fully functional (e.g., headless CI)
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            self.root.cget.return_value = '#2b2b2b'
            
            # Patch variables and widgets
            self.patchers.append(patch('tkinter.DoubleVar', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.StringVar', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Frame', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Scale', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.ttk.Scale', return_value=MagicMock()))
            
            for p in self.patchers:
                p.start()
            
        self.parent_widget = tk.Frame(self.root)

        # Mock the context object that is passed around during GUI building
        self.mock_context = MagicMock()
        
        # The builder_instance is the main GUI builder that holds state,
        # including the 'topic_widgets' dictionary.
        self.mock_builder_instance = MagicMock()
        self.mock_builder_instance.topic_widgets = {}
        
        # Mock other required context attributes
        self.mock_context.builder_instance = self.mock_builder_instance
        self.mock_context.state_mirror_engine = MagicMock()
        self.mock_context.subscriber_router = MagicMock()
        self.mock_context.base_mqtt_topic_from_path = "devices/test"

    def tearDown(self):
        """Tear down the test environment"""
        if hasattr(self, 'patchers'):
            for p in self.patchers:
                p.stop()
                
        if hasattr(self.root, 'destroy') and not isinstance(self.root, MagicMock):
            try:
                self.parent_widget.destroy()
                self.root.destroy()
            except Exception:
                pass


    def test_make_slider_value_prevents_attribute_error(self):
        """
        Tests that BuilderSliderValueCreator.make() does not raise an AttributeError
        and correctly populates the topic_widgets dictionary on the builder_instance.
        This test replicates the conditions that caused the original error.
        """
        config_data = {
            "label_active": "Test Slider",
            "path": "test/slider/path",
            "min": "0",
            "max": "100",
            "value": "50",
            "units": "dB"
        }

        # Call the static make method
        widget = BuilderSliderValueCreator.make(
            parent_widget=self.parent_widget,
            config_data=config_data,
            context=self.mock_context
        )

        # 1. CHECK: The widget was created successfully
        self.assertIsNotNone(widget, "The widget should be created, not None.")

        # 2. CHECK: The builder_instance's topic_widgets dictionary was populated.
        # This is the crucial check to ensure the 'AttributeError' doesn't happen.
        # The path from config_data should now be a key in the dictionary.
        self.assertIn(config_data["path"], self.mock_builder_instance.topic_widgets)
        
        # 3. CHECK: The value stored is a tuple containing the StringVar and the Scale widget
        stored_tuple = self.mock_builder_instance.topic_widgets[config_data["path"]]
        self.assertIsInstance(stored_tuple, tuple, "The stored value should be a tuple.")
        self.assertEqual(len(stored_tuple), 2, "The tuple should contain two elements.")
        
        # Check the elements in the tuple (using isinstance or checking if they are mocks)
        string_var, scale_widget = stored_tuple
        
        # Check if the value was set correctly
        if not isinstance(string_var, MagicMock):
            self.assertEqual(string_var.get(), str(config_data["value"]))
        
        print("✅ Test passed: 'test_make_slider_value_prevents_attribute_error' confirmed the fix.")


if __name__ == "__main__":
    unittest.main()
