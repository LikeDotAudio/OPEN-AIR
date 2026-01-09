# formats/worker_importer_from_soundbase_pdf_v2.py
#
# This module contains the logic for converting Sound Base PDF files (version 2)
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
# Version 20250821.200641.1

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


# Parses a Sound Base PDF file (version 2 format) and extracts frequency data, converting it to a standardized CSV format.
# This function uses regex to identify ZONE and GROUP information, then extracts frequency-device pairs
# from the text content of the PDF.
# Inputs:
#     pdf_file_path (str): The full path to the PDF file.
# Outputs:
#     tuple: A tuple containing the standardized headers and a list of dictionaries,
#            where each dictionary represents a row of converted data.
def Marker_convert_SB_v2_PDF_File_report_to_csv(pdf_file_path):
    """
    Parses a PDF file (Sound Base v2 format) and extracts frequency data, converting it
    into a standardized CSV format.

    Args:
        pdf_file_path (str): The full path to the PDF file.

    Returns:
        tuple: A tuple containing:
               - headers (list): A list of strings representing the CSV header row.
               - csv_data (list): A list of dictionaries, where each dictionary
                                  represents a row of data with keys matching the headers.
    """
    current_function = inspect.currentframe().f_code.co_name

    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message=f"▶️ Starting PDF (Sound Base v2) report conversion for: {os.path.basename(pdf_file_path)}",
            file=current_file,
            version=current_version,
            function=f"{current_function}",
            **_get_log_args(),
        )

    csv_data = []

    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            text = pdf.pages[0].extract_text()

            # Use regex to find the ZONE
            zone_match = re.search(r"ZONE: (.+)", text)
            zone = zone_match.group(1).strip() if zone_match else "N/A"
            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🔍 Found ZONE: {zone}",
                    file=current_file,
                    version=current_version,
                    function=current_function,
                    **_get_log_args(),
                )

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
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"🔍 Found new GROUP: {current_group}",
                            file=current_file,
                            version=current_version,
                            function=current_function,
                            **_get_log_args(),
                        )
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
                            csv_data.append(
                                {
                                    "ZONE": zone,
                                    "GROUP": current_group,
                                    "DEVICE": device_clean,
                                    "NAME": device_clean,
                                    "FREQ_MHZ": freq_clean,
                                    "PEAK": np.nan,
                                }
                            )

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"✅ Finished conversion. Extracted {len(csv_data)} rows.",
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
        return [], []
    except Exception as e:
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"❌ Error during PDF conversion: {e}",
                file=current_file,
                version=current_version,
                function=current_function,
                **_get_log_args(),
            )
        return [], []