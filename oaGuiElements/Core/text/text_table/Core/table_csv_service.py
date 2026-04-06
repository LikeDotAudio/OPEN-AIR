# Core/table_csv_service.py
from oaGuiFramework.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import os
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import re
from ..Table_CSV_Writer import TableCsvWriter
from ..Table_CSV_Reader import TableCsvReader
from ..Table_CSV_check import TableCsvCheck
import oaOchestration.Constants.project_paths as app_paths

CSV_SAVE_DIR = str(app_paths.TABLES_DIR)

class TableCSVService:
    """Manages local CSV backup and restoration for the table widget."""

    def __init__(self, label):
        self.writer = TableCsvWriter()
        self.reader = TableCsvReader()
        self.checker = TableCsvCheck()
        clean_lbl = re.sub(r"[^a-zA-Z0-9]", "_", label)
        self.csv_path = os.path.join(CSV_SAVE_DIR, f"{clean_lbl}.csv")

    def save(self, headers, item_map):
        """Writes current item_map to the local CSV backup."""
        if headers:
            self.writer.write_to_csv(self.csv_path, list(headers), list(item_map.values()))

    def load(self):
        """Reads from CSV and returns a dictionary structured for the table update."""
        from loguru import logger
        try:
            headers, data = self.reader.read_from_csv(self.csv_path)
        except FileNotFoundError:
            matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"📜 CSV file not found at {self.csv_path}. This is normal if no data has been saved yet.", level="DEBUG")
            return None

        if not data: 
            return None
        
        data_dict = {}
        kp = ["id", "gpib_address", "serial_number", "resource_string", "model"]
        for i, row in enumerate(data):
            key = next((row[k] for k in kp if k in row and row[k]), f"row_{i}")
            data_dict[key] = row
        return data_dict

    def check_integrity(self, headers, topic):
        """Initializes/validates CSV from remote topic data."""
        self.checker.initialize_from_csv(self.csv_path, headers, topic)