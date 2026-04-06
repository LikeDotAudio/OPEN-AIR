# FileReaders/from_shure_wwb_shw.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Logic for converting Shure Wireless Workbench .shw (XML) files into standardized marker format.

import os
import xml.etree.ElementTree as ET
import numpy as np

from oaLogging.Methods.matrix_gate import is_debug_allowed, matrix_log

def _is_debug():
    return is_debug_allowed(system="UI", element="IMPORTER")

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

# --- Constants ---
VERSION = "20251129.120000.1"
HEADERS = ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]

def convert_shure_wwb_shw_to_markers(xml_file_path):
    """
    Parses a Shure Wireless Workbench 6 XML (.shw) report and returns
    a list of dictionaries in the standardized marker format.
    """
    return _internal_convert_shure_wwb_shw_to_markers(xml_file_path)

def Marker_convert_WWB_SHW_File_report_to_csv(xml_file_path):
    """
    Backward compatibility alias.
    """
    return convert_shure_wwb_shw_to_markers(xml_file_path)

def _internal_convert_shure_wwb_shw_to_markers(xml_file_path):
    """
    Parses an SHW (XML) file and extracts frequency data, converting it
    into a standardized marker format. All frequencies are converted to MHz for consistency.
    """

    matrix_log("ui", "importer", "_internal_convert_shure_wwb_shw_to_markers", 
               f"▶️ Starting SHW report conversion for '{os.path.basename(xml_file_path)}'.", "DEBUG")

    marker_data = []

    try:
        with open(xml_file_path, "r", encoding="utf-8") as xml_file:
            tree = ET.parse(xml_file)
        root = tree.getroot()

        matrix_log("ui", "importer", "_internal_convert_shure_wwb_shw_to_markers", "✅ XML file parsed successfully.", "SUCCESS")

        # Iterate through 'freq_entry' elements
        for i, freq_entry in enumerate(root.findall(".//freq_entry")):
            if i % 100 == 0:  # Print progress every 100 entries
                matrix_log("ui", "importer", "_internal_convert_shure_wwb_shw_to_markers", f"▶️ Processing SHW entry {i}...", "DEBUG")

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
                    matrix_log("ui", "importer", "_internal_convert_shure_wwb_shw_to_markers", 
                               f"↔️ SHW Freq conversion: '{freq_str}' kHz -> {freq_MHz} MHz", "DEBUG")
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

        matrix_log("ui", "importer", "_internal_convert_shure_wwb_shw_to_markers", 
                   f"✅ Finished SHW report conversion. Extracted {len(marker_data)} rows.", "SUCCESS")
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
