import unittest
from unittest.mock import MagicMock
from workers.Splinker.splinker import ControlBroker

class TestSplinker(unittest.TestCase):
    def setUp(self):
        self.state_cache_manager = MagicMock()
        self.mqtt_manager = MagicMock()
        self.broker = ControlBroker.get_instance(
            state_cache_manager=self.state_cache_manager,
            mqtt_manager=self.mqtt_manager
        )

    def test_singleton(self):
        """Test that ControlBroker is a singleton."""
        instance1 = ControlBroker.get_instance()
        instance2 = ControlBroker.get_instance()
        self.assertIs(instance1, instance2)

    def test_initialization(self):
        """Test broker initialization."""
        self.assertTrue(hasattr(self.broker, "splinks"))
        self.assertIsInstance(self.broker.splinks, list)
        self.assertFalse(self.broker.panic_active)

    def test_add_monitor_callback(self):
        """Test adding a monitor callback."""
        callback = MagicMock()
        self.broker.add_monitor_callback(callback)
        self.assertIn(callback, self.broker._monitor_callbacks)
        
        # Cleanup
        self.broker.remove_monitor_callback(callback)
        self.assertNotIn(callback, self.broker._monitor_callbacks)

if __name__ == "__main__":
    unittest.main()
