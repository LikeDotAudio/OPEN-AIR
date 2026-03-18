# importers/worker_importer_loader.py
#
# This module provides functions for loading marker data from various file formats (CSV, HTML, SHW, ZIP, PDF) into the application's marker table.
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
from tkinter import filedialog
import os
import csv

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance

from oaFileImportCSV.from_csv_unknown import (
    Marker_convert_csv_unknow_report_to_csv,
)
from oaFileImportHTML.from_ias_html import (
    Marker_convert_IAShtml_report_to_csv,
)
from oaFileImportShow.from_shure_wwb_shw import (
    Marker_convert_WWB_SHW_File_report_to_csv,
)
from oaFileImportPDF.from_soundbase_pdf_v1 import (
    Marker_convert_SB_PDF_File_report_to_csv,
)
from oaFileImportShow.from_shure_wwb_zip import (
    Marker_convert_wwb_zip_report_to_csv,
)
from oaFileImportPDF.from_soundbase_pdf_v2 import (
    Marker_convert_SB_v2_PDF_File_report_to_csv,
)
from oaFileImportShow.saver import save_markers_file_internally
from oaOchestration.project_paths import GLOBAL_PROJECT_ROOT

# Define the canonical headers
CANONICAL_HEADERS = ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]


# Checks for and loads an existing MARKERS.csv file from the DATA directory on startup.
# If the file exists, it reads its contents and returns the headers and data.
# Otherwise, it returns canonical headers and an empty data list.
# Inputs:
#     None.
# Outputs:
#     tuple: A tuple containing the headers and a list of dictionaries representing the marker data.
def maker_file_check_for_markers_file():
    """
    Checks for the MARKERS.csv file in the DATA directory and loads it if it exists.
    """
    current_function = inspect.currentframe().f_code.co_name

    # Use the stable GLOBAL_PROJECT_ROOT now available.
    from oaOchestration.path_initializer import DATA_RUNNING_DIR
    target_path = DATA_RUNNING_DIR / "MARKERS.csv"

    if LOCAL_DEBUG:
        logger.debug(f"📥📑🔍 [IMPORTER] {current_function}")

    if target_path.is_file():
        if LOCAL_DEBUG:
            logger.success(
                f"📥📑✅ [SUCCESS] Found an existing MARKERS.csv file. "
                f"Attempting to load."
            )
        try:
            with open(target_path, "r", newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames if reader.fieldnames else CANONICAL_HEADERS
                data = list(reader)

            if LOCAL_DEBUG:
                logger.success(
                    "📥📑✅ [SUCCESS] Successfully loaded MARKERS.csv on startup."
                )
            return headers, data
        except Exception as e:
            logger.exception(
                f"📥📑❌ [ERROR] Error loading existing MARKERS.csv on startup: {e}"
            )
    else:
        if LOCAL_DEBUG:
            logger.debug(
                "📥📑🟡 [IMPORTER] No existing MARKERS.csv found. "
                "Starting with a blank table."
            )
    return CANONICAL_HEADERS, []


# Loads marker data from a selected CSV file into the importer tab's table.
# This function prompts the user to select a CSV file, converts its content
# to the standardized marker format, updates the importer tab's internal data model,
# and refreshes the Treeview display.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
# Outputs:
#     None.
def load_markers_file_action(importer_tab_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    if not file_path:
        if LOCAL_DEBUG:
            logger.debug(
                "📥📑🟡 [IMPORTER] 'Load CSV Marker Set' action cancelled."
            )
        return
    headers, data = Marker_convert_csv_unknow_report_to_csv(file_path=file_path)
    if headers and data:
        importer_tab_instance.tree_headers = headers
        importer_tab_instance.tree_data = data
        importer_tab_instance._update_treeview()
        save_markers_file_internally(importer_tab_instance)


# Loads marker data from a selected IAS HTML report into the importer tab's table.
# This function prompts the user to select an HTML file, extracts and converts its
# content to the standardized marker format, updates the importer tab's internal data model,
# and refreshes the Treeview display.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
# Outputs:
#     None.
def load_ias_html_action(importer_tab_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".html",
        filetypes=[("HTML files", "*.html;*.htm"), ("All files", "*.*")],
    )
    if not file_path:
        if LOCAL_DEBUG:
            logger.debug(
                "📥📑🟡 [IMPORTER] 'Load IAS HTML' action cancelled by user."
            )
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        headers, data = Marker_convert_IAShtml_report_to_csv(html_content)
        if headers and data:
            importer_tab_instance.tree_headers = headers
            importer_tab_instance.tree_data = data
            importer_tab_instance._update_treeview()
            save_markers_file_internally(importer_tab_instance)
    except Exception as e:
        logger.exception(
            f"📥📑❌ [ERROR] Error loading IAS HTML file: {e}"
        )
        return


# Loads marker data from a selected Shure Wireless Workbench (.shw) XML file into the importer tab's table.
# This function prompts the user to select an SHW file, converts its content
# to the standardized marker format, updates the importer tab's internal data model,
# and refreshes the Treeview display.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
# Outputs:
#     None.
def load_wwb_shw_action(importer_tab_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".shw",
        filetypes=[("Shure Wireless Workbench files", "*.shw"), ("All files", "*.*")],
    )
    if not file_path:
        if LOCAL_DEBUG:
            logger.debug(
                "📥📑🟡 [IMPORTER] 'Load WWB.shw' action cancelled by user."
            )
        return
    headers, data = Marker_convert_WWB_SHW_File_report_to_csv(xml_file_path=file_path)
    if headers and data:
        importer_tab_instance.tree_headers = headers
        importer_tab_instance.tree_data = data
        importer_tab_instance._update_treeview()
        save_markers_file_internally(importer_tab_instance)


# Loads marker data from a selected Shure Wireless Workbench (.zip) archive into the importer tab's table.
# This function prompts the user to select a ZIP file, extracts and converts its
# content to the standardized marker format, updates the importer tab's internal data model,
# and refreshes the Treeview display.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
# Outputs:
#     None.
def load_wwb_zip_action(importer_tab_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".zip",
        filetypes=[("Shure Wireless Workbench files", "*.zip"), ("All files", "*.*")],
    )
    if not file_path:
        if LOCAL_DEBUG:
            logger.debug(
                "📥📑🟡 [IMPORTER] 'Load WWB.zip' action cancelled by user."
            )
        return
    headers, data = Marker_convert_wwb_zip_report_to_csv(file_path=file_path)
    if headers and data:
        importer_tab_instance.tree_headers = headers
        importer_tab_instance.tree_data = data
        importer_tab_instance._update_treeview()
        save_markers_file_internally(importer_tab_instance)


# Loads marker data from a selected Sound Base PDF report (version 1) into the importer tab's table.
# This function prompts the user to select a PDF file, converts its content
# to the standardized marker format, updates the importer tab's internal data model,
# and refreshes the Treeview display.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
# Outputs:
#     None.
def load_sb_pdf_action(importer_tab_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
    )
    if not file_path:
        if LOCAL_DEBUG:
            logger.debug(
                "📥📑🟡 [IMPORTER] 'Load SB PDF' action cancelled by user."
            )
        return
    headers, data = Marker_convert_SB_PDF_File_report_to_csv(pdf_file_path=file_path)
    if headers and data:
        importer_tab_instance.tree_headers = headers
        importer_tab_instance.tree_data = data
        importer_tab_instance._update_treeview()
        save_markers_file_internally(importer_tab_instance)


# Loads marker data from a selected Sound Base PDF report (version 2) into the importer tab's table.
# This function prompts the user to select a PDF file, converts its content
# to the standardized marker format, updates the importer tab's internal data model,
# and refreshes the Treeview display.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
# Outputs:
#     None.
def load_sb_v2_pdf_action(importer_tab_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".pdf",
        filetypes=[("Sound Base V2 PDF files", "*.pdf"), ("All files", "*.*")],
    )
    if not file_path:
        if LOCAL_DEBUG:
            logger.debug(
                "📥📑🟡 [IMPORTER] 'Load SB V2.pdf' action cancelled by user."
            )
        return
    headers, data = Marker_convert_SB_v2_PDF_File_report_to_csv(pdf_file_path=file_path)
    if headers and data:
        importer_tab_instance.tree_headers = headers
        importer_tab_instance.tree_data = data
        importer_tab_instance._update_treeview()
        save_markers_file_internally(importer_tab_instance)
