# workers/importers/formats/from_shure_wwb_shw.py
#
# Logic for converting Shure Wireless Workbench .shw (XML) files into standardized marker format.
#

import os
import xml.etree.ElementTree as ET
import numpy as np

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from loguru import logger
from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

# --- Constants ---
VERSION = "20251129.120000.1"
HEADERS = ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]

def convert_shure_wwb_shw_to_markers(xml_file_path):
    """
    Parses an SHW (XML) file and extracts frequency data, converting it
    into a standardized marker format. All frequencies are converted to MHz for consistency.
    """

    if LOCAL_DEBUG:
        logger.debug(f"▶️ Starting SHW report conversion for '{os.path.basename(xml_file_path)}'.")

    marker_data = []

    try:
        with open(xml_file_path, "r", encoding="utf-8") as xml_file:
            tree = ET.parse(xml_file)
        root = tree.getroot()

        logger.success("✅ XML file parsed successfully.")

        # Iterate through 'freq_entry' elements
        for i, freq_entry in enumerate(root.findall(".//freq_entry")):
            if i % 100 == 0:  # Print progress every 100 entries
                logger.debug(f"▶️ Processing SHW entry {i}...")

            zone_element = freq_entry.find("compat_key/zone")
            zone = zone_element.text if zone_element is not None else "N/A"

            group = freq_entry.get("tag", "N/A")

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

            # Extract FREQ from value (WWB SHW files usually contain markers in kHz)
            freq_element = freq_entry.find("value")
            freq_MHz = "N/A"
            if freq_element is not None and freq_element.text is not None:
                freq_str = freq_element.text
                try:
                    # Convert kHz to MHz
                    freq_MHz = float(freq_str) / 1000.0
                    if LOCAL_DEBUG:
                        logger.debug(f"↔️ SHW Freq conversion: '{freq_str}' kHz -> {freq_MHz} MHz")
                except ValueError:
                    logger.error(f"❌ SHW Freq conversion error: '{freq_str}'")
                    freq_MHz = "Invalid Frequency"

            marker_data.append(
                {
                    "ZONE": zone,
                    "GROUP": group,
                    "DEVICE": device,
                    "NAME": name,
                    "FREQ_MHZ": freq_MHz,
                    "PEAK": np.nan,
                }
            )

        if LOCAL_DEBUG:
            logger.success(f"✅ Finished SHW report conversion. Extracted {len(marker_data)} rows.")
        return HEADERS, marker_data

    except FileNotFoundError:
        logger.error(f"❌ The file '{xml_file_path}' was not found.")
        raise
    except ET.ParseError as parse_error:
        logger.error(f"❌ Malformed XML (SHW) file '{xml_file_path}': {parse_error}")
        raise
    except Exception:
        logger.exception("❌ Error during SHW conversion data extraction")
        raise
