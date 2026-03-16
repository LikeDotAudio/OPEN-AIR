# text_table/Table_CSV_Reader.py
#
# This module provides functionality to read data from CSV files into a list of dictionaries.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1
import csv
import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

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
            from workers.handlers.safe_file_io import handle_file_read_error
            return handle_file_read_error(file_path, e, fallback=(None, None))
