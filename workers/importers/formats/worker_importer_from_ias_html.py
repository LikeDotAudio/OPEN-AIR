# workers/importers/worker_importer_ias_html.py
#
# This file contains the logic for converting IAS HTML frequency coordination reports
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
from bs4 import BeautifulSoup

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


def Marker_convert_IAShtml_report_to_csv(html_content):
    """
    Converts the HTML frequency coordination report into a list of dictionaries
    suitable for CSV output, handling multiple zones. This version is based on
    the IAS HTML to CSV.py prototype for accurate extraction.
    All frequencies are converted to MHz for consistency.

    Inputs:
        html_content (str): The full HTML content of the report.

    Returns:
        tuple: A tuple containing:
               - list: A list of strings representing the CSV headers.
               - list: A list of dictionaries, where each dictionary represents a row
                       in the CSV and keys are column headers.
    """

    current_function = inspect.currentframe().f_code.co_name

    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message="▶️ Starting HTML report conversion.",
            file=current_file,
            version=current_version,
            function=current_function,
            **_get_log_args(),
        )

    soup = BeautifulSoup(html_content, "html.parser")

    data_rows = []

    # Find the main content area within the HTML, based on the IAS prototype.
    main_content_container = None

    first_zone_p = soup.find(
        "p",
        style=lambda value: value
        and "font-size: large" in value
        and "text-decoration: underline" in value,
    )

    if first_zone_p:
        main_content_container = first_zone_p.find_parent("span")

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message=f"🔍 Found main content container based on first zone paragraph.",
                file=current_file,
                version=current_version,
                function=current_function,
                **_get_log_args(),
            )

    if not main_content_container:
        main_table = soup.find("table", class_="MainTable")
        if main_table:
            main_table_trs = main_table.find_all("tr")
            if len(main_table_trs) > 1:
                second_tr_td = main_table_trs[1].find("td")
                if second_tr_td:
                    potential_span_wrapper = second_tr_td.find("span")
                    if potential_span_wrapper:
                        main_content_container = potential_span_wrapper
                    else:
                        main_content_container = second_tr_td

                    if app_constants.global_settings["debug_enabled"]:
                        debug_logger(
                            message=f"🔍 Found main content container based on MainTable structure.",
                            file=current_file,
                            version=current_version,
                            function=current_function,
                            **_get_log_args(),
                        )

    if not main_content_container:

        if app_constants.global_settings["debug_enabled"]:
            debug_logger(
                message="⚠️ Could not find the main content container. No data will be extracted.",
                file=current_file,
                version=current_version,
                function=current_function,
                **_get_log_args(),
            )
        return headers, data_rows

    current_zone_type = ""
    # Iterate through the children of the identified main content container
    for element in main_content_container.children:
        if (
            element.name == "p"
            and element.get("style")
            and "font-size: large" in element.get("style")
            and "text-decoration: underline" in element.get("style")
        ):
            zone_text = element.get_text(strip=True)
            if zone_text.startswith("Zone:"):
                current_zone_type = zone_text.replace("Zone:", "").strip()

                if app_constants.global_settings["debug_enabled"]:
                    debug_logger(
                        message=f"▶️ Processing Zone: {current_zone_type}",
                        file=current_file,
                        version=current_version,
                        function=current_function,
                        **_get_log_args(),
                    )

        elif element.name == "table" and "Assignment" in element.get("class", []):
            table = element

            device_name_tag = table.find("th")
            current_group_name = (
                device_name_tag.get_text(strip=True) if device_name_tag else ""
            )

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"▶️ Processing Group: {current_group_name}",
                    file=current_file,
                    version=current_version,
                    function=current_function,
                    **_get_log_args(),
                )

            rows_in_table = table.find_all("tr")[
                1:
            ]  # Skip the first row as it contains the <th> (device_name)

            if app_constants.global_settings["debug_enabled"]:
                debug_logger(
                    message=f"🔍 Found {len(rows_in_table)} rows in current table.",
                    file=current_file,
                    version=current_version,
                    function=current_function,
                    **_get_log_args(),
                )

            for row in rows_in_table:
                data_spans = row.find_all("span")

                if data_spans:
                    for data_span in data_spans:
                        cells = data_span.find_all("td")
                        if len(cells) >= 4:
                            band_type = cells[0].get_text(strip=True)

                            channel_frequency_tag = cells[3].find("b")
                            channel_frequency_str = (
                                channel_frequency_tag.get_text(strip=True)
                                if channel_frequency_tag
                                else ""
                            )

                            channel_name = cells[1].get_text(strip=True)
                            if not channel_name:
                                channel_name = cells[2].get_text(strip=True)

                            # Convert frequency string to MHz
                            freq_MHz = "N/A"
                            try:
                                freq_match = re.search(
                                    r"(\d+(\.\d+)?)\s*(kHz|MHz|GHz)",
                                    channel_frequency_str,
                                    re.IGNORECASE,
                                )
                                if freq_match:
                                    value = float(freq_match.group(1))
                                    unit = freq_match.group(3).lower()
                                    if unit == "mhz":
                                        freq_MHz = value
                                    elif unit == "ghz":
                                        freq_MHz = value * 1000  # GHz to MHz
                                    elif unit == "khz":
                                        freq_MHz = value / 1000  # kHz to MHz
                                    if app_constants.global_settings["debug_enabled"]:
                                        debug_logger(
                                            message=f"↔️ HTML Freq conversion: '{channel_frequency_str}' -> {freq_MHz} MHz",
                                            file=current_file,
                                            version=current_version,
                                            function=current_function,
                                            **_get_log_args(),
                                        )
                                else:
                                    # Fallback if regex doesn't match, assume MHz
                                    freq_MHz = float(
                                        channel_frequency_str
                                    )  # Assume it's already in MHz

                                    if app_constants.global_settings["debug_enabled"]:
                                        debug_logger(
                                            message=f"↔️ HTML Freq conversion (fallback): '{channel_frequency_str}' -> {freq_MHz} MHz",
                                            file=current_file,
                                            version=current_version,
                                            function=current_function,
                                            **_get_log_args(),
                                        )
                            except ValueError:

                                if app_constants.global_settings["debug_enabled"]:
                                    debug_logger(
                                        message=f"❌ HTML Freq conversion error: '{channel_frequency_str}'",
                                        file=current_file,
                                        version=current_version,
                                        function=current_function,
                                        **_get_log_args(),
                                    )
                                freq_MHz = "Invalid Frequency"

                            row_data = {
                                "ZONE": current_zone_type,
                                "GROUP": current_group_name,
                                "DEVICE": band_type,
                                "NAME": channel_name,
                                "FREQ_MHZ": freq_MHz,  # Store in MHz
                                "PEAK": np.nan,  # NEW: Added Peak column
                            }
                            if band_type or channel_frequency_str or channel_name:
                                data_rows.append(row_data)

                            if app_constants.global_settings["debug_enabled"]:
                                debug_logger(
                                    message=f"✅ Added HTML row: {row_data}",
                                    file=current_file,
                                    version=current_version,
                                    function=current_function,
                                    **_get_log_args(),
                                )
                else:
                    # Process rows that have <td>s directly (e.g., blank rows or specific structures without inner spans)
                    cells = row.find_all("td")
                    if len(cells) >= 4:
                        band_type = cells[0].get_text(strip=True)
                        channel_frequency_tag = cells[3].find("b")
                        channel_frequency_str = (
                            channel_frequency_tag.get_text(strip=True)
                            if channel_frequency_tag
                            else ""
                        )

                        channel_name = cells[1].get_text(strip=True)

                        if not channel_name:
                            channel_name = cells[2].get_text(strip=True)

                        # Convert frequency string to MHz
                        freq_MHz = "N/A"
                        try:
                            freq_match = re.search(
                                r"(\d+(?:\.\d+)?)\s*(?:(k|m|g)?hz)?",
                                channel_frequency_str,
                                re.IGNORECASE,
                            )
                            if freq_match:
                                value = float(freq_match.group(1))
                                unit_group = freq_match.group(
                                    2
                                )  # FIX: Changed from group(3) to group(2) to match regex changes
                                if unit_group:
                                    unit = unit_group.lower()
                                    if unit == "m":  # MHz
                                        freq_MHz = value
                                    elif unit == "g":  # GHz
                                        freq_MHz = value * 1000
                                    elif unit == "k":  # kHz
                                        freq_MHz = value / 1000
                                else:  # No unit specified, assume MHz
                                    freq_MHz = value
                                if app_constants.global_settings["debug_enabled"]:
                                    debug_logger(
                                        message=f"↔️ HTML Freq conversion (direct td): '{channel_frequency_str}' -> {freq_MHz} MHz",
                                        file=current_file,
                                        version=current_version,
                                        function=current_function,
                                        **_get_log_args(),
                                    )
                            else:
                                # Fallback if regex doesn't match, assume MHz
                                freq_MHz = float(
                                    channel_frequency_str
                                )  # Assume it's already in MHz

                                if app_constants.global_settings["debug_enabled"]:
                                    debug_logger(
                                        message=f"↔️ HTML Freq conversion (direct td, fallback): '{channel_frequency_str}' -> {freq_MHz} MHz",
                                        file=current_file,
                                        version=current_version,
                                        function=current_function,
                                        **_get_log_args(),
                                    )
                        except ValueError:

                            if app_constants.global_settings["debug_enabled"]:
                                debug_logger(
                                    message=f"❌ HTML Freq conversion error (direct td): '{channel_frequency_str}'",
                                    file=current_file,
                                    version=current_version,
                                    function=current_function,
                                    **_get_log_args(),
                                )
                            freq_MHz = "Invalid Frequency"

                        row_data = {
                            "ZONE": current_zone_type,
                            "GROUP": current_group_name,
                            "DEVICE": band_type,
                            "NAME": channel_name,
                            "FREQ_MHZ": freq_MHz,  # Store in MHz
                            "PEAK": np.nan,  # NEW: Added Peak column
                        }
                        if band_type or channel_frequency_str or channel_name:
                            data_rows.append(row_data)
                            if app_constants.global_settings["debug_enabled"]:
                                debug_logger(
                                    message=f"✅ Added HTML row (direct td): {row_data}",
                                    file=current_file,
                                    version=current_version,
                                    function=current_function,
                                    **_get_log_args(),
                                )

    if app_constants.global_settings["debug_enabled"]:
        debug_logger(
            message=f"✅ Finished HTML report conversion. Extracted {len(data_rows)} rows.",
            file=current_file,
            version=current_version,
            function=current_function,
            **_get_log_args(),
        )
    return headers, data_rows
