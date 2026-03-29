import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from tkinter import ttk
import os

# Set a path for logs before other imports
# This is a pattern seen in the project to handle logging initialization
os.environ['OPEN_AIR_LOG_PATH'] = '/tmp/open_air_tests'

from oaGuiElements.Core.utils.slider_value.slider_value import BuilderSliderValueCreator

class TestSliderValueCreator(unittest.TestCase):

    def setUp(self):
        """Set up for the test"""
        # Create a root window to act as parent for widgets
        # In a real test suite, you might want to manage this root instance more carefully
        # but for a single test file, creating it once is fine.
        if not hasattr(tk, '_default_root'):
            self.root = tk.Tk()
        else:
            self.root = tk._default_root
            
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
        # Destroy the parent widget to clean up
        for widget in self.parent_widget.winfo_children():
            widget.destroy()
        self.parent_widget.destroy()


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
        self.assertIsInstance(widget, tk.Frame, "The created widget should be a tk.Frame.")

        # 2. CHECK: The builder_instance's topic_widgets dictionary was populated.
        # This is the crucial check to ensure the 'AttributeError' doesn't happen.
        # The path from config_data should now be a key in the dictionary.
        self.assertIn(config_data["path"], self.mock_builder_instance.topic_widgets)
        
        # 3. CHECK: The value stored is a tuple containing the StringVar and the Scale widget
        stored_tuple = self.mock_builder_instance.topic_widgets[config_data["path"]]
        self.assertIsInstance(stored_tuple, tuple, "The stored value should be a tuple.")
        self.assertEqual(len(stored_tuple), 2, "The tuple should contain two elements.")
        
        # Check the elements in the tuple
        string_var, scale_widget = stored_tuple
        self.assertIsInstance(string_var, tk.StringVar, "The first element should be a tk.StringVar.")
        self.assertIsInstance(scale_widget, ttk.Scale, "The second element should be a ttk.Scale.")
        
        # Check if the value was set correctly
        self.assertEqual(string_var.get(), str(config_data["value"]))
        
        print("✅ Test passed: 'test_make_slider_value_prevents_attribute_error' confirmed the fix.")


if __name__ == "__main__":
    unittest.main()
