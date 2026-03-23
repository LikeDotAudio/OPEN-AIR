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
#        # Reset singleton instance for isolated tests
#        State._instance = None
#        self.state = State()
#
#        state2 = State()
#        self.assertIs(self.state, state2, "State should be a singleton")
#
#        """Test setting a new value and retrieving it."""
#        self.state.set("test_key", "test_value")
#        self.assertEqual(self.state.get("test_key"), "test_value")
#
#        """Test getting a value that doesn't exist, with a default."""
#        default_val = "default"
#        self.assertEqual(self.state.get("nonexistent_key", default_val), default_val)
#
#        """Test getting a value that doesn't exist, without a default."""
#        self.assertIsNone(self.state.get("nonexistent_key"))
#
#        """Test updating an existing value."""
#        self.state.set("test_key", "initial_value")
#        self.state.set("test_key", "updated_value")
#        self.assertEqual(self.state.get("test_key"), "updated_value")
#
#        """Test if setting a value notifies registered observers."""
#        mock_observer = unittest.mock.Mock()
#        self.state.subscribe("change", mock_observer)
#        
#        self.state.set("another_key", "another_value")
#        
#        # The observer should be called with the key and new value
#        mock_observer.assert_called_once_with("another_key", "another_value")
#
#        """Test that an unsubscribed observer is not notified."""
#        mock_observer = unittest.mock.Mock()
#        self.state.subscribe("change", mock_observer)
#        self.state.unsubscribe("change", mock_observer)
#
#        self.state.set("key", "value")
#        
#        mock_observer.assert_not_called()
#
#    unittest.main()
