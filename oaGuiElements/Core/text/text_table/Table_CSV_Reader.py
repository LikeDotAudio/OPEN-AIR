# text_table/Table_CSV_Reader.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: This module provides functionality to read data from CSV files into a list of dictionaries.

import csv
import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()


class CSVReadError(Exception):
    """Custom exception raised when a CSV file cannot be parsed."""
    pass

class TableCsvReader:
    def read_from_csv(self, file_path):
        """
        Reads data from a CSV file into a list of dictionaries.

        Args:
            file_path (str): The full path to the input CSV file.

        Returns:
            tuple: A tuple containing (headers, data_list).
            
        Raises:
            FileNotFoundError: If the file does not exist.
            CSVReadError: If the file cannot be read or parsed.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found at {file_path}")

        try:
            with open(file_path, "r", newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames
                if headers is None:
                     headers = [] # Handle empty files gracefully
                data = [row for row in reader]

            if LOCAL_DEBUG: logger.success(f"✅ Successfully read {len(data)} rows from {file_path}")
            return headers, data
        except Exception as e:
            from oaOchestration.safe_file_io import handle_file_read_error
            return handle_file_read_error(file_path, e, fallback=(None, None))
