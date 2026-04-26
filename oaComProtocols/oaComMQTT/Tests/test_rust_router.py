import unittest

from oaComProtocols.oaComMQTT.Core.mqtt_router import MqttRouter


class TestMqttRouter(unittest.TestCase):
    def setUp(self):
        self.router = MqttRouter()

    def test_exact_match(self):
        called = []
        def cb(msg): called.append(msg)

        self.router.subscribe("test/topic", cb)
        callbacks = self.router.match_topic("test/topic")
        self.assertEqual(len(callbacks), 1)
        callbacks[0]("hello")
        self.assertEqual(called, ["hello"])

    def test_wildcard_match(self):
        called = []
        def cb(msg): called.append(msg)

        self.router.subscribe("st2138/#", cb)
        callbacks = self.router.match_topic("st2138/device/1/param/freq")
        self.assertEqual(len(callbacks), 1)
        callbacks[0]("world")
        self.assertEqual(called, ["world"])

    def test_plus_wildcard(self):
        called = []
        def cb(msg): called.append(msg)

        self.router.subscribe("a/+/c", cb)
        self.assertEqual(len(self.router.match_topic("a/b/c")), 1)
        self.assertEqual(len(self.router.match_topic("a/x/c")), 1)
        self.assertEqual(len(self.router.match_topic("a/b/d")), 0)

if __name__ == "__main__":
    unittest.main()
