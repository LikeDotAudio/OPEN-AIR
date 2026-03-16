# formats/worker_importer_from_csv_unknown.py
#
# This module contains the logic for a 'best-effort' conversion of CSV files
# with unknown headers into the standardized marker report format.
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

import csv
import inspect
import re
import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

# --- Global Scope Variables ---
Current_Date = 20251129
Current_Time = 120000
Current_iteration = 1

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = Current_Date * Current_Time * Current_iteration

current_file = os.path.basename(__file__)

headers = ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]


# Performs a 'best-effort' conversion of a CSV file with unknown headers to the standardized marker report format.
# This function attempts to map column headers from the input CSV to a predefined set of
# standard headers (ZONE, GROUP, DEVICE, NAME, FREQ_MHZ, PEAK) and converts frequency values
# to MHz as needed.
# Inputs:
#     file_path (str): The path to the input CSV file.
# Outputs:
#     tuple: A tuple containing the standardized headers and a list of dictionaries
#            with the matched data. Returns empty lists on error or file not found.
def Marker_convert_csv_unknow_report_to_csv(file_path):
    """
    Performs a 'best-effort' conversion of a CSV file with unknown headers
    to the standardized marker report format.

    Args:
        file_path (str): The path to the input CSV file.

    Returns:
        tuple: A tuple containing the standardized headers and a list of
               dictionaries with the matched data.
    """
    logger.debug(f"▶️ Starting best-effort CSV conversion for: {file_path}",
        file=current_file,
        version=current_version)

    # Standardized headers and their common aliases
    standard_headers = ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]
    header_aliases = {
        "zone": ["zone", "area", "location"],
        "group": ["group", "channel_group"],
        "device": ["device", "dev_type", "model"],
        "name": ["name", "alias", "description"],
        "FREQ_MHZ": ["freq", "frequency", "frequency_mhz", "FREQ_MHZ"],
        "peak": ["peak", "peak_level", "max_level", "dbm"],
    }

    try:
        with open(file_path, "r", newline="") as csvfile:
            reader = csv.reader(csvfile)
            try:
                input_headers = [h.strip().lower() for h in next(reader)]
            except StopIteration:
                return [], []
            data = list(reader)

        header_map = {}
        for std_header in standard_headers:
            aliases = header_aliases.get(std_header.lower(), [std_header.lower()])
            for alias in aliases:
                if alias in input_headers:
                    header_map[std_header] = input_headers.index(alias)
                    break

        processed_data = []
        for row in data:
            new_row = {header: None for header in standard_headers}

            for std_header, index in header_map.items():
                if index < len(row):
                    value = row[index].strip()
                    if std_header.lower() == "FREQ_MHZ" and value:
                        try:
                            # Attempt to convert to MHz if needed
                            match = re.search(
                                r"(\d+(?:\.\d+)?)\s*(?:(k|m|g)?hz)?",
                                value,
                                re.IGNORECASE,
                            )
                            if match:
                                val = float(match.group(1))
                                unit = match.group(2)
                                if unit and unit.lower() == "k":
                                    val /= 1000
                                elif unit and unit.lower() == "g":
                                    val *= 1000
                                new_row[std_header] = val

                            else:
                                new_row[std_header] = float(value)
                        except ValueError:
                            new_row[std_header] = value
                    else:
                        new_row[std_header] = value
            processed_data.append(new_row)

        logger.success(f"✅ Finished best-effort conversion. Headers mapped: {header_map}",
            file=current_file,
            version=current_version)
        return standard_headers, processed_data

    except FileNotFoundError:
        logger.error(f"❌ The file '{file_path}' was not found.",
            file=current_file,
            version=current_version)
        return [], []
    except Exception as e:
        if LOCAL_DEBUG:
            logger.exception("❌ Error during best-effort CSV conversion",
                file=current_file,
                version=current_version)
        return [], []
