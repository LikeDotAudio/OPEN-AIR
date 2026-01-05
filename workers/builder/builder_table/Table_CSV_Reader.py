import csv
import os
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

class TableCsvReader:
    def read_from_csv(self, file_path):
        """
        Reads data from a CSV file into a list of dictionaries.

        Args:
            file_path (str): The full path to the input CSV file.
            
        Returns:
            A tuple containing (headers, data_list) or (None, None) on error.
        """
        if not os.path.exists(file_path):
            debug_logger(message=f"⚠️ CSV file not found at {file_path}", level="WARNING", **_get_log_args())
            return None, None
            
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames
                data = [row for row in reader]
                
            debug_logger(message=f"✅ Successfully read {len(data)} rows from {file_path}", **_get_log_args())
            return headers, data
        except Exception as e:
            debug_logger(message=f"❌ Error reading from CSV file {file_path}: {e}", level="ERROR", **_get_log_args())
            return None, None
