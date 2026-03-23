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
#from unittest.mock import patch, MagicMock
#from oaGuiEditorWYSIWYG.workspaces.Core.layout.preview_engine import PreviewEngine
#
#class TestPreviewEngine(unittest.TestCase):
#
#    def setUp(self):
#        self.root = tk.Tk()
#        self.root.withdraw()
#        self.preview_frame = tk.Frame(self.root)
#        self.engine = PreviewEngine(self.preview_frame)
#
#    def tearDown(self):
#        self.root.destroy()
#        
#    @patch('oaGuiEditorWYSIWYG.workspaces.Core.layout.preview_engine.DynamicGuiBuilder')
#    def test_render_preview(self, MockGuiBuilder):
#        """Test that the engine uses the GUI builder to render a preview."""
#        mock_builder_instance = MockGuiBuilder.return_value
#        gui_definition = {
#            "type": "frame",
#            "children": [{"type": "label", "text": "Preview"}]
#        }
#        
#        self.engine.render(gui_definition)
#        
#        # Check that the builder was instantiated with the correct frame
#        MockGuiBuilder.assert_called_with(self.preview_frame, event_bus=None) # No event bus in preview
#        
#        # Check that the build was called
#        mock_builder_instance.build_gui.assert_called_once_with(gui_definition)
#        
#    @patch('oaGuiEditorWYSIWYG.workspaces.Core.layout.preview_engine.DynamicGuiBuilder')
#    def test_clear_preview(self, MockGuiBuilder):
#        """Test that the preview area can be cleared."""
#        mock_builder_instance = MockGuiBuilder.return_value
#        
#        # Render something first
#        self.engine.render({"type": "button"})
#        
#        # Now clear it
#        self.engine.clear()
#        
#        # Check that the builder's destroy method was called
#        mock_builder_instance.destroy_widgets.assert_called_once()
#        
#    @patch('oaGuiEditorWYSIWYG.workspaces.Core.layout.preview_engine.DynamicGuiBuilder')
#    def test_update_preview(self, MockGuiBuilder):
#        """Test that updating the preview clears the old one first."""
#        mock_builder_instance = MockGuiBuilder.return_value
#
#        self.engine.render({"type": "button"})
#        self.engine.render({"type": "label"})
#        
#        # Destroy should be called before the second build
#        mock_builder_instance.destroy_widgets.assert_called_once()
#        self.assertEqual(mock_builder_instance.build_gui.call_count, 2)
#
#
#if __name__ == '__main__':
#    unittest.main()
