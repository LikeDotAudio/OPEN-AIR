# oaFileImportCSV/Methods/csv_parser.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2150.2
#
# Description: Pure Rust CSV parser with Polars support (No Python fallback).

LOCAL_DEBUG = False
from oaRustCore import oa_csv_parser_rs as oacsvparser_rs


class CSVParser:
    """
    High-performance CSV parser using Rust and Polars.
    MANDATORY Rust implementation.
    """
    @staticmethod
    def convert_csv_unknown(file_path: str):
        if LOCAL_DEBUG:
            print("📄🛠️🔗 [CSV] Using PURE RUST parser (nom/regex).")
        return oacsvparser_rs.convert_csv_unknown(file_path)

    @staticmethod
    def load_large_csv(file_path: str):
        if LOCAL_DEBUG:
            print("📊🛠️🔗 [CSV] Using PURE RUST loader (Polars).")
        return oacsvparser_rs.load_large_csv(file_path)
