import unittest
import tkinter as tk
from unittest.mock import MagicMock
from oaGuiEditorWYSIWYG.workspaces.json_editor import JSONEditor

class TestJSONEditor(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.mock_event_bus = MagicMock()

    def tearDown(self):
        self.root.destroy()

    def test_json_editor_creation(self):
        """Test the creation of the JSON editor widget."""
        editor = JSONEditor(self.root, self.mock_event_bus)
        self.assertIsInstance(editor, tk.Frame)
        self.assertTrue(any(isinstance(w, tk.Text) for w in editor.winfo_children()))

    def test_load_json_into_editor(self):
        """Test that JSON data is loaded and displayed in the text widget."""
        editor = JSONEditor(self.root, self.mock_event_bus)
        json_data = {"key": "value", "nested": {"num": 1}}
        
        # Simulate the event that loads the data
        editor.on_file_loaded(json_data)
        
        # Check the content of the text widget
        content = editor.text_widget.get("1.0", "end-1c")
        import json
        self.assertEqual(json.loads(content), json_data)

    def test_editing_json_publishes_event(self):
        """Test that modifying the text and hitting the update button publishes an event."""
        editor = JSONEditor(self.root, self.mock_event_bus)
        
        # Load initial data
        initial_data = {"key": "value"}
        editor.on_file_loaded(initial_data)
        
        # Modify the text in the widget
        new_content_str = '{"key": "new_value"}'
        editor.text_widget.delete("1.0", "end")
        editor.text_widget.insert("1.0", new_content_str)
        
        # Simulate clicking the update button
        editor.update_json()
        
        # Verify the 'json_updated' event was published with the correct data
        expected_data = {"key": "new_value"}
        self.mock_event_bus.publish.assert_called_once_with("json_updated", expected_data)

    def test_invalid_json_publishes_error(self):
        """Test that attempting to update with invalid JSON publishes an error."""
        editor = JSONEditor(self.root, self.mock_event_bus)
        
        invalid_content = '{"key": "value"' # Missing closing brace
        editor.text_widget.insert("1.0", invalid_content)
        
        editor.update_json()
        
        self.mock_event_bus.publish.assert_called_once_with("error", "Invalid JSON format.")

if __name__ == '__main__':
    unittest.main()
