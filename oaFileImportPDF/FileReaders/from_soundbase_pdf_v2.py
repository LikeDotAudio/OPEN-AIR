import os

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# FileReaders/from_soundbase_pdf_v2.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Logic for converting Sound Base PDF files (version 2) into standardized marker format.

import re
import numpy as np
import pdfplumber

# --- Native Rust Optimization ---
try:
    from oaRustCore.oa_pdf_parser_rs import PDFEngine
    HAS_RUST_PARSER = True
    rust_pdf_engine = PDFEngine()
except Exception:
    HAS_RUST_PARSER = False

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False
from loguru import logger
from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

# --- Constants ---
VERSION = "20260402.0010.1"
HEADERS = ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]

def convert_soundbase_pdf_v2_to_markers(pdf_file_path):
    """
    Standardized entry point for SoundBase PDF V2 conversion.
    """
    return _internal_convert_soundbase_pdf_v2_to_markers(pdf_file_path)

def Marker_convert_SB_v2_PDF_File_report_to_csv(pdf_file_path):
    """
    Backward compatibility alias.
    """
    return convert_soundbase_pdf_v2_to_markers(pdf_file_path)

def _internal_convert_soundbase_pdf_v2_to_markers(pdf_file_path):
    """
    Parses a PDF file (Sound Base v2 format) and extracts frequency data, converting it
    into a standardized marker format.
    """

    if LOCAL_DEBUG:
        matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"▶️ Starting PDF (Sound Base v2) report conversion for: {os.path.basename(pdf_file_path)}", "DEBUG")

    marker_data = []

    try:
        text = ""
        # 1. Attempt High-Performance Rust Extraction
        if HAS_RUST_PARSER:
            try:
                text = rust_pdf_engine.extract_text(str(pdf_file_path))
                if LOCAL_DEBUG:
                    matrix_log("ui", "importer", "pdf_v2", "🦀 [RUST] Successfully extracted PDF text natively.", "DEBUG")
            except Exception as e:
                logger.warning(f"⚠️ [RUST] Native extraction failed, falling back to pdfplumber: {e}")

        # 2. Fallback to pdfplumber if Rust failed or is unavailable
        if not text:
            with pdfplumber.open(pdf_file_path) as pdf:
                text = pdf.pages[0].extract_text()
                if LOCAL_DEBUG:
                    matrix_log("ui", "importer", "pdf_v2", "🐍 [PYTHON] Extracted PDF text via pdfplumber.", "DEBUG")

        if not text:
            logger.error(f"❌ BlueprintLoader: Failed to extract text from {pdf_file_path}")
            return [], []

        # Use regex to find the ZONE
        zone_match = re.search(r"ZONE: (.+)", text)
        zone = zone_match.group(1).strip() if zone_match else "N/A"
        matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔍 Found ZONE: {zone}", "DEBUG")

        # The pattern to find all groups
        group_pattern = re.compile(
            r"^\s*([A-Z\s&]+ IEM\'S|[A-Z\s&]+ MICS & BACKLINE)\s*$", re.MULTILINE
        )

        lines = text.split("\n")
        current_group = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if the line is a new group header
            group_match = group_pattern.search(line)
            if group_match:
                current_group = group_match.group(1).strip()
                matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔍 Found new GROUP: {current_group}", "DEBUG")
                continue

            # Regex to find all frequency-device pairs on the current line
            device_matches = re.findall(
                r"(\d+\.\d+)\s+([\w\s-]+?(?=\s*\d+\.\d+|$))", line
            )

            if device_matches:
                for freq, device in device_matches:
                    device_clean = device.strip()
                    freq_clean = freq.strip()

                    if current_group:
                        marker_data.append(
                            {
                                "ZONE": zone,
                                "GROUP": current_group,
                                "DEVICE": device_clean,
                                "NAME": device_clean,
                                "FREQ_MHZ": freq_clean,
                                "PEAK": np.nan,
                            }
                        )

            if LOCAL_DEBUG:
                matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"✅ Finished conversion. Extracted {len(marker_data)} rows.", "SUCCESS")
            return HEADERS, marker_data

    except FileNotFoundError:
        logger.error(f"❌ The file '{pdf_file_path}' was not found.")
        return [], []
    except Exception:
        if LOCAL_DEBUG:
            logger.exception("❌ Error during PDF conversion")
        return [], []