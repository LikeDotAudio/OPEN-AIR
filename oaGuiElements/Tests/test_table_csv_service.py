import inspect
import os
import unittest
from unittest.mock import patch

from oaLogging.Methods.matrix_gate import matrix_log

os.environ['OPEN_AIR_LOG_PATH'] = '/tmp/open_air_tests'

# Temporarily add project root to sys.path for sibling module imports
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from oaGuiElements.Core.text.text_table.Core.table_csv_service import TableCSVService


class TestTableCSVService(unittest.TestCase):

    def setUp(self):
        """Set up for the test"""
        self.label = "TestTable"
        # Mock the dependencies that TableCSVService uses
        self.patcher_writer = patch('oaGuiElements.Core.text.text_table.Core.table_csv_service.TableCsvWriter')
        self.patcher_reader = patch('oaGuiElements.Core.text.text_table.Core.table_csv_service.TableCsvReader')
        self.patcher_checker = patch('oaGuiElements.Core.text.text_table.Core.table_csv_service.TableCsvCheck')

        self.mock_writer_class = self.patcher_writer.start()
        self.mock_reader_class = self.patcher_reader.start()
        self.mock_checker_class = self.patcher_checker.start()

        self.mock_reader_instance = self.mock_reader_class.return_value

    def tearDown(self):
        """Tear down the test environment"""
        self.patcher_writer.stop()
        self.patcher_reader.stop()
        self.patcher_checker.stop()

    def test_load_handles_file_not_found_gracefully(self):
        """
        Tests that TableCSVService.load() returns None and logs a debug message
        when the CSV file does not exist, instead of crashing.
        """
        # Configure the mock reader to raise FileNotFoundError
        self.mock_reader_instance.read_from_csv.side_effect = FileNotFoundError

        # Instantiate the service
        service = TableCSVService(self.label)

        # Call the load method
        result = service.load()

        # 1. CHECK: The method should return None
        self.assertIsNone(result, "load() should return None when FileNotFoundError is raised.")

        # 2. CHECK: The reader's read_from_csv method was called
        self.mock_reader_instance.read_from_csv.assert_called_once_with(service.csv_path)

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "✅ Test passed: 'test_load_handles_file_not_found_gracefully' confirmed the fix.", level="INFO")

    def test_load_parses_valid_csv_data(self):
        """
        Tests that TableCSVService.load() correctly parses data returned by the reader.
        """
        # Configure the mock reader to return sample data
        headers = ["id", "model", "value"]
        data = [
            {"id": "1", "model": "ModelA", "value": "10"},
            {"id": "2", "model": "ModelB", "value": "20"},
        ]
        self.mock_reader_instance.read_from_csv.return_value = (headers, data)

        # Instantiate the service
        service = TableCSVService(self.label)

        # Call the load method
        result = service.load()

        # 1. CHECK: The result should not be None
        self.assertIsNotNone(result, "load() should return data, not None.")

        # 2. CHECK: The result should be a dictionary
        self.assertIsInstance(result, dict, "The parsed result should be a dictionary.")

        # 3. CHECK: The dictionary keys should be the 'id's from the data
        self.assertIn("1", result)
        self.assertIn("2", result)

        # 4. CHECK: The values should be the original row dictionaries
        self.assertEqual(result["1"], data[0])
        self.assertEqual(result["2"], data[1])

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, "✅ Test passed: 'test_load_parses_valid_csv_data' works as expected.", level="INFO")


if __name__ == "__main__":
    unittest.main()
