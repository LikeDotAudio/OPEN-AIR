# workers/importers/worker_importer_csv_unknown.py
#
# This file contains the logic for a 'best-effort' conversion of CSV files
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
# Version 20251129.120000.1

import csv
import inspect
import re
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
    current_function = inspect.currentframe().f_code.co_name
    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message=f"▶️ Starting best-effort CSV conversion for: {file_path}",
            file=current_file,
            version=current_version,
            function=current_function,
            **_get_log_args(),
        )

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
            input_headers = [h.strip().lower() for h in next(reader)]
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

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"✅ Finished best-effort conversion. Headers mapped: {header_map}",
                file=current_file,
                version=current_version,
                function=current_function,
                **_get_log_args(),
            )
        return standard_headers, processed_data

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
    except Exception as e:
        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"❌ Error during best-effort CSV conversion: {e}",
                file=current_file,
                version=current_version,
                function=current_function,
                **_get_log_args(),
            )
        return [], []
