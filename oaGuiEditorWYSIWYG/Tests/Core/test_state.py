import unittest
from oaGuiEditorWYSIWYG.Core.state import State

class TestState(unittest.TestCase):

    def setUp(self):
        # Reset singleton instance for isolated tests
        State._instance = None
        self.state = State()

    def test_singleton_instance(self):
        state2 = State()
        self.assertIs(self.state, state2, "State should be a singleton")

    def test_set_and_get_value(self):
        """Test setting a new value and retrieving it."""
        self.state.set("test_key", "test_value")
        self.assertEqual(self.state.get("test_key"), "test_value")

    def test_get_nonexistent_value_with_default(self):
        """Test getting a value that doesn't exist, with a default."""
        default_val = "default"
        self.assertEqual(self.state.get("nonexistent_key", default_val), default_val)

    def test_get_nonexistent_value_without_default(self):
        """Test getting a value that doesn't exist, without a default."""
        self.assertIsNone(self.state.get("nonexistent_key"))

    def test_update_existing_value(self):
        """Test updating an existing value."""
        self.state.set("test_key", "initial_value")
        self.state.set("test_key", "updated_value")
        self.assertEqual(self.state.get("test_key"), "updated_value")

    def test_set_notifies_observers(self):
        """Test if setting a value notifies registered observers."""
        mock_observer = unittest.mock.Mock()
        self.state.subscribe("change", mock_observer)
        
        self.state.set("another_key", "another_value")
        
        # The observer should be called with the key and new value
        mock_observer.assert_called_once_with("another_key", "another_value")

    def test_unsubscribe_observer(self):
        """Test that an unsubscribed observer is not notified."""
        mock_observer = unittest.mock.Mock()
        self.state.subscribe("change", mock_observer)
        self.state.unsubscribe("change", mock_observer)

        self.state.set("key", "value")
        
        mock_observer.assert_not_called()

if __name__ == '__main__':
    unittest.main()
