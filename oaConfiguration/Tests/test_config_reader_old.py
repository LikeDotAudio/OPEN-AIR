import unittest
from oaConfiguration.config_reader import Config

class TestConfigReader(unittest.TestCase):
    def test_singleton(self):
        """Test that the Config class acts as a singleton."""
        instance1 = Config.get_instance()
        instance2 = Config.get_instance()
        self.assertIs(instance1, instance2, "Config instance is not the same")

    def test_default_values(self):
        """Test that default values are present after initialization."""
        config = Config.get_instance()
        # These are likely to exist if initialized.
        self.assertTrue(hasattr(config, "MQTT_BROKER_ADDRESS"), "MQTT_BROKER_ADDRESS missing")
        self.assertTrue(hasattr(config, "CURRENT_VERSION"), "CURRENT_VERSION missing")

    def test_global_settings_property(self):
        """Test the global_settings property."""
        config = Config.get_instance()
        settings = config.global_settings
        self.assertIsInstance(settings, dict)
        self.assertIn("general_debug_enabled", settings)
        self.assertIn("debug_enabled", settings)

if __name__ == "__main__":
    unittest.main()
