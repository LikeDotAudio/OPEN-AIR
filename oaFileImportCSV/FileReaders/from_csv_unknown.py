# FileReaders/from_csv_unknown.py
#
# Best-effort CSV parser for unknown header formats.
#
# Author: Anthony Peter Kuzub
# Version: 20260331.2240.1

import os
import csv
import inspect
from loguru import logger
from oaLogging.Methods.matrix_gate import matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config

# --- Constants ---
VERSION = "20260331.2240.1"

try:
    from oaRustCore.oa_csv_parser_rs import convert_csv_unknown as rust_convert_csv_unknown
    HAS_RUST_CSV = True
except ImportError:
    logger.warning("🚀⚠️ [CSV] Rust CSV Parser missing. Falling back to slow Python parsing.")
    HAS_RUST_CSV = False

def Marker_convert_csv_unknow_report_to_csv(file_path):
    """
    Performs a 'best-effort' conversion of a CSV file with unknown headers
    to the standardized marker report format using the mandatory Rust parser.
    """
    matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"▶️ Starting best-effort CSV conversion for: {file_path}", "DEBUG")

    try:
        standard_headers, processed_data = rust_convert_csv_unknown(file_path)
        matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🚀 Using HIGH-PERFORMANCE RUST CSV parser.", "DEBUG")
        return standard_headers, processed_data
    except Exception as e:
        matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🚀❌ [FATAL] Rust CSV conversion failed: {e}", "ERROR")
        raise e
