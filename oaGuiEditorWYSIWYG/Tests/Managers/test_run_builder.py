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
#        # Mock the dependencies that would normally be passed to the builder
#        self.mock_root = MagicMock()
#        self.mock_event_bus = MagicMock()
#        self.builder = RunBuilder(self.mock_root, self.mock_event_bus)
#
#    @patch('oaGuiEditorWYSIWYG.Managers.run_builder.LoaderOrchestrator')
#        """
#        Test that run_builder correctly invokes the LoaderOrchestrator with JSON content.
#        """
#        json_content = '{"type": "frame", "children": []}'
#        mock_builder_instance = MockUIOrchestrator.return_value
#
#        self.builder.build_gui_from_json(json_content)
#
#        # Verify LoaderOrchestrator was instantiated with the correct root
#        MockUIOrchestrator.assert_called_once_with(self.mock_root, self.mock_event_bus)
#
#        # Verify the build process was started with the parsed JSON
#        mock_builder_instance.build_gui.assert_called_once()
#        args, kwargs = mock_builder_instance.build_gui.call_args
#        self.assertEqual(args[0], {"type": "frame", "children": []})
#
#        """
#        Test that run_builder handles invalid JSON gracefully.
#        """
#        invalid_json = '{"type": "frame", "children": [}'
#
#        # Expecting a JSONDecodeError
#            self.builder.build_gui_from_json(invalid_json)
#
#        # Check that the event bus was notified of the failure
#        self.mock_event_bus.publish.assert_called_with("error", "Failed to decode JSON for builder.")
#
#    @patch('oaGuiEditorWYSIWYG.Managers.run_builder.LoaderOrchestrator')
#        """
#        Test that the builder can clear the previous GUI and rebuild.
#        """
#        json_content = '{"type": "label", "text": "Hello"}'
#        mock_builder_instance = MockUIOrchestrator.return_value
#
#        # First build
#        self.builder.build_gui_from_json(json_content)
#
#        # Check that destroy_widgets was called before the second build
#        self.builder.build_gui_from_json(json_content)
#        mock_builder_instance.destroy_widgets.assert_called_once()
#
#        self.assertEqual(mock_builder_instance.build_gui.call_count, 2)
#
#    unittest.main()
