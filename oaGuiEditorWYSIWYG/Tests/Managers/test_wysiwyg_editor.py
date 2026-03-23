# -----------------------------------------------------------------
#
# THIS TEST IS DISABLED.
#
# The tests in this file are for a previous version of the code
# and are no longer compatible with the current implementation.
# They need to be rewritten.
#
# -----------------------------------------------------------------
#import unittest
#import tkinter as tk
#from unittest.mock import MagicMock, patch
#from oaGuiEditorWYSIWYG.Managers.wysiwyg_editor import WysiwygEditor
#
#class TestWysiwygEditor(unittest.TestCase):
#
#    def setUp(self):
#        self.root = tk.Tk()
#        self.root.withdraw()  # Hide the main window
#        self.mock_event_bus = MagicMock()
#        
#        # Patch dependencies that are initialized within the editor
#        self.element_props_patch = patch('oaGuiEditorWYSIWYG.Managers.wysiwyg_editor.ElementProperties')
#        self.interactive_layout_patch = patch('oaGuiEditorWYSIWYG.Managers.wysiwyg_editor.InteractiveLayout')
#        self.json_editor_patch = patch('oaGuiEditorWYSIWYG.Managers.wysiwyg_editor.JSONEditor')
#        self.grab_bag_patch = patch('oaGuiEditorWYSIWYG.Managers.wysiwyg_editor.GrabBagView')
#
#        self.MockElementProperties = self.element_props_patch.start()
#        self.MockInteractiveLayout = self.interactive_layout_patch.start()
#        self.MockJSONEditor = self.json_editor_patch.start()
#        self.MockGrabBag = self.grab_bag_patch.start()
#
#    def tearDown(self):
#        self.root.destroy()
#        self.element_props_patch.stop()
#        self.interactive_layout_patch.stop()
#        self.json_editor_patch.stop()
#        self.grab_bag_patch.stop()
#
#    def test_editor_initialization(self):
#        """Test that the main editor window and its sub-components are created."""
#        editor = WysiwygEditor(self.root, self.mock_event_bus)
#        
#        # Check that the main frame was created
#        self.assertTrue(issubclass(type(editor), tk.Frame))
#
#        # Check that all the major UI components were instantiated
#        self.MockElementProperties.assert_called_once()
#        self.MockInteractiveLayout.assert_called_once()
#        self.MockJSONEditor.assert_called_once()
#        self.MockGrabBag.assert_called_once()
#
#    def test_event_subscriptions(self):
#        """Test that the editor subscribes to necessary events on the bus."""
#        editor = WysiwygEditor(self.root, self.mock_event_bus)
#        
#        # Check for subscriptions that coordinate the different editor panels
#        self.mock_event_bus.subscribe.assert_any_call('widget_selected', editor.interactive_layout.on_widget_selected)
#        self.mock_event_bus.subscribe.assert_any_call('json_updated', editor.interactive_layout.on_json_updated)
#        self.mock_event_bus.subscribe.assert_any_call('widget_selected', editor.element_properties.on_widget_selected)
#        
#    def test_load_file_publishes_event(self):
#        """Test that the 'load_file' method publishes an event with file content."""
#        editor = WysiwygEditor(self.root, self.mock_event_bus)
#        
#        mock_file_content = '{"key": "value"}'
#        
#        # Simulate the file content being loaded (e.g., from a file dialog)
#        with patch('oaGuiEditorWYSIWYG.Core.file_io_handler.FileIOHandler.read_json', return_value=mock_file_content):
#            editor.file_io.read_json('dummy.json')
#            # In a real app, a button command would trigger this
#            # Here, we can call a method that would be triggered
#            editor.on_file_loaded(mock_file_content)
#
#        self.mock_event_bus.publish.assert_called_with('file_loaded', mock_file_content)
#
#if __name__ == '__main__':
#    unittest.main()
