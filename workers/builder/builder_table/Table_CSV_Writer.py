# builder_table/Table_CSV_Writer.py
#
# This module provides functionality to write a list of dictionaries to a CSV file.
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
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args


class TableCsvWriter:
    # Writes a list of dictionaries to a CSV file.
    # This function creates (or overwrites) a CSV file at the specified path, including
    # a header row derived from the provided headers, and then writes each dictionary
    # in the data list as a row in the CSV.
    # Inputs:
    #     file_path (str): The full path to the output CSV file.
    #     headers (list): A list of strings for the CSV header row.
    #     data (list): A list of dictionaries, where each dictionary represents a row.
    # Outputs:
    #     bool: True if the write operation was successful, False otherwise.
    def write_to_csv(self, file_path, headers, data):
        """
        Writes a list of dictionaries to a CSV file.

        Args:
            file_path (str): The full path to the output CSV file.
            headers (list): A list of strings for the CSV header row.
            data (list): A list of dictionaries, where each dictionary is a row.
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

            debug_logger(
                message=f"✅ Successfully wrote table data to {file_path}",
                **_get_log_args(),
            )
            return True
        except Exception as e:
            debug_logger(
                message=f"❌ Error writing to CSV file {file_path}: {e}",
                level="ERROR",
                **_get_log_args(),
            )
            return False