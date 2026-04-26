# FileWriters/file_csv_export.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: exporters/worker_file_csv_export.py
import csv
import inspect
import os

from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

LOCAL_DEBUG = False

app_constants = Config.get_instance()  # Get the singleton instance

# --- Global Scope Variables ---
CURRENT_DATE = 20250824
CURRENT_TIME = 120616
CURRENT_TIME_HASH = 120616
REVISION_NUMBER = 1
current_version = f"{CURRENT_DATE}.{CURRENT_TIME}.{REVISION_NUMBER}"
current_version_hash = int(CURRENT_DATE) * CURRENT_TIME_HASH * REVISION_NUMBER
current_file = f"{os.path.basename(__file__)}"


class CsvExportUtility:
    """
    A utility class to handle CSV file export logic.
    """

    # Initializes the CsvExportUtility.
    # This constructor takes a function for printing messages to the GUI console,
    # allowing the utility to provide feedback to the user during export operations.
    # Inputs:
    #     print_to_gui_func (function): A function to print messages to the GUI console.
    # Outputs:
    #     None.
    def __init__(self, print_to_gui_func):
        self._print_to_gui_console = print_to_gui_func

    # Exports a list of dictionaries to a CSV file.
    # This method takes data in the form of a list of dictionaries (where each dictionary
    # represents a row) and writes it to the specified CSV file. It automatically extracts
    # headers from the first dictionary's keys and handles file creation.
    # Inputs:
    #     data (list of dict): The data to export, with each dictionary representing a row.
    #     file_path (str): The full path to the output CSV file.
    # Outputs:
    #     None.
    def export_data_to_csv(self, data, file_path):
        """
        Exports a list of dictionaries to a CSV file.

        Args:
            data (list of dict): The data to export. Each dictionary represents a row.
            file_path (str): The path to the output CSV file.
        """
        current_function_name = inspect.currentframe().f_code.co_name

        if LOCAL_DEBUG:
            matrix_log("ui", "exporter", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🟢️️️🟢 ➡️➡️ '{current_function_name}' to save data to CSV at '{file_path}'.", "DEBUG")

        try:
            if not data:
                logger.error("❌ No data to export.")
                return

            # Grab the headers from the first dictionary's keys
            headers = data[0].keys()

            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)

            matrix_log("ui", "exporter", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"✅ Data successfully exported to {file_path}", "SUCCESS")

        except Exception:
            logger.exception("❌ Error in {current_function_name}")
            if LOCAL_DEBUG:
                logger.exception("❌🔴 Arrr, the code be capsized! The error be")
