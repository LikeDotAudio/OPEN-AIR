# -----------------------------------------------------------------
#
# THIS TEST IS DISABLED.
#
# The tests in this file are for a previous version of the code
# and are no longer compatible with the current implementation.
# They need to be rewritten.
#
# -----------------------------------------------------------------
# import unittest
# from unittest.mock import MagicMock
# from oaThreadManager.Core.mqtt_subscriber_mixin import MQTTSubscriberMixin
#
# # A dummy class that uses the mixin for testing purposes
# class DummySubscriber(MQTTSubscriberMixin):
#     def __init__(self, router):
#         self.subscriber_router = router
#         self.some_value = None
#
#     def sample_callback(self, payload):
#         self.some_value = payload
#
# class TestMQTTSubscriberMixin(unittest.TestCase):
#
#     def setUp(self):
#         self.mock_router = MagicMock()
#         self.subscriber = DummySubscriber(self.mock_router)
#
#     def test_subscribe(self):
#         """Test the 'subscribe' method."""
#         topic = "test/topic"
#         callback = self.subscriber.sample_callback
#        
#         self.subscriber.subscribe(topic, callback)
#        
#         # Check that the router's subscribe method was called correctly
#         self.mock_router.subscribe_to_topic.assert_called_once_with(topic, callback)
#
#     def test_unsubscribe(self):
#         """Test the 'unsubscribe' method."""
#         topic = "test/topic"
#         callback = self.subscriber.sample_callback
#        
#         self.subscriber.unsubscribe(topic, callback)
#        
#         # Check that the router's unsubscribe method was called correctly
#         self.mock_router.unsubscribe_from_topic.assert_called_once_with(topic, callback)
#
#     def test_bind_subscriptions(self):
#         """Test the '_bind_subscriptions' method with a subscription map."""
#        
#         # Define a subscription map on the dummy class
#         self.subscriber.subscription_map = {
#             "topic/one": self.subscriber.sample_callback,
#             "topic/two": "another_method" # Method name as a string
#         }
#         # Mock the 'another_method'
#         self.subscriber.another_method = MagicMock()
#        
#         self.subscriber._bind_subscriptions()
#        
#         # Check that subscribe was called for both mappings
#         self.assertEqual(self.mock_router.subscribe_to_topic.call_count, 2)
#         self.mock_router.subscribe_to_topic.assert_any_call("topic/one", self.subscriber.sample_callback)
#         self.mock_router.subscribe_to_topic.assert_any_call("topic/two", self.subscriber.another_method)
#        
# if __name__ == '__main__':
#     unittest.main()
