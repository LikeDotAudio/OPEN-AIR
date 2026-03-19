import unittest
from unittest.mock import MagicMock, patch
import time
import oaWatchdog.Managers.watchdog as watchdog

class TestWatchdogFunctions(unittest.TestCase):
    def setUp(self):
        watchdog.stop_heartbeat()
        watchdog.PANIC_CALLBACKS = []

    def test_kick_watchdog(self):
        """Goal: Verify that kick_watchdog updates the timestamp."""
        old_time = watchdog.LAST_HEARTBEAT_TIME
        time.sleep(0.01)
        watchdog.kick_watchdog()
        self.assertGreater(watchdog.LAST_HEARTBEAT_TIME, old_time)

    @patch("threading.Thread")
    def test_start_heartbeat(self, mock_thread):
        """Goal: Verify that start_heartbeat spawns a thread and sets running flag."""
        watchdog.start_heartbeat()
        self.assertTrue(watchdog.WATCHDOG_RUNNING)
        self.assertTrue(mock_thread.called)

    def test_register_panic_callback(self):
        """Goal: Verify that callbacks can be registered."""
        callback = MagicMock()
        watchdog.register_panic_callback(callback)
        self.assertIn(callback, watchdog.PANIC_CALLBACKS)

if __name__ == "__main__":
    unittest.main()
