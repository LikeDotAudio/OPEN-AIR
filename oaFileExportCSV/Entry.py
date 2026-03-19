"""
oaFileExportCSV/Entry.py - The sole orchestrator for the CSV Export Module.
"""

from .FileWriters.file_csv_export import CsvExportUtility
from .Methods.utils_csv_writer import *

def get_csv_export_utility(print_to_gui_func):
    """Returns a new CsvExportUtility instance."""
    return CsvExportUtility(print_to_gui_func)

__all__ = [
    "CsvExportUtility",
    "get_csv_export_utility"
]
