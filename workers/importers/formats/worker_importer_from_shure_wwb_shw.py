# formats/worker_importer_from_shure_wwb_shw.py
#
# This module contains the logic for converting WWB .shw (XML) files
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
import xml.etree.ElementTree as ET
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


# Parses an SHW (XML) file and extracts frequency data, converting it into a standardized CSV format.
# This function extracts zone, group, device, name, and frequency from the XML structure,
# converting all frequencies to MHz for consistency.
# Inputs:
#     xml_file_path (str): The full path to the SHW (XML) file.
# Outputs:
#     tuple: A tuple containing the standardized headers and a list of dictionaries,
#            where each dictionary represents a row of converted data.
# Raises:
#     FileNotFoundError: If the specified XML file does not exist.
#     xml.etree.ElementTree.ParseError: If the XML file is malformed.
#     Exception: For other parsing or data extraction errors.
def Marker_convert_WWB_SHW_File_report_to_csv(xml_file_path):
    """
    Parses an SHW (XML) file and extracts frequency data, converting it
    into a standardized CSV format. This version is based on the SHOW to CSV.py
    prototype for accurate extraction of ZONE and GROUP.
    All frequencies are converted to MHz for consistency.

    Inputs:
        xml_file_path (str): The full path to the SHW (XML) file.
        console_print_func (function, optional): A function to use for printing messages
                                                 to the console. If None, uses standard print.
    Outputs:
        tuple: A tuple containing:
               - headers (list): A list of strings representing the CSV header row.
               - csv_data (list): A list of dictionaries, where each dictionary
                                  represents a row of data with keys matching the headers.
    Raises:
        FileNotFoundError: If the specified XML file does not exist.
        xml.etree.ElementTree.ParseError: If the XML file is malformed.
        Exception: For other parsing or data extraction errors.
    """

    current_function = inspect.currentframe().f_code.co_name

    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message=f"▶️ Starting SHW report conversion for '{os.path.basename(xml_file_path)}'.",
            file=current_file,
            version=current_version,
            function=current_function,
            **_get_log_args(),
        )

    csv_data = []

    try:
        with open(xml_file_path, "r", encoding="utf-8") as f:
            tree = ET.parse(f)
        root = tree.getroot()

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="✅ XML file parsed successfully.",
                file=current_file,
                version=current_version,
                function=current_function,
                **_get_log_args(),
            )

        # Iterate through 'freq_entry' elements
        for i, freq_entry in enumerate(root.findall(".//freq_entry")):
            if i % 100 == 0:  # Print progress every 100 entries

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"▶️ Processing SHW entry {i}...",
                        file=current_file,
                        version=current_version,
                        function=current_function,
                        **_get_log_args(),
                    )

            # Reverting ZONE and GROUP extraction to match SHOW to CSV.py prototype
            zone_element = freq_entry.find("compat_key/zone")
            zone = zone_element.text if zone_element is not None else "N/A"

            group = freq_entry.get(
                "tag", "N/A"
            )  # Extract GROUP from the 'tag' attribute of freq_entry

            # Extract DEVICE (manufacturer, model, band)
            manufacturer = (
                freq_entry.find("manufacturer").text
                if freq_entry.find("manufacturer") is not None
                else "N/A"
            )
            model = (
                freq_entry.find("model").text
                if freq_entry.find("model") is not None
                else "N/A"
            )
            band_element = freq_entry.find("compat_key/band")
            band = band_element.text if band_element is not None else "N/A"
            device = f"{manufacturer} - {model} - {band}"

            # Extract NAME
            name_element = freq_entry.find("source_name")
            name = name_element.text if name_element is not None else "N/A"

            # Extract FREQ from value. User states SHW files contain markers in KHZ.
            freq_element = freq_entry.find("value")
            freq_MHz = "N/A"
            if freq_element is not None and freq_element.text is not None:
                freq_str = freq_element.text

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"🔍 DEBUG (SHW): Processing freq_str: '{freq_str}' for device '{name}'",
                        file=current_file,
                        version=current_version,
                        function=current_function,
                        **_get_log_args(),
                    )

                try:
                    # Convert kHz to MHz as per user's clarification
                    freq_MHz = float(freq_str) / 1000.0
                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"↔️ SHW Freq conversion: '{freq_str}' kHz -> {freq_MHz} MHz",
                            file=current_file,
                            version=current_version,
                            function=current_function,
                            **_get_log_args(),
                        )
                except ValueError:

                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"❌ SHW Freq conversion error: '{freq_str}'",
                            file=current_file,
                            version=current_version,
                            function=current_function,
                            **_get_log_args(),
                        )
                    freq_MHz = "Invalid Frequency"

            csv_data.append(
                {
                    "ZONE": zone,
                    "GROUP": group,
                    "DEVICE": device,
                    "NAME": name,
                    "FREQ_MHZ": freq_MHz,  # Store in MHz
                    "PEAK": np.nan,  # NEW: Added Peak column
                }
            )

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"✅ Finished SHW report conversion. Extracted {len(csv_data)} rows.",
                file=current_file,
                version=current_version,
                function=current_function,
                **_get_log_args(),
            )
        return headers, csv_data

    except FileNotFoundError:

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"❌ The file '{xml_file_path}' was not found.",
                file=current_file,
                version=current_version,
                function=current_function,
                **_get_log_args(),
            )
        raise FileNotFoundError(f"The file '{xml_file_path}' was not found.")
    except ET.ParseError as e:

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"❌ Malformed XML (SHW) file '{xml_file_path}': {e}",
                file=current_file,
                version=current_version,
                function=current_function,
                **_get_log_args(),
            )
        raise ET.ParseError(f"🔴 ERROR parsing XML (SHW) file '{xml_file_path}': {e}")
    except Exception as e:

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"❌ Error during SHW conversion data extraction: {e}",
                file=current_file,
                version=current_version,
                function=current_function,
                **_get_log_args(),
            )
        raise