import csv
import os
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args


class TableCsvWriter:
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
