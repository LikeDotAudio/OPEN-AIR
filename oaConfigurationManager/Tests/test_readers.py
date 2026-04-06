# oaConfigurationManager/Tests/test_readers.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Unit tests for FileReaders in oaConfigurationManager.

import unittest
from pathlib import Path
from oaConfigurationManager.Core.config_loader import ConfigLoader

class TestConfigReader(unittest.TestCase):
    """
    Harden FileReaders for oaConfigurationManager.
    """

    def setUp(self):
        """BUILD: Define the path to the mock sample file."""
        self.assets_dir = Path(__file__).parent / "Assets"
        self.sample_ini = self.assets_dir / "sample.ini"
        self.dummy_setup = self.assets_dir / "dummy_setup.py"

    def test_config_loader(self):
        """OPERATE & CHECK: Verify that the config loader correctly reads the mock file."""
        # Ensure the mock file exists
        self.assertTrue(self.sample_ini.exists(), f"Mock file {self.sample_ini} not found.")

        # Operate
        config = ConfigLoader.load(self.sample_ini, self.dummy_setup)

        # Check
        self.assertIsNotNone(config)
        self.assertEqual(config["Version"]["CURRENT_VERSION"], "20260316.1")
        # Note: configparser may include quotes if present in the .ini file
        self.assertEqual(config["MQTT"]["BROKER_ADDRESS"], '"localhost"')

if __name__ == "__main__":
    unittest.main()
