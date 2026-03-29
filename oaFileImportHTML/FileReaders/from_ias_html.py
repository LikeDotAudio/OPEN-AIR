# FileReaders/from_ias_html.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Logic for converting IAS HTML frequency coordination reports into standardized marker format.

import re
import numpy as np
from bs4 import BeautifulSoup

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from loguru import logger
from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

# --- Constants ---
VERSION = "20251129.120000.1"
HEADERS = ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]

def convert_ias_html_to_markers(html_content):
    """
    Standardized entry point for HTML conversion.
    """
    return _internal_convert_ias_html_to_markers(html_content)

def Marker_convert_IAShtml_report_to_csv(html_content):
    """
    Backward compatibility alias.
    """
    return convert_ias_html_to_markers(html_content)

def _internal_convert_ias_html_to_markers(html_content):
    """
    Converts the HTML frequency coordination report into a list of dictionaries
    suitable for standardized marker format, handling multiple zones.
    All frequencies are converted to MHz for consistency.
    """

    logger.debug("▶️ Starting HTML report conversion.")

    soup = BeautifulSoup(html_content, "html.parser")
    data_rows = []

    # Find the main content area within the HTML
    main_content_container = None

    first_zone_p = soup.find(
        "p",
        style=lambda value: value
        and "font-size: large" in value
        and "text-decoration: underline" in value,
    )

    if first_zone_p:
        main_content_container = first_zone_p.find_parent("span")
        logger.debug(f"🔍 Found main content container based on first zone paragraph.")

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
                    logger.debug(f"🔍 Found main content container based on MainTable structure.")

    if not main_content_container:
        logger.debug("⚠️ Could not find the main content container. No data will be extracted.")
        return HEADERS, data_rows

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
                logger.debug(f"▶️ Processing Zone: {current_zone_type}")

        elif element.name == "table" and "Assignment" in element.get("class", []):
            table = element
            device_name_tag = table.find("th")
            current_group_name = (
                device_name_tag.get_text(strip=True) if device_name_tag else ""
            )
            logger.debug(f"▶️ Processing Group: {current_group_name}")

            rows_in_table = table.find_all("tr")[
                1:
            ]  # Skip the first row as it contains the <th> (device_name)

            if LOCAL_DEBUG: logger.debug(f"🔍 Found {len(rows_in_table)} rows in current table.")

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
                                    r"(\d+(?:\.\d+)?)\s*(?:(k|m|g)?hz)?",
                                    channel_frequency_str,
                                    re.IGNORECASE,
                                )
                                if freq_match:
                                    value = float(freq_match.group(1))
                                    unit_group = freq_match.group(2)
                                    if unit_group:
                                        unit = unit_group.lower()
                                        if unit == "m":
                                            freq_MHz = value
                                        elif unit == "g":
                                            freq_MHz = value * 1000  # GHz to MHz
                                        elif unit == "k":
                                            freq_MHz = value / 1000  # kHz to MHz
                                    else:
                                        freq_MHz = value
                                    if LOCAL_DEBUG: logger.debug(f"↔️ HTML Freq conversion: '{channel_frequency_str}' -> {freq_MHz} MHz")
                                else:
                                    freq_MHz = float(channel_frequency_str)
                                    if LOCAL_DEBUG: logger.debug(f"↔️ HTML Freq conversion (fallback): '{channel_frequency_str}' -> {freq_MHz} MHz")
                            except ValueError:
                                logger.error(f"❌ HTML Freq conversion error: '{channel_frequency_str}'")
                                freq_MHz = "Invalid Frequency"

                            row_data = {
                                "ZONE": current_zone_type,
                                "GROUP": current_group_name,
                                "DEVICE": band_type,
                                "NAME": channel_name,
                                "FREQ_MHZ": freq_MHz,
                                "PEAK": np.nan,
                            }
                            if band_type or channel_frequency_str or channel_name:
                                data_rows.append(row_data)
                                if LOCAL_DEBUG: logger.success(f"✅ Added HTML row: {row_data}")
                else:
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
                                unit_group = freq_match.group(2)
                                if unit_group:
                                    unit = unit_group.lower()
                                    if unit == "m":
                                        freq_MHz = value
                                    elif unit == "g":
                                        freq_MHz = value * 1000
                                    elif unit == "k":
                                        freq_MHz = value / 1000
                                else:
                                    freq_MHz = value
                                if LOCAL_DEBUG: logger.debug(f"↔️ HTML Freq conversion (direct td): '{channel_frequency_str}' -> {freq_MHz} MHz")
                            else:
                                freq_MHz = float(channel_frequency_str)
                                if LOCAL_DEBUG: logger.debug(f"↔️ HTML Freq conversion (direct td, fallback): '{channel_frequency_str}' -> {freq_MHz} MHz")
                        except ValueError:
                            logger.error(f"❌ HTML Freq conversion error (direct td): '{channel_frequency_str}'")
                            freq_MHz = "Invalid Frequency"

                        row_data = {
                            "ZONE": current_zone_type,
                            "GROUP": current_group_name,
                            "DEVICE": band_type,
                            "NAME": channel_name,
                            "FREQ_MHZ": freq_MHz,
                            "PEAK": np.nan,
                        }
                        if band_type or channel_frequency_str or channel_name:
                            data_rows.append(row_data)
                            if LOCAL_DEBUG: logger.success(f"✅ Added HTML row (direct td): {row_data}")

    if LOCAL_DEBUG: logger.success(f"✅ Finished HTML report conversion. Extracted {len(data_rows)} rows.")
    return HEADERS, data_rows
