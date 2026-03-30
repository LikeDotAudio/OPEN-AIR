# oaTests/Tests/test_config_editor.py
# Author: Gemini QA Lead
# Version: 20260330.0001.1
#
# Description: Unit tests for the config.ini TUI editor.

import unittest
import os
import pathlib
import configparser
from oaTests.Managers.configIniEditor.manager import ConfigIniEditor

class TestConfigIniEditor(unittest.TestCase):
    def setUp(self):
        """Build: Create a temporary config.ini file."""
        self.test_file = pathlib.Path("test_config.ini")
        self.config = configparser.ConfigParser()
        self.config["DEBUG_MATRIX"] = {
            "master_debug_enable": "False",
            "sys_comms": "True"
        }
        with open(self.test_file, 'w') as f:
            self.config.write(f)
        
        self.editor = ConfigIniEditor(config_path=self.test_file)

    def tearDown(self):
        """Cleanup: Remove temporary file."""
        if self.test_file.exists():
            os.remove(self.test_file)

    def test_read_flags(self):
        """Check: Editor correctly reads boolean flags from INI."""
        flags = self.editor.get_debug_matrix_flags()
        self.assertFalse(flags["master_debug_enable"])
        self.assertTrue(flags["sys_comms"])

    def test_set_flag(self):
        """Operate: Update a flag and verify disk persistence."""
        self.editor.set_debug_flag("sys_data", True)
        
        # Verify by re-reading the file directly
        new_config = configparser.ConfigParser()
        new_config.read(self.test_file)
        self.assertEqual(new_config["DEBUG_MATRIX"]["sys_data"], "True")

if __name__ == "__main__":
    unittest.main()
