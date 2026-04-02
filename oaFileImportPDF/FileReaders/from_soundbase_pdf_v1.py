import os

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# FileReaders/from_soundbase_pdf_v1.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Logic for converting Sound Base PDF files (version 1) into standardized marker format.

import re
import numpy as np
import pdfplumber

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from loguru import logger
from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

# --- Constants ---
VERSION = "20251129.120000.1"
HEADERS = ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]

def convert_soundbase_pdf_v1_to_markers(pdf_file_path):
    """
    Standardized entry point for SoundBase PDF V1 conversion.
    """
    return _internal_convert_soundbase_pdf_v1_to_markers(pdf_file_path)

def Marker_convert_SB_PDF_File_report_to_csv(pdf_file_path):
    """
    Backward compatibility alias.
    """
    return convert_soundbase_pdf_v1_to_markers(pdf_file_path)

def _internal_convert_soundbase_pdf_v1_to_markers(pdf_file_path):
    """
    Parses a PDF file (Sound Base format v1) and extracts frequency data, converting it
    into a standardized marker format.
    """

    if LOCAL_DEBUG:
        matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"▶️ Starting PDF report conversion for '{os.path.basename(pdf_file_path)}'.", "DEBUG")

    marker_data = []

    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            last_known_group = "Uncategorized"  # Default group if not found

            if LOCAL_DEBUG:
                matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"📄 Opened PDF with {len(pdf.pages)} pages.", "DEBUG")

            for page_num, page in enumerate(pdf.pages):
                matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"▶️ Processing Page {page_num + 1}...", "DEBUG")
                
                # Extract text for group headers
                lines = page.extract_text().splitlines()
                lines = [line.strip() for line in lines if line.strip()]

                group_headers = [
                    (i, line)
                    for i, line in enumerate(lines)
                    if re.match(r".+\(\d+ frequencies\)", line)
                ]

                tables = page.extract_tables()
                if LOCAL_DEBUG:
                    matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🔍 Found {len(tables)} tables on Page {page_num + 1}.", "DEBUG")

                group_index = 0
                for table_num, table in enumerate(tables):
                    if group_index < len(group_headers):
                        last_known_group = group_headers[group_index][1]
                        group_index += 1

                    current_zone = last_known_group

                    matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"▶️ Processing Table {table_num + 1} for Zone: {current_zone}", "DEBUG")

                    for row_num, row in enumerate(table):
                        if not row or all(
                            cell is None or cell.strip() == "" for cell in row
                        ):
                            continue

                        if (
                            "Model" in row[0] and "Frequency" in row[-1]
                        ):  # Skip header rows
                            matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"⏩ Skipping header row: {row}", "DEBUG")
                            continue

                        clean_row = [
                            cell.replace("\n", " ").strip() if cell else ""
                            for cell in row
                        ]
                        # Ensure row has at least 6 elements to unpack safely
                        while len(clean_row) < 6:
                            clean_row.append("")

                        (
                            model_pdf,
                            band_pdf,
                            name_pdf,
                            preset_pdf,
                            spacing_pdf,
                            frequency_pdf_str,
                        ) = clean_row

                        if (
                            model_pdf.strip() == current_zone.strip()
                        ):  # Skip rows that mistakenly repeat the group name
                            matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"⏩ Skipping duplicate group name row: {row}", "DEBUG")
                            continue

                        # Map PDF fields to standard fields
                        zone_standard = current_zone
                        group_standard = model_pdf

                        # Construct DEVICE from PDF Model, Band, Preset
                        device_standard = f"{model_pdf}"
                        if band_pdf:
                            device_standard += f" - {band_pdf}"
                        if preset_pdf:
                            device_standard += f" - {preset_pdf}"

                        name_standard = name_pdf
                        freq_MHz_standard = "N/A"

                        try:
                            # The frequency is already in MHz, so no conversion needed
                            freq_MHz_standard = float(frequency_pdf_str)
                            if LOCAL_DEBUG:
                                matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"↔️ PDF Freq conversion: '{frequency_pdf_str}' -> {freq_MHz_standard} MHz", "DEBUG")
                        except ValueError:
                            logger.error(f"❌ PDF Freq conversion error: '{frequency_pdf_str}'")
                            freq_MHz_standard = "Invalid Frequency"

                        marker_data.append(
                            {
                                "ZONE": zone_standard,
                                "GROUP": group_standard,
                                "DEVICE": device_standard,
                                "NAME": name_standard,
                                "FREQ_MHZ": freq_MHz_standard,
                                "PEAK": np.nan,
                            }
                        )
                        if LOCAL_DEBUG:
                            matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"✅ Added PDF row: {marker_data[-1]}", "SUCCESS")

        if LOCAL_DEBUG:
            matrix_log("ui", "importer", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"✅ Finished PDF report conversion. Extracted {len(marker_data)} rows.", "SUCCESS")
        return HEADERS, marker_data

    except FileNotFoundError:
        logger.error(f"❌ The file '{pdf_file_path}' was not found.")
        raise FileNotFoundError(f"The file '{pdf_file_path}' was not found.")
    except Exception:
        if LOCAL_DEBUG:
            logger.exception("❌ Error during PDF conversion data extraction")
        raise