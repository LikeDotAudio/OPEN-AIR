# /home/anthony/Documents/OPEN-AIR/oaGuiFramework/Tests/test_layout_parser.py
# Author: Gemini (Collaborator)
# Version: 20260405.2355.1
#
# Description: Unit tests for LayoutParser - Verifying Robustness against empty files

import unittest
from unittest.mock import MagicMock, patch
import pathlib
import orjson
from oaGuiFramework.Core.layout_parser import LayoutParser

class TestLayoutParser(unittest.TestCase):

    def setUp(self):
        """Set up."""
        self.parser = LayoutParser(current_version="2026.04.05")

    def test_parse_empty_layout_file(self):
        """Verify that an empty layout.json returns an error dictionary instead of crashing."""
        # BUILD: Create a mock path for a directory
        mock_dir = MagicMock(spec=pathlib.Path)
        mock_dir.exists.return_value = True
        mock_dir.is_file.return_value = False
        
        # mock_dir / "layout.json" -> mock_file
        mock_file = MagicMock(spec=pathlib.Path)
        mock_dir.__truediv__.return_value = mock_file
        
        # layout.json is a file, exists, but size is 0
        mock_file.is_file.return_value = True
        mock_file.stat.return_value.st_size = 0
        
        # OPERATE: Parse directory
        result = self.parser.parse_directory(mock_dir)
        
        # CHECK: Result should be an error type
        self.assertEqual(result["type"], "error")
        self.assertEqual(result["data"]["error_message"], "Empty layout.json")

    def test_parse_valid_layout_file(self):
        """Verify that a valid layout.json is parsed correctly."""
        # BUILD: Mock path and valid content
        valid_data = {"type": "directory_listing", "fields": {}}
        
        mock_dir = MagicMock(spec=pathlib.Path)
        mock_dir.exists.return_value = True
        mock_dir.is_file.return_value = False
        
        mock_file = MagicMock(spec=pathlib.Path)
        mock_dir.__truediv__.return_value = mock_file
        
        mock_file.is_file.return_value = True
        mock_file.stat.return_value.st_size = 100
        
        # Mock the built-in open for this file
        with patch("builtins.open", unittest.mock.mock_open(read_data=orjson.dumps(valid_data))):
            # OPERATE
            result = self.parser.parse_directory(mock_dir)
            
            # CHECK
            self.assertIsNotNone(result)
            self.assertEqual(result.get("type"), "directory_listing")

if __name__ == '__main__':
    unittest.main()
