# workers/importers/worker_importer_loader.py
#
# A complete and comprehensive pre-amble that describes the file and the functions within.
# The purpose is to provide clear documentation and versioning.
#
# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# As the current hour is 20, no change is needed.

Current_Date = 20251226
Current_Time = 120000
Current_iteration = 44

current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"
current_version_hash = (Current_Date * Current_Time * Current_iteration)


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

import inspect
from tkinter import filedialog
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args 
from workers.importers.formats.worker_importer_from_csv_unknown import Marker_convert_csv_unknow_report_to_csv
from workers.importers.formats.worker_importer_from_ias_html import Marker_convert_IAShtml_report_to_csv
from workers.importers.formats.worker_importer_from_shure_wwb_shw import Marker_convert_WWB_SHW_File_report_to_csv
from workers.importers.formats.worker_importer_from_soundbase_pdf_v1 import Marker_convert_SB_PDF_File_report_to_csv
from workers.importers.formats.worker_importer_from_shure_wwb_zip import Marker_convert_wwb_zip_report_to_csv
from workers.importers.formats.worker_importer_from_soundbase_pdf_v2 import Marker_convert_SB_v2_PDF_File_report_to_csv
from workers.importers.worker_importer_saver import save_markers_file_internally
import os
import csv
import pathlib
from managers.configini.config_reader import Config
from workers.setup.worker_project_paths import GLOBAL_PROJECT_ROOT

app_constants = Config.get_instance() # Get the singleton instance

# Define the canonical headers
CANONICAL_HEADERS = ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]

LOCAL_DEBUG_ENABLE = False

def maker_file_check_for_markers_file():
    # Checks for the MARKERS.csv file in the DATA directory and loads it if it exists.
    current_function = inspect.currentframe().f_code.co_name
    
    # Use the stable GLOBAL_PROJECT_ROOT now available.
    target_path = GLOBAL_PROJECT_ROOT / 'DATA' / 'MARKERS.csv'
    
    if app_constants.global_settings['debug_enabled']:
        debug_logger(
                        function=f"{current_function}",
                        **_get_log_args()
                    )
    
    if target_path.is_file():
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"✅ Found an existing MARKERS.csv file. Attempting to load.",
                file=os.path.basename(__file__), # Use current file for logging
                version=current_version,
                function=f"{current_function}",
            )
        try:
            with open(target_path, 'r', newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames if reader.fieldnames else CANONICAL_HEADERS
                data = list(reader)
            
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message="✅ Successfully loaded MARKERS.csv on startup.",
                    file=os.path.basename(__file__),
                    version=current_version,
                    function=f"{current_function}",
                )
            return headers, data
        except Exception as e:
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"❌ Error loading existing MARKERS.csv on startup: {e}",
                    file=os.path.basename(__file__),
                    version=current_version,
                    function=f"{current_function}",
                )
            debug_logger(message=f"❌ Failed to load existing MARKERS.csv. {e}")
    else:
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message="🟢️️️🟡 No existing MARKERS.csv found. Starting with a blank table.",
                file=os.path.basename(__file__),
                version=current_version,
                function=f"{current_function}",
            )
    return CANONICAL_HEADERS, []

def load_markers_file_action(importer_tab_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    if not file_path:
        debug_logger(
            message="🟢️️️🟡 'Load CSV Marker Set' action cancelled by user.",
            file=importer_tab_instance.current_file,
            version=importer_tab_instance.current_version,
            function=f"{current_function}",
        )
        return
    headers, data = Marker_convert_csv_unknow_report_to_csv(file_path=file_path)
    if headers and data:
        importer_tab_instance.tree_headers = headers
        importer_tab_instance.tree_data = data
        importer_tab_instance._update_treeview()
        save_markers_file_internally(importer_tab_instance)

def load_ias_html_action(importer_tab_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".html",
        filetypes=[("HTML files", "*.html;*.htm"), ("All files", "*.*")]
    )
    if not file_path:
        debug_logger(
            message="🟢️️️🟡 'Load IAS HTML' action cancelled by user.",
            file=importer_tab_instance.current_file,
            version=importer_tab_instance.current_version,
            function=f"{current_function}",
        )
        return
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        headers, data = Marker_convert_IAShtml_report_to_csv(html_content)
        if headers and data:
            importer_tab_instance.tree_headers = headers
            importer_tab_instance.tree_data = data
            importer_tab_instance._update_treeview()
            save_markers_file_internally(importer_tab_instance)
    except Exception as e:
        debug_logger(
            message=f"❌ Error loading IAS HTML file: {e}",
            file=importer_tab_instance.current_file,
            version=importer_tab_instance.current_version,
            function=f"{current_function}",
        )
        return

def load_wwb_shw_action(importer_tab_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".shw",
        filetypes=[("Shure Wireless Workbench files", "*.shw"), ("All files", "*.*")]
    )
    if not file_path:
        debug_logger(
            message="🟢️️️🟡 'Load WWB.shw' action cancelled by user.",
            file=importer_tab_instance.current_file,
            version=importer_tab_instance.current_version,
            function=f"{current_function}",
        )
        return
    headers, data = Marker_convert_WWB_SHW_File_report_to_csv(xml_file_path=file_path)
    if headers and data:
        importer_tab_instance.tree_headers = headers
        importer_tab_instance.tree_data = data
        importer_tab_instance._update_treeview()
        save_markers_file_internally(importer_tab_instance)

def load_wwb_zip_action(importer_tab_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".zip",
        filetypes=[("Shure Wireless Workbench files", "*.zip"), ("All files", "*.*")]
    )
    if not file_path:
        debug_logger(
            message="🟢️️️🟡 'Load WWB.zip' action cancelled by user.",
            file=importer_tab_instance.current_file,
            version=importer_tab_instance.current_version,
            function=f"{current_function}",
            
        )
        return
    headers, data = Marker_convert_wwb_zip_report_to_csv(file_path=file_path)
    if headers and data:
        importer_tab_instance.tree_headers = headers
        importer_tab_instance.tree_data = data
        importer_tab_instance._update_treeview()
        save_markers_file_internally(importer_tab_instance)

def load_sb_pdf_action(importer_tab_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
    )
    if not file_path:
        debug_logger(
            message="🟢️️️🟡 'Load SB PDF' action cancelled by user.",
            file=importer_tab_instance.current_file,
            version=importer_tab_instance.current_version,
            function=f"{current_function}",
        )
        return
    headers, data = Marker_convert_SB_PDF_File_report_to_csv(pdf_file_path=file_path)
    if headers and data:
        importer_tab_instance.tree_headers = headers
        importer_tab_instance.tree_data = data
        importer_tab_instance._update_treeview()
        save_markers_file_internally(importer_tab_instance)

def load_sb_v2_pdf_action(importer_tab_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".pdf",
        filetypes=[("Sound Base V2 PDF files", "*.pdf"), ("All files", "*.*")]
    )
    if not file_path:
        debug_logger(
            message="🟢️️️🟡 'Load SB V2.pdf' action cancelled by user.",
            file=importer_tab_instance.current_file,
            version=importer_tab_instance.current_version,
            function=f"{current_function}",
            
        )
        return
    headers, data = Marker_convert_SB_v2_PDF_File_report_to_csv(pdf_file_path=file_path)
    if headers and data:
        importer_tab_instance.tree_headers = headers
        importer_tab_instance.tree_data = data
        importer_tab_instance._update_treeview()
        save_markers_file_internally(importer_tab_instance)