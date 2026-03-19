# workers/importers/formats/from_soundbase_pdf_v2.py
#
# Logic for converting Sound Base PDF files (version 2) into standardized marker format.
#

import os
import re
import numpy as np
import pdfplumber

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True
from loguru import logger
from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()

# --- Constants ---
VERSION = "20251129.120000.1"
HEADERS = ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]

def convert_soundbase_pdf_v2_to_markers(pdf_file_path):
    """
    Parses a PDF file (Sound Base v2 format) and extracts frequency data, converting it
    into a standardized marker format.
    """

    if LOCAL_DEBUG:
        logger.debug(f"▶️ Starting PDF (Sound Base v2) report conversion for: {os.path.basename(pdf_file_path)}")

    marker_data = []

    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            text = pdf.pages[0].extract_text()

            # Use regex to find the ZONE
            zone_match = re.search(r"ZONE: (.+)", text)
            zone = zone_match.group(1).strip() if zone_match else "N/A"
            logger.debug(f"🔍 Found ZONE: {zone}")

            # The pattern to find all groups
            group_pattern = re.compile(
                r"^\s*([A-Z\s&]+ IEM\'S|[A-Z\s&]+ MICS & BACKLINE)\s*$", re.MULTILINE
            )

            lines = text.split("\n")
            current_group = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check if the line is a new group header
                group_match = group_pattern.search(line)
                if group_match:
                    current_group = group_match.group(1).strip()
                    logger.debug(f"🔍 Found new GROUP: {current_group}")
                    continue

                # Regex to find all frequency-device pairs on the current line
                device_matches = re.findall(
                    r"(\d+\.\d+)\s+([\w\s-]+?(?=\s*\d+\.\d+|$))", line
                )

                if device_matches:
                    for freq, device in device_matches:
                        device_clean = device.strip()
                        freq_clean = freq.strip()

                        if current_group:
                            marker_data.append(
                                {
                                    "ZONE": zone,
                                    "GROUP": current_group,
                                    "DEVICE": device_clean,
                                    "NAME": device_clean,
                                    "FREQ_MHZ": freq_clean,
                                    "PEAK": np.nan,
                                }
                            )

            if LOCAL_DEBUG:
                logger.success(f"✅ Finished conversion. Extracted {len(marker_data)} rows.")
            return HEADERS, marker_data

    except FileNotFoundError:
        logger.error(f"❌ The file '{pdf_file_path}' was not found.")
        return [], []
    except Exception:
        if LOCAL_DEBUG:
            logger.exception("❌ Error during PDF conversion")
        return [], []
