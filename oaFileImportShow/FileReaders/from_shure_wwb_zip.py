# FileReaders/from_shure_wwb_zip.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: formats/worker_importer_from_shure_wwb_zip.py

import csv
import inspect
import io
import os
import re
import zipfile
import numpy as np

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

# --- Global Scope Variables ---
Current_Date = 20251129
Current_Time = 120000
Current_iteration = 1

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = Current_Date * Current_Time * Current_iteration

current_file = os.path.basename(__file__)

headers = ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]


# Parses a WWB .zip file, extracts relevant frequency data, and returns it in a standardized CSV format.
# This function extracts zone and group information from the zip filename, then processes
# any contained CSV files, assuming the first column represents frequency in MHz.
# Inputs:
#     file_path (str): The full path to the WWB .zip archive.
# Outputs:
#     tuple: A tuple containing the standardized headers and a list of dictionaries,
#            where each dictionary represents a row of converted data.
def Marker_convert_wwb_zip_report_to_csv(file_path):
    """
    Parses a WWB.zip file, extracts relevant information, and returns a standardized
    list of dictionaries.

    Args:
        file_path (str): The full path to the WWB.zip archive.

    Returns:
        tuple: A tuple containing:
               - headers (list): A list of strings representing the CSV header row.
               - csv_data (list): A list of dictionaries, where each dictionary
                                  represents a row of data with keys matching the headers.
    """
    if not file_path:
        logger.debug("🟡 No file path provided for zip conversion.", file=current_file,
            version=current_version)
        return [], []

    if LOCAL_DEBUG: logger.debug(f"▶️ Starting ZIP report conversion for: {os.path.basename(file_path)}",
        file=current_file,
        version=current_version)

    csv_data = []

    try:
        # Parse the zip filename to get ZONE and GROUP
        zip_filename_stem = os.path.splitext(os.path.basename(file_path))[0]
        # Example: 'Chase Rice 08-09-25_Main Stage Direct Support_wwb'
        zip_parts = re.split(r"_(?=\w+)", zip_filename_stem)

        # The ZONE is the first part, stripping the date part.
        zone = zip_parts[0] if len(zip_parts) > 0 else "N/A"

        # The main group is the second part, stripping the last two parts.
        group_match = re.search(r"([^_]+)_wwb$", zip_filename_stem)
        main_group = group_match.group(1).replace("_", " ") if group_match else "N/A"

        if LOCAL_DEBUG: logger.debug(f"🔍 Derived from ZIP filename: ZONE='{zone}', Main Group='{main_group}'")

        with zipfile.ZipFile(file_path, "r") as zip_ref:
            csv_files = [name for name in zip_ref.namelist() if name.endswith(".csv")]

            if not csv_files:
                logger.error("❌ No .csv file found inside the .zip archive.")
                logger.error("❌ No CSV file found within ZIP. Mission failed!", file=current_file,
                    version=current_version)
                return [], []

            if len(csv_files) > 1:
                if LOCAL_DEBUG: logger.debug(f"⚠️ Found multiple .csv files. Processing all of them.")
                logger.debug(f"⚠️ Found multiple CSV files. Processing all of them.",
                    file=current_file,
                    version=current_version)

            for csv_file_name in csv_files:
                # Parse the CSV filename for device and group
                csv_filename_stem = os.path.splitext(os.path.basename(csv_file_name))[0]
                csv_filename_parts = csv_filename_stem.split("_")

                device = csv_filename_parts[0] if len(csv_filename_parts) > 0 else "N/A"
                csv_group = (
                    csv_filename_parts[1] if len(csv_filename_parts) > 1 else "N/A"
                )

                with zip_ref.open(csv_file_name) as csv_in_zip:
                    csv_reader = csv.reader(io.TextIOWrapper(csv_in_zip, "utf-8"))

                    for row in csv_reader:
                        if not row:
                            continue

                        try:
                            # Assume the first column is the frequency in MHz
                            freq_mhz = float(row[0])

                            row_data = {
                                "ZONE": zone,
                                "GROUP": csv_group,
                                "DEVICE": device,
                                "NAME": "",  # The prompt says just the freq, so name can be empty or the freq itself.
                                "FREQ_MHZ": freq_mhz,
                                "PEAK": np.nan,
                            }
                            csv_data.append(row_data)
                            logger.success(f"✅ Added ZIP CSV row: {row_data}",
                                file=current_file,
                                version=current_version)
                        except (ValueError, IndexError):
                            # Skip rows that are not valid frequency data
                            logger.debug(f"⏩ Skipping non-frequency data row: {row}",
                                file=current_file,
                                version=current_version)

        if LOCAL_DEBUG: logger.success(f"✅ Extracted and converted {len(csv_files)} CSV files successfully!")
        return headers, csv_data

    except FileNotFoundError:
        logger.error(f"❌ The file '{file_path}' was not found.",
            file=current_file,
            version=current_version)
        return [], []
    except zipfile.BadZipFile:
        logger.error(f"❌ The file '{file_path}' is not a valid zip archive.",
            file=current_file,
            version=current_version)
        return [], []
    except Exception as e:
        if LOCAL_DEBUG:
            logger.exception("❌ Error converting ZIP file",
                file=current_file,
                version=current_version)
        return [], []
