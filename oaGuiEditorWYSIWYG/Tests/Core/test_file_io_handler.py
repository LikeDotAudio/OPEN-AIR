import unittest
import os
from unittest.mock import mock_open, patch
from oaGuiEditorWYSIWYG.Core.file_io_handler import FileIOHandler

class TestFileIOHandler(unittest.TestCase):

    def setUp(self):
        self.handler = FileIOHandler()

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    def test_read_json_success(self, mock_file):
        data = self.handler.read_json("dummy_path.json")
        self.assertEqual(data, {"key": "value"})
        mock_file.assert_called_once_with("dummy_path.json", 'r')

    @patch("builtins.open", new_callable=mock_open)
    def test_write_json_success(self, mock_file):
        data_to_write = {"key": "new_value"}
        self.handler.write_json("dummy_path.json", data_to_write)
        mock_file.assert_called_once_with("dummy_path.json", 'w')
        # Extracting the call arguments from the mock
        handle = mock_file()
        written_data = handle.write.call_args[0][0]
        import json
        self.assertEqual(json.loads(written_data), data_to_write)

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_read_json_file_not_found(self, mock_file):
        with self.assertRaises(FileNotFoundError):
            self.handler.read_json("non_existent.json")

    @patch("builtins.open", side_effect=IOError)
    def test_write_json_io_error(self, mock_file):
        with self.assertRaises(IOError):
            self.handler.write_json("unwritable.json", {})

if __name__ == '__main__':
    unittest.main()
