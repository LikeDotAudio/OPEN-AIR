# workers/importers/worker_importer_wwb_zip.py
#
# This file contains the logic for converting WWB .zip files
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

import csv
import inspect
import io
import os
import re
import zipfile
import numpy as np

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
    current_function = inspect.currentframe().f_code.co_name

    if not file_path:
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="🟡 No file path provided for zip conversion.",
                file=current_file,
                version=current_version,
                function=f"{current_function}",
                **_get_log_args(),
            )
        return [], []

    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message=f"▶️ Starting ZIP report conversion for: {os.path.basename(file_path)}",
            file=current_file,
            version=current_version,
            function=f"{current_function}",
            **_get_log_args(),
        )

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

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔍 Derived from ZIP filename: ZONE='{zone}', Main Group='{main_group}'",
                **_get_log_args(),
            )

        with zipfile.ZipFile(file_path, "r") as zip_ref:
            csv_files = [name for name in zip_ref.namelist() if name.endswith(".csv")]

            if not csv_files:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message="❌ No .csv file found inside the .zip archive.",
                        **_get_log_args(),
                    )
                    debug_logger(
                        message="❌ No CSV file found within ZIP. Mission failed!",
                        file=current_file,
                        version=current_version,
                        function=f"{current_function}",
                        **_get_log_args(),
                    )
                return [], []

            if len(csv_files) > 1:
                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"⚠️ Found multiple .csv files. Processing all of them.",
                        **_get_log_args(),
                    )
                    debug_logger(
                        message=f"⚠️ Found multiple CSV files. Processing all of them.",
                        file=current_file,
                        version=current_version,
                        function=f"{current_function}",
                        **_get_log_args(),
                    )

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
                            if app_constants.global_settings["debug_enabled"]:
                                debug_logger(
                                    message=f"✅ Added ZIP CSV row: {row_data}",
                                    file=current_file,
                                    version=current_version,
                                    function=f"{current_function}",
                                    **_get_log_args(),
                                )
                        except (ValueError, IndexError):
                            # Skip rows that are not valid frequency data
                            if app_constants.global_settings["debug_enabled"]:
                                debug_logger(
                                    message=f"⏩ Skipping non-frequency data row: {row}",
                                    file=current_file,
                                    version=current_version,
                                    function=f"{current_function}",
                                    **_get_log_args(),
                                )

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"✅ Extracted and converted {len(csv_files)} CSV files successfully!",
                **_get_log_args(),
            )
        return headers, csv_data

    except FileNotFoundError:
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"❌ The file '{file_path}' was not found.",
                file=current_file,
                version=current_version,
                function=current_function,
                **_get_log_args(),
            )
        return [], []
    except zipfile.BadZipFile:
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"❌ The file '{file_path}' is not a valid zip archive.",
                file=current_file,
                version=current_version,
                function=f"{current_function}",
                **_get_log_args(),
            )
        return [], []
    except Exception as e:
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"❌ Error converting ZIP file: {e}",
                file=current_file,
                version=current_version,
                function=f"{current_function}",
                **_get_log_args(),
            )
        return [], []
