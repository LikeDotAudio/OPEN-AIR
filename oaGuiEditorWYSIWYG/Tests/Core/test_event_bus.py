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
#        self.bus = EventBus()
#
#        bus2 = EventBus()
#        self.assertIs(self.bus, bus2)
#
#        mock_callback = unittest.mock.Mock()
#        self.bus.subscribe("test_event", mock_callback)
#        self.bus.publish("test_event", "test_payload")
#        mock_callback.assert_called_once_with("test_payload")
#
#        mock_callback = unittest.mock.Mock()
#        self.bus.subscribe("test_event", mock_callback)
#        self.bus.unsubscribe("test_event", mock_callback)
#        self.bus.publish("test_event", "test_payload")
#        mock_callback.assert_not_called()
#
#    unittest.main()
