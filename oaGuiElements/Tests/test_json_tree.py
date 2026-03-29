import unittest
from unittest.mock import MagicMock
import tkinter as tk
import os

# Set a path for logs before other imports
os.environ['OPEN_AIR_LOG_PATH'] = '/tmp/open_air_tests'

from oaGuiElements.Core.utils.json_tree.json_tree import BuilderDataJsonTreeCreator, JsonTreeWidget

class TestJsonTreeWidget(unittest.TestCase):

    def setUp(self):
        """Set up for the test"""
        if not hasattr(tk, '_default_root'):
            self.root = tk.Tk()
        else:
            self.root = tk._default_root
            
        self.parent_widget = tk.Frame(self.root)

        # Mock the context object
        self.mock_context = MagicMock()
        self.mock_builder_instance = MagicMock()
        self.mock_context.builder_instance = self.mock_builder_instance
        self.mock_context.state_mirror_engine = MagicMock()
        self.mock_context.subscriber_router = MagicMock()
        self.mock_context.base_mqtt_topic_from_path = "devices/test"

    def tearDown(self):
        """Tear down the test environment"""
        for widget in self.parent_widget.winfo_children():
            widget.destroy()
        self.parent_widget.destroy()

    def test_make_json_tree_prevents_name_error(self):
        """
        Tests that BuilderDataJsonTreeCreator.make() does not raise a NameError.
        This test ensures that all necessary modules like TransparencyManager (or its mixin)
        are correctly imported and used.
        """
        config_data = {
            "label_active": "Test JSON Tree",
            "path": "test/json_tree/path",
            "json_source": {"key": "value", "nested": {"a": 1}},
            "show_label": True
        }

        # Call the static make method
        widget = BuilderDataJsonTreeCreator.make(
            parent_widget=self.parent_widget,
            config_data=config_data,
            context=self.mock_context
        )

        # 1. CHECK: The widget was created successfully
        self.assertIsNotNone(widget, "The widget should be created, not None.")
        self.assertIsInstance(widget, JsonTreeWidget, "The created widget should be a JsonTreeWidget.")

        # 2. CHECK: The state mirror engine was called to register the widget.
        self.mock_context.state_mirror_engine.register_widget.assert_called_once_with(
            config_data["path"], None, self.mock_context.base_mqtt_topic_from_path, config_data
        )
        
        # 3. CHECK: The widget state was initialized.
        self.mock_context.state_mirror_engine.initialize_widget_state.assert_called_once_with(config_data["path"])

        # 4. Check if a label was created
        # This is an indirect way to check if the UI was built to some extent
        label_found = False
        for child in widget.header.winfo_children():
            if isinstance(child, tk.Label):
                if child.cget("text") == config_data["label_active"]:
                    label_found = True
                    break
        self.assertTrue(label_found, "The label for the JSON tree should have been created.")

        print("✅ Test passed: 'test_make_json_tree_prevents_name_error' confirmed the fix.")


if __name__ == "__main__":
    unittest.main()
