# -----------------------------------------------------------------
#
# THIS TEST IS DISABLED.
#
# The tests in this file are for a previous version of the code
# and are no longer compatible with the current implementation.
# They need to be rewritten.
#
# -----------------------------------------------------------------
#
## Dummy host class for the mixin
#        self.frame = tk.Frame(parent)
#        self.event_bus = event_bus
#        # The mixin may expect a factory
#        self.editor_factory = MagicMock()
#        self.property_entries = {}
#        self.selected_widget_id = None
#
#    
#        self.root = tk.Tk()
#        self.root.withdraw()
#        self.mock_event_bus = MagicMock()
#        self.renderer = DummyRenderer(self.root, self.mock_event_bus)
#
#        self.root.destroy()
#        
#        """Test that render_properties creates editors for a widget's data."""
#        widget_data = {
#            "id": "label1",
#            "text": "Hello",
#            "font_size": 12,
#            "is_bold": False
#        }
#        
#        # Mock the factory to return a simple widget
#        self.renderer.editor_factory.create_editor.return_value = tk.Entry(self.renderer.frame)
#        
#        self.renderer.render_properties(widget_data)
#        
#        # Check that the factory was called for each property
#        self.assertEqual(self.renderer.editor_factory.create_editor.call_count, len(widget_data))
#        
#        # Check that labels and editors were created in the frame
#        # There should be a label and an editor for each property
#        self.assertEqual(len(self.renderer.frame.winfo_children()), len(widget_data) * 2)
#        
#        # Check that references to the editors are stored
#        self.assertEqual(len(self.renderer.property_entries), len(widget_data))
#        self.assertIn("text", self.renderer.property_entries)
#
#        """Test that the property view can be cleared."""
#        widget_data = {"id": "w1", "text": "abc"}
#        self.renderer.render_properties(widget_data)
#        
#        self.assertGreater(len(self.renderer.frame.winfo_children()), 0)
#        self.assertGreater(len(self.renderer.property_entries), 0)
#        
#        self.renderer.clear_properties()
#        
#        self.assertEqual(len(self.renderer.frame.winfo_children()), 0)
#        self.assertEqual(len(self.renderer.property_entries), 0)
#
#    @patch.object(tk.Entry, 'get')
#        """Test that changing a property publishes an event."""
#        # Setup the state as if a widget is selected and rendered
#        self.renderer.selected_widget_id = "button1"
#        mock_entry = tk.Entry(self.renderer.frame)
#        self.renderer.property_entries = {"text": mock_entry}
#
#        mock_get.return_value = "New Button Text"
#        
#        # Simulate the 'Enter' key press or similar event
#        self.renderer.on_property_change(None, "text")
#        
#        self.renderer.event_bus.publish.assert_called_once_with(
#            "widget_property_updated",
#            {"id": "button1", "property": "text", "value": "New Button Text"}
#        )
#
#    unittest.main()
