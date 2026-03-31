# oaFileImportShow/FileReaders/loader.py
#
# Provides functions for loading marker data from various file formats 
# (CSV, HTML, SHW, ZIP, PDF) into the application's marker table.
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
# Version 20260330.1600.1

import inspect
from tkinter import filedialog
import os
import csv
from loguru import logger
from oaLogging.Methods.matrix_gate import is_debug_allowed, matrix_log
from oaConfiguration.FileReaders.config_reader import Config

def _is_debug():
    return is_debug_allowed(system="UI", element="IMPORTER")

app_constants = Config.get_instance()

from oaFileImportCSV.FileReaders.from_csv_unknown import (
    Marker_convert_csv_unknow_report_to_csv,
)
from oaFileImportHTML.FileReaders.from_ias_html import (
    Marker_convert_IAShtml_report_to_csv,
)
from oaFileImportShow.FileReaders.from_shure_wwb_shw import (
    Marker_convert_WWB_SHW_File_report_to_csv,
)
from oaFileImportPDF.FileReaders.from_soundbase_pdf_v1 import (
    Marker_convert_SB_PDF_File_report_to_csv,
)
from oaFileImportShow.FileReaders.from_shure_wwb_zip import (
    Marker_convert_wwb_zip_report_to_csv,
)
from oaFileImportPDF.FileReaders.from_soundbase_pdf_v2 import (
    Marker_convert_SB_v2_PDF_File_report_to_csv,
)
from oaFileImportShow.FileReaders.saver import save_markers_file_internally
from oaOchestration.Constants.project_paths import GLOBAL_PROJECT_ROOT

# Define the canonical headers
CANONICAL_HEADERS = ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]

def maker_file_check_for_markers_file():
    """
    Checks for the MARKERS.csv file in the DATA directory and loads it if it exists.
    """
    current_function = inspect.currentframe().f_code.co_name
    from oaOchestration.Core.path_initializer import DATA_RUNNING_DIR
    target_path = DATA_RUNNING_DIR / "MARKERS.csv"

    matrix_log("ui", "importer", "maker_file_check_for_markers_file", 
               f"📥📑🔍 [IMPORTER] {current_function}", "DEBUG")

    if target_path.is_file():
        matrix_log("ui", "importer", "maker_file_check_for_markers_file", 
                   "📥📑✅ [SUCCESS] Found an existing MARKERS.csv file. Attempting to load.", "SUCCESS")
        try:
            with open(target_path, "r", newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames if reader.fieldnames else CANONICAL_HEADERS
                data = list(reader)

            matrix_log("ui", "importer", "maker_file_check_for_markers_file", 
                       "📥📑✅ [SUCCESS] Successfully loaded MARKERS.csv on startup.", "SUCCESS")
            return headers, data
        except Exception as e:
            matrix_log("ui", "importer", "maker_file_check_for_markers_file", 
                       f"📥📑❌ [ERROR] Error loading existing MARKERS.csv on startup: {e}", "ERROR")
    else:
        matrix_log("ui", "importer", "maker_file_check_for_markers_file", 
                   "📥📑🟡 [IMPORTER] No existing MARKERS.csv found. Starting with a blank table.", "DEBUG")
    return CANONICAL_HEADERS, []

def load_markers_file_action(importer_tab_instance):
    file_path = filedialog.askopenfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    if not file_path:
        matrix_log("ui", "importer", "load_markers_file_action", 
                   "📥📑🟡 [IMPORTER] 'Load CSV Marker Set' action cancelled.", "DEBUG")
        return
    headers, data = Marker_convert_csv_unknow_report_to_csv(file_path=file_path)
    if headers and data:
        importer_tab_instance.tree_headers = headers
        importer_tab_instance.tree_data = data
        importer_tab_instance._update_treeview()
        save_markers_file_internally(importer_tab_instance)

def load_ias_html_action(importer_tab_instance):
    file_path = filedialog.askopenfilename(
        defaultextension=".html",
        filetypes=[("HTML files", "*.html;*.htm"), ("All files", "*.*")],
    )
    if not file_path:
        matrix_log("ui", "importer", "load_ias_html_action", 
                   "📥📑🟡 [IMPORTER] 'Load IAS HTML' action cancelled by user.", "DEBUG")
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
        matrix_log("ui", "importer", "load_ias_html_action", f"📥📑❌ [ERROR] Error loading IAS HTML file: {e}", "ERROR")
        return

def load_wwb_shw_action(importer_tab_instance):
    file_path = filedialog.askopenfilename(
        defaultextension=".shw",
        filetypes=[("Shure Wireless Workbench files", "*.shw"), ("All files", "*.*")],
    )
    if not file_path:
        matrix_log("ui", "importer", "load_wwb_shw_action", "📥📑🟡 [IMPORTER] 'Load WWB.shw' action cancelled by user.", "DEBUG")
        return
    headers, data = Marker_convert_WWB_SHW_File_report_to_csv(xml_file_path=file_path)
    if headers and data:
        importer_tab_instance.tree_headers = headers
        importer_tab_instance.tree_data = data
        importer_tab_instance._update_treeview()
        save_markers_file_internally(importer_tab_instance)

def load_wwb_zip_action(importer_tab_instance):
    file_path = filedialog.askopenfilename(
        defaultextension=".zip",
        filetypes=[("Shure Wireless Workbench files", "*.zip"), ("All files", "*.*")],
    )
    if not file_path:
        matrix_log("ui", "importer", "load_wwb_zip_action", "📥📑🟡 [IMPORTER] 'Load WWB.zip' action cancelled by user.", "DEBUG")
        return
    headers, data = Marker_convert_wwb_zip_report_to_csv(file_path=file_path)
    if headers and data:
        importer_tab_instance.tree_headers = headers
        importer_tab_instance.tree_data = data
        importer_tab_instance._update_treeview()
        save_markers_file_internally(importer_tab_instance)

def load_sb_pdf_action(importer_tab_instance):
    file_path = filedialog.askopenfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
    )
    if not file_path:
        matrix_log("ui", "importer", "load_sb_pdf_action", "📥📑🟡 [IMPORTER] 'Load SB PDF' action cancelled by user.", "DEBUG")
        return
    headers, data = Marker_convert_SB_PDF_File_report_to_csv(pdf_file_path=file_path)
    if headers and data:
        importer_tab_instance.tree_headers = headers
        importer_tab_instance.tree_data = data
        importer_tab_instance._update_treeview()
        save_markers_file_internally(importer_tab_instance)

def load_sb_v2_pdf_action(importer_tab_instance):
    file_path = filedialog.askopenfilename(
        defaultextension=".pdf",
        filetypes=[("Sound Base V2 PDF files", "*.pdf"), ("All files", "*.*")],
    )
    if not file_path:
        matrix_log("ui", "importer", "load_sb_v2_pdf_action", "📥📑🟡 [IMPORTER] 'Load SB V2.pdf' action cancelled by user.", "DEBUG")
        return
    headers, data = Marker_convert_SB_v2_PDF_File_report_to_csv(pdf_file_path=file_path)
    if headers and data:
        importer_tab_instance.tree_headers = headers
        importer_tab_instance.tree_data = data
        importer_tab_instance._update_treeview()
        save_markers_file_internally(importer_tab_instance)
