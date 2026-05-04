import inspect
import os
import tkinter as tk
import unittest
from unittest.mock import MagicMock, patch

from oaLogging.Methods.matrix_gate import matrix_log

# Set a path for logs before other imports
os.environ['OPEN_AIR_LOG_PATH'] = '/tmp/open_air_tests'

from oaGuiElements.Core.input.json_tree.Core.json_tree import BuilderDataJsonTreeCreator, JsonTreeWidget


class TestJsonTreeWidget(unittest.TestCase):

    def setUp(self):
        """Set up for the test"""
        self.patchers = []
        try:
            # Attempt to create a real Tk root
            self.root = tk.Tk()
            self.root.withdraw()
            # Verify we can actually create widgets (not just initialize Tcl)
            tk.Frame(self.root).destroy()
        except Exception:
            # Fall back to mocking if Tkinter is not fully functional (e.g., headless CI)
            self.root = MagicMock()
            self.root.winfo_exists.return_value = True
            self.root.cget.return_value = '#2b2b2b'

            # Patch variables and widgets
            self.patchers.append(patch('tkinter.DoubleVar', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.StringVar', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.IntVar', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.BooleanVar', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Frame', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Label', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Canvas', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Entry', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Button', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Scrollbar', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Text', return_value=MagicMock()))
            self.patchers.append(patch('tkinter.Listbox', return_value=MagicMock()))

            for p in self.patchers:
                p.start()

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
        if hasattr(self, 'patchers'):
            for p in self.patchers:
                p.stop()

        if hasattr(self.root, 'destroy') and not isinstance(self.root, MagicMock):
            try:
                self.parent_widget.destroy()
                self.root.destroy()
            except Exception:
                pass

    def test_make_json_tree_prevents_name_error(self):
        """
        Tests that BuilderDataJsonTreeCreator.make() does not raise a NameError.
        This test ensures that all necessary modules like EngineVisualEffects (or its mixin)
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

        # If we're mocking, we might not get a JsonTreeWidget instance back if Frame was patched
        if not isinstance(self.parent_widget, MagicMock):
            self.assertIsInstance(widget, JsonTreeWidget, "The created widget should be a JsonTreeWidget.")

        # 2. CHECK: The state mirror engine was called to register the widget.
        self.mock_context.state_mirror_engine.register_widget.assert_called_once_with(
            config_data["path"], None, self.mock_context.base_mqtt_topic_from_path, config_data
        )

        # 3. CHECK: The widget state was initialized.
        self.mock_context.state_mirror_engine.initialize_widget_state.assert_called_once_with(config_data["path"])

        # Check if a label was created (only if not mocked)
        if not isinstance(self.parent_widget, MagicMock):
            label_found = False
            for child in widget.header.winfo_children():
                if isinstance(child, tk.Label):
                    if child.cget("text") == config_data["label_active"]:
                        label_found = True
                        break
            self.assertTrue(label_found, "The label for the JSON tree should have been created.")

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "✅ Test passed: 'test_make_json_tree_prevents_name_error' confirmed the fix.", level="INFO")


if __name__ == "__main__":
    unittest.main()
