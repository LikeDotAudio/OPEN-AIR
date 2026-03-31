# text_table/Table_CSV_Writer.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: This module provides functionality to write a list of dictionaries to a CSV file.

import csv
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import os

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()


class CSVWriteError(Exception):
    """Custom exception raised when a CSV file cannot be written."""
    pass


class TableCsvWriter:
    def write_to_csv(self, file_path, headers, data):
        """
        Writes a list of dictionaries to a CSV file.

        Args:
            file_path (str): The full path to the output CSV file.
            headers (list): A list of strings for the CSV header row.
            data (list): A list of dictionaries, where each dictionary is a row.
            
        Raises:
            CSVWriteError: If the file cannot be written.
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(
                    csvfile, fieldnames=headers, extrasaction="ignore"
                )

                writer.writeheader()

                for row_data in data:
                    writer.writerow(row_data)

            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"✅ Successfully wrote table data to {file_path}", level="SUCCESS")
            return True
        except Exception as e:
            from oaOchestration.safe_file_io import handle_file_write_error
            return handle_file_write_error(file_path, e)
