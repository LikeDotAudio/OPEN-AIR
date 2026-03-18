import unittest
import configparser
from unittest.mock import patch, MagicMock
from managers.configini.config_reader import Config

class TestConfigReader(unittest.TestCase):
    def test_singleton_integrity(self):
        """BUILD: Request two instances. CHECK: Assert they are identical."""
        c1 = Config.get_instance()
        c2 = Config.get_instance()
        self.assertIs(c1, c2)

    @patch("managers.configini.config_reader.ConfigLoader.load")
    def test_config_loading_from_file(self, mock_load):
        """BUILD: Mock ConfigParser content. OPERATE: Load. CHECK: Assert specific value."""
        # Setup mock ConfigParser
        mock_config = configparser.ConfigParser()
        mock_config.add_section("MQTT")
        mock_config.set("MQTT", "BROKER_ADDRESS", "10.0.0.1")
        mock_load.return_value = mock_config
        
        config = Config.get_instance()
        # Manually trigger read_config logic
        config.read_config()
        
        self.assertEqual(config.MQTT_BROKER_ADDRESS, "10.0.0.1")

if __name__ == "__main__":
    unittest.main()
