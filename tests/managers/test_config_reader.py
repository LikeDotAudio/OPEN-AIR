import unittest
from unittest.mock import patch, mock_open
from managers.configini.config_reader import Config

class TestConfigReader(unittest.TestCase):
    def test_singleton_integrity(self):
        """BUILD: Request two instances. CHECK: Assert they are identical."""
        # Reset for test isolation if needed, though get_instance is a standard singleton
        c1 = Config.get_instance()
        c2 = Config.get_instance()
        self.assertIs(c1, c2)

    @patch("builtins.open", new_callable=mock_open, read_data="[MQTT]\nBROKER_ADDRESS=10.0.0.1")
    @patch("managers.configini.config_reader.ConfigDefaults.get_defaults")
    def test_config_loading_from_file(self, mock_defaults, mock_file):
        """BUILD: Mock file content. OPERATE: Load. CHECK: Assert specific value."""
        # Note: read_config is internal or called by get_instance
        # We'll use a fresh instance logic for the mock if possible or patch the existing one
        mock_defaults.return_value = {"MQTT": {"BROKER_ADDRESS": "localhost"}}
        
        config = Config.get_instance()
        # Manually trigger read_config logic or re-init
        config.read_config("mock_config.ini")
        
        self.assertEqual(config.MQTT_BROKER_ADDRESS, "10.0.0.1")

if __name__ == "__main__":
    unittest.main()
