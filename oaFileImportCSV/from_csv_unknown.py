# workers/importers/formats/from_csv_unknown.py
#
# Best-effort conversion of CSV files with unknown headers into standard marker format.
#

import csv
import re
import os

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from loguru import logger
from oaConfiguration.config_reader import Config

app_constants = Config.get_instance()

# --- Constants ---
VERSION = "20251129.120000.1"

def Marker_convert_csv_unknow_report_to_csv(file_path):
    """
    Performs a 'best-effort' conversion of a CSV file with unknown headers
    to the standardized marker report format.
    """
    logger.debug(f"▶️ Starting best-effort CSV conversion for: {file_path}")

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

        logger.success(f"✅ Finished best-effort conversion. Headers mapped: {header_map}")
        return standard_headers, processed_data

    except FileNotFoundError:
        logger.error(f"❌ The file '{file_path}' was not found.")
        return [], []
    except Exception:
        if LOCAL_DEBUG:
            logger.exception("❌ Error during best-effort CSV conversion")
        return [], []
