# oaFileExportCSV/Methods/csv_writer.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2230.2
#
# Description: Pure Rust asynchronous CSV writer (No Python fallback).
from .oaCSVWriter_rs from oaRustCore import oa_csv_writer_rs as oacsvwriter_rs

LOCAL_DEBUG = False

class CSVWriter:
    """
    High-performance asynchronous CSV writer using Rust.
    MANDATORY Rust implementation.
    """
    @staticmethod
    def dump_async(data_list: list, filepath: str):
        """
        Asynchronously writes a list of dictionaries to a CSV file.
        Non-blocking for the Python main thread.
        """
        if LOCAL_DEBUG:
            print("📝🛠️🔗 [CSV] Using PURE RUST async writer.")
        oacsvwriter_rs.dump_async(data_list, filepath)
