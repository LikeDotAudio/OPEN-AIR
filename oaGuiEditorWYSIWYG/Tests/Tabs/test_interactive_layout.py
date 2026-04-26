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
#
#        self.root = tk.Tk()
#        self.root.withdraw()
#        self.mock_event_bus = MagicMock()
#
#        self.root.destroy()
#
#    @patch('oaGuiEditorWYSIWYG.Tabs.interactive_layout.DynamicGuiBuilder')
#        """Test that the layout view is created and builds the initial GUI."""
#        mock_builder_instance = MockGuiBuilder.return_value
#        layout_view = InteractiveLayout(self.root, self.mock_event_bus)
#
#        self.assertIsInstance(layout_view, tk.Frame)
#        MockGuiBuilder.assert_called_once_with(layout_view.gui_frame, self.mock_event_bus)
#
#        # It should build an initial empty structure
#        mock_builder_instance.build_gui.assert_called_once()
#
#    @patch('oaGuiEditorWYSIWYG.Tabs.interactive_layout.DynamicGuiBuilder')
#        """Test that receiving a 'json_updated' event triggers a GUI rebuild."""
#        mock_builder_instance = MockGuiBuilder.return_value
#        layout_view = InteractiveLayout(self.root, self.mock_event_bus)
#
#        new_json_data = {"type": "label", "text": "Updated"}
#
#        # Simulate the event
#        layout_view.on_json_updated(new_json_data)
#
#        # Check that the builder destroyed old widgets and rebuilt
#        mock_builder_instance.destroy_widgets.assert_called_once()
#        mock_builder_instance.build_gui.assert_called_with(new_json_data)
#        self.assertEqual(mock_builder_instance.build_gui.call_count, 2) # Once on init, once on update
#
#        """Test that clicking on a widget in the layout publishes a selection event."""
#        # This test is more complex as it requires a real builder and widgets.
#        # We can mock the builder's output to simulate a built GUI.
#        layout_view = InteractiveLayout(self.root, self.mock_event_bus)
#
#        # Let's assume the builder creates a widget and gives it a tag 'widget_id_label1'
#        # And that our selection mechanism relies on finding this widget.
#        mock_widget = tk.Label(layout_view.gui_frame, text="test")
#        mock_widget.widget_id = "label1"
#
#        # The builder would return a map from id to widget
#        layout_view.builder.widgets = {"label1": mock_widget}
#
#        # Simulate the event that would trigger selection
#        # This depends on the implementation (e.g., a binding on the widget)
#        # We'll call the handler directly.
#        layout_view.on_widget_click(mock_widget)
#
#        # The editor should now publish that this widget was selected.
#        # The data published might be the widget's config from the json.
#        # This requires the layout to have access to the json definition.
#        layout_view.json_data = {"children": [{"id": "label1", "type": "label"}]}
#
#        layout_view.on_widget_click(mock_widget)
#
#        self.mock_event_bus.publish.assert_called_with("widget_selected", {"id": "label1", "type": "label"})
#
#    unittest.main()
