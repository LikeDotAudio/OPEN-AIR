# workers/importers/worker_importer_sb_pdf_v1.py
#
# This file contains the logic for converting Sound Base PDF files (version 1)
# into a standardized CSV format.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20251129.120000.1

import inspect
import os
import re
import numpy as np
import pdfplumber

from managers.configini.config_reader import Config
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

# --- Global Scope Variables ---
Current_Date = 20251129
Current_Time = 120000
Current_iteration = 1

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = Current_Date * Current_Time * Current_iteration

current_file = os.path.basename(__file__)
app_constants = Config.get_instance()

headers = ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]


def Marker_convert_SB_PDF_File_report_to_csv(pdf_file_path):
    """
    Parses a PDF file (Sound Base format) and extracts frequency data, converting it
    into a standardized CSV format. This function maps PDF fields to the MARKERS.CSV
    structure as follows:
    - PDF 'Group' -> CSV 'ZONE'
    - PDF 'Model' -> CSV 'GROUP'
    - PDF 'Name' -> CSV 'NAME'
    - PDF 'Frequency' -> CSV 'FREQ' (in MHz)
    - CSV 'DEVICE' is constructed from PDF 'Model', 'Band', and 'Preset'.

    Inputs:
        pdf_file_path (str): The full path to the PDF file.
        console_print_func (function, optional): A function to use for printing messages
                                                 to the console. If None, uses standard print.
    Outputs:
        tuple: A tuple containing:
               - headers (list): A list of strings representing the CSV header row.
               - csv_data (list): A list of dictionaries, where each dictionary
                                  represents a row of data with keys matching the headers.
    Raises:
        FileNotFoundError: If the specified PDF file does not exist.
        Exception: For other parsing or data extraction errors.
    """

    current_function = inspect.currentframe().f_code.co_name

    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message=f"▶️ Starting PDF report conversion for '{os.path.basename(pdf_file_path)}'.",
            file=current_file,
            version=current_version,
            function=current_function,
            **_get_log_args(),
        )

    csv_data = []

    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            last_known_group = "Uncategorized"  # Default group if not found

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"📄 Opened PDF with {len(pdf.pages)} pages.",
                    file=current_file,
                    version=current_version,
                    function=current_function,
                    **_get_log_args(),
                )

            for page_num, page in enumerate(pdf.pages):

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"▶️ Processing Page {page_num + 1}...",
                        file=current_file,
                        version=current_version,
                        function=current_function,
                        **_get_log_args(),
                    )
                # Extract text for group headers
                lines = page.extract_text().splitlines()
                lines = [line.strip() for line in lines if line.strip()]

                group_headers = [
                    (i, line)
                    for i, line in enumerate(lines)
                    if re.match(r".+\(\d+ frequencies\)", line)
                ]

                tables = page.extract_tables()
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🔍 Found {len(tables)} tables on Page {page_num + 1}.",
                        file=current_file,
                        version=current_version,
                        function=current_function,
                        **_get_log_args(),
                    )

                group_index = 0
                for table_num, table in enumerate(tables):
                    if group_index < len(group_headers):
                        last_known_group = group_headers[group_index][1]
                        group_index += 1

                    current_zone = last_known_group  # PDF Group -> CSV ZONE

                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"▶️ Processing Table {table_num + 1} for Zone: {current_zone}",
                            file=current_file,
                            version=current_version,
                            function=current_function,
                            **_get_log_args(),
                        )

                    for row_num, row in enumerate(table):
                        if not row or all(
                            cell is None or cell.strip() == "" for cell in row
                        ):
                            continue

                        if (
                            "Model" in row[0] and "Frequency" in row[-1]
                        ):  # Skip header rows
                            if app_constants.global_settings["debug_enabled"]:
                                debug_logger(
                                    message=f"⏩ Skipping header row: {row}",
                                    file=current_file,
                                    version=current_version,
                                    function=current_function,
                                    **_get_log_args(),
                                )
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
                            if app_constants.global_settings["debug_enabled"]:
                                debug_logger(
                                    message=f"⏩ Skipping duplicate group name row: {row}",
                                    file=current_file,
                                    version=current_version,
                                    function=current_function,
                                    **_get_log_args(),
                                )
                            continue

                        # Map PDF fields to CSV fields
                        zone_csv = current_zone
                        group_csv = model_pdf  # PDF Model -> CSV GROUP

                        # Construct DEVICE from PDF Model, Band, Preset
                        device_csv = f"{model_pdf}"
                        if band_pdf:
                            device_csv += f" - {band_pdf}"
                        if preset_pdf:
                            device_csv += f" - {preset_pdf}"

                        name_csv = name_pdf  # PDF Name -> CSV NAME

                        freq_MHz_csv = "N/A"

                        try:
                            # The frequency is already in MHz, so no conversion needed
                            freq_MHz_csv = float(frequency_pdf_str)
                            if app_constants.global_settings["debug_enabled"]:
                                debug_logger(
                                    message=f"↔️ PDF Freq conversion: '{frequency_pdf_str}' -> {freq_MHz_csv} MHz",
                                    file=current_file,
                                    version=current_version,
                                    function=current_function,
                                    **_get_log_args(),
                                )
                        except ValueError:

                            if app_constants.global_settings["debug_enabled"]:
                                debug_logger(
                                    message=f"❌ PDF Freq conversion error: '{frequency_pdf_str}'",
                                    file=current_file,
                                    version=current_version,
                                    function=current_function,
                                    **_get_log_args(),
                                )
                            freq_MHz_csv = "Invalid Frequency"

                        csv_data.append(
                            {
                                "ZONE": zone_csv,
                                "GROUP": group_csv,
                                "DEVICE": device_csv,
                                "NAME": name_csv,
                                "FREQ_MHZ": freq_MHz_csv,
                                "PEAK": np.nan,  # NEW: Added Peak column
                            }
                        )
                        if app_constants.global_settings["debug_enabled"]:
                            debug_logger(
                                message=f"✅ Added PDF row: {csv_data[-1]}",
                                file=current_file,
                                version=current_version,
                                function=current_function,
                                **_get_log_args(),
                            )

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"✅ Finished PDF report conversion. Extracted {len(csv_data)} rows.",
                file=current_file,
                version=current_version,
                function=current_function,
                **_get_log_args(),
            )
        return headers, csv_data

    except FileNotFoundError:

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"❌ The file '{pdf_file_path}' was not found.",
                file=current_file,
                version=current_version,
                function=current_function,
                **_get_log_args(),
            )
        raise FileNotFoundError(f"The file '{pdf_file_path}' was not found.")
    except Exception as e:

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"❌ Error during PDF conversion data extraction: {e}",
                file=current_file,
                version=current_version,
                function=current_function,
                **_get_log_args(),
            )
        raise
