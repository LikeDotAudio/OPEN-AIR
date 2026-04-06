# FileReaders/from_shure_wwb_zip.py
#
# Parses a Shure Wireless Workbench .zip archive, extracts relevant 
# frequency data, and returns it in a standardized marker format.
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
# Version 20260330.1600.1

import csv
import inspect
import io
import os
import re
import zipfile
import numpy as np
from loguru import logger
from oaLogging.Methods.matrix_gate import is_debug_allowed, matrix_log
from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

headers = ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]

def Marker_convert_wwb_zip_report_to_csv(file_path):
    """
    Parses a WWB.zip file, extracts relevant information, and returns a standardized
    list of dictionaries.
    """
    if not file_path:
        matrix_log("ui", "importer", "Marker_convert_wwb_zip_report_to_csv", 
                   "🟡 No file path provided for zip conversion.", "DEBUG")
        return [], []

    matrix_log("ui", "importer", "Marker_convert_wwb_zip_report_to_csv", 
               f"▶️ Starting ZIP report conversion for: {os.path.basename(file_path)}", "DEBUG")

    csv_data = []

    try:
        # Parse the zip filename to get ZONE and GROUP
        zip_filename_stem = os.path.splitext(os.path.basename(file_path))[0]
        zip_parts = re.split(r"_(?=\w+)", zip_filename_stem)

        zone = zip_parts[0] if len(zip_parts) > 0 else "N/A"

        group_match = re.search(r"([^_]+)_wwb$", zip_filename_stem)
        main_group = group_match.group(1).replace("_", " ") if group_match else "N/A"

        matrix_log("ui", "importer", "Marker_convert_wwb_zip_report_to_csv", 
                   f"🔍 Derived from ZIP filename: ZONE='{zone}', Main Group='{main_group}'", "DEBUG")

        with zipfile.ZipFile(file_path, "r") as zip_ref:
            csv_files = [name for name in zip_ref.namelist() if name.endswith(".csv")]

            if not csv_files:
                logger.error("❌ No .csv file found inside the .zip archive.")
                return [], []

            if len(csv_files) > 1:
                matrix_log("ui", "importer", "Marker_convert_wwb_zip_report_to_csv", 
                           "⚠️ Found multiple .csv files. Processing all of them.", "DEBUG")

            for csv_file_name in csv_files:
                csv_filename_stem = os.path.splitext(os.path.basename(csv_file_name))[0]
                csv_filename_parts = csv_filename_stem.split("_")

                device = csv_filename_parts[0] if len(csv_filename_parts) > 0 else "N/A"
                csv_group = csv_filename_parts[1] if len(csv_filename_parts) > 1 else "N/A"

                with zip_ref.open(csv_file_name) as csv_in_zip:
                    csv_reader = csv.reader(io.TextIOWrapper(csv_in_zip, "utf-8"))

                    for row in csv_reader:
                        if not row: continue
                        try:
                            freq_mhz = float(row[0])
                            row_data = {
                                "ZONE": zone, "GROUP": csv_group, "DEVICE": device,
                                "NAME": "", "FREQ_MHZ": freq_mhz, "PEAK": np.nan,
                            }
                            csv_data.append(row_data)
                            matrix_log("ui", "importer", "Marker_convert_wwb_zip_report_to_csv", 
                                       f"✅ Added ZIP CSV row: {row_data}", "SUCCESS")
                        except (ValueError, IndexError):
                            matrix_log("ui", "importer", "Marker_convert_wwb_zip_report_to_csv", 
                                       f"⏩ Skipping non-frequency data row: {row}", "TRACE")

        matrix_log("ui", "importer", "Marker_convert_wwb_zip_report_to_csv", 
                   f"✅ Extracted and converted {len(csv_files)} CSV files successfully!", "SUCCESS")
        return headers, csv_data

    except FileNotFoundError:
        logger.error(f"❌ The file '{file_path}' was not found.")
        return [], []
    except zipfile.BadZipFile:
        logger.error(f"❌ The file '{file_path}' is not a valid zip archive.")
        return [], []
    except Exception as e:
        logger.exception(f"❌ Error converting ZIP file: {e}")
        return [], []
