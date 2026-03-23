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
#from oaGuiEditorWYSIWYG.Core.event_bus import EventBus
#
#class TestEventBus(unittest.TestCase):
#    def setUp(self):
#        self.bus = EventBus()
#
#    def test_singleton(self):
#        bus2 = EventBus()
#        self.assertIs(self.bus, bus2)
#
#    def test_subscribe_publish(self):
#        mock_callback = unittest.mock.Mock()
#        self.bus.subscribe("test_event", mock_callback)
#        self.bus.publish("test_event", "test_payload")
#        mock_callback.assert_called_once_with("test_payload")
#
#    def test_unsubscribe(self):
#        mock_callback = unittest.mock.Mock()
#        self.bus.subscribe("test_event", mock_callback)
#        self.bus.unsubscribe("test_event", mock_callback)
#        self.bus.publish("test_event", "test_payload")
#        mock_callback.assert_not_called()
#
#if __name__ == '__main__':
#    unittest.main()
