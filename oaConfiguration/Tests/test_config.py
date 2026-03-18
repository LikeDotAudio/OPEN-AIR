import unittest
import pathlib
import os
import configparser
from oaConfiguration.config import create_default_config_ini

class TestConfigGenerator(unittest.TestCase):
    def setUp(self):
        self.test_config_path = pathlib.Path("test_config.ini")
        if self.test_config_path.exists():
            self.test_config_path.unlink()

    def tearDown(self):
        if self.test_config_path.exists():
            self.test_config_path.unlink()

    def test_create_default_config_ini(self):
        """Test that the default config.ini is created with expected sections."""
        create_default_config_ini(self.test_config_path, silent=True)
        
        self.assertTrue(self.test_config_path.exists(), "config.ini was not created")
        
        config = configparser.ConfigParser()
        config.read(self.test_config_path)
        
        expected_sections = ["Version", "Debug", "UI", "MQTT", "ScanSettings", "OSC"]
        for section in expected_sections:
            self.assertIn(section, config.sections(), f"Section {section} missing from config")

        # Check some specific values
        self.assertEqual(config["Version"]["CURRENT_VERSION"], "20251225")
        self.assertEqual(config["MQTT"]["BROKER_ADDRESS"], "localhost")
        self.assertEqual(config["ScanSettings"]["scan_gateways"], "True")

if __name__ == "__main__":
    unittest.main()
