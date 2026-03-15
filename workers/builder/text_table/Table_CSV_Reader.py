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


class TableCsvReader:
    # Reads data from a CSV file and returns it as a list of dictionaries.
    # Each dictionary in the list represents a row, with keys corresponding to the CSV headers.
    # Inputs:
    #     file_path (str): The full path to the input CSV file.
    # Outputs:
    #     tuple: A tuple containing (headers, data_list) on success, or (None, None) on error.
    def read_from_csv(self, file_path):
        """
        Reads data from a CSV file into a list of dictionaries.

        Args:
            file_path (str): The full path to the input CSV file.

        Returns:
            A tuple containing (headers, data_list) or (None, None) on error.
        """
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ CSV file not found at {file_path}")
            return None, None

        try:
            with open(file_path, "r", newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames
                data = [row for row in reader]

            if LOCAL_DEBUG: logger.success(f"✅ Successfully read {len(data)} rows from {file_path}")
            return headers, data
        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("❌ Error reading from CSV file {file_path}")
            return None, None
