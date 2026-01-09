# importers/worker_importer_appender.py
#
# This module provides functions for appending data from various file formats (CSV, HTML, SHW, ZIP, PDF) to a marker table.
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
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.importers.formats.worker_importer_from_csv_unknown import (
    Marker_convert_csv_unknow_report_to_csv,
)
from workers.importers.formats.worker_importer_from_ias_html import (
    Marker_convert_IAShtml_report_to_csv,
)
from workers.importers.formats.worker_importer_from_shure_wwb_shw import (
    Marker_convert_WWB_SHW_File_report_to_csv,
)
from workers.importers.formats.worker_importer_from_soundbase_pdf_v1 import (
    Marker_convert_SB_PDF_File_report_to_csv,
)
from workers.importers.worker_marker_file_import_converter import (
    Marker_convert_wwb_zip_report_to_csv,
    Marker_convert_SB_v2_PDF_File_report_to_csv,
)
from workers.importers.worker_importer_saver import save_markers_file_internally

LOCAL_DEBUG_ENABLE = False


# Appends data from an unknown CSV file to the marker table.
# This function prompts the user to select a CSV file, converts its content
# to the standardized marker format, and then imports this new data into the
# active table editor.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
#     editor_instance: The instance of the table editor.
# Outputs:
#     None.
def append_markers_file_action(importer_tab_instance, editor_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    if not file_path:
        debug_logger(
            message="🟢️️️🟡 'Append CSV Marker Set' action cancelled by user.",
            file=importer_tab_instance.current_file,
            version=importer_tab_instance.current_version,
            function=f"{current_function}",
        )
        return
    headers, new_data = Marker_convert_csv_unknow_report_to_csv(file_path=file_path)
    if headers and new_data:
        # Pass the new data to the table editor for handling
        editor_instance.import_data(new_data)
        save_markers_file_internally(importer_tab_instance)


# Appends data from an IAS HTML report to the marker table.
# This function prompts the user to select an HTML file, extracts and converts its
# content to the standardized marker format, and then imports this data into the
# active table editor.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
#     editor_instance: The instance of the table editor.
# Outputs:
#     None.
def append_ias_html_action(importer_tab_instance, editor_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".html",
        filetypes=[("HTML files", "*.html;*.htm"), ("All files", "*.*")],
    )
    if not file_path:
        debug_logger(
            message="🟢️️️🟡 'Append IAS HTML' action cancelled by user.",
            file=importer_tab_instance.current_file,
            version=importer_tab_instance.current_version,
            function=f"{current_function}",
        )
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        headers, new_data = Marker_convert_IAShtml_report_to_csv(html_content)
        if headers and new_data:
            editor_instance.import_data(new_data)
            save_markers_file_internally(importer_tab_instance)
    except Exception as e:
        debug_logger(
            message=f"❌ Error appending IAS HTML file: {e}",
            file=importer_tab_instance.current_file,
            version=importer_tab_instance.current_version,
            function=f"{current_function}",
        )
        return


# Appends data from a Shure Wireless Workbench (.shw) XML file to the marker table.
# This function prompts the user to select an SHW file, converts its content
# to the standardized marker format, and then imports this new data into the
# active table editor.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
#     editor_instance: The instance of the table editor.
# Outputs:
#     None.
def append_wwb_shw_action(importer_tab_instance, editor_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".shw",
        filetypes=[("Shure Wireless Workbench files", "*.shw"), ("All files", "*.*")],
    )
    if not file_path:
        debug_logger(
            message="🟢️️️🟡 'Append WWB.shw' action cancelled by user.",
            file=importer_tab_instance.current_file,
            version=importer_tab_instance.current_version,
            function=f"{current_function}",
        )
        return
    headers, new_data = Marker_convert_WWB_SHW_File_report_to_csv(
        xml_file_path=file_path
    )
    if headers and new_data:
        editor_instance.import_data(new_data)
        save_markers_file_internally(importer_tab_instance)


# Appends data from a Shure Wireless Workbench (.zip) archive to the marker table.
# This function prompts the user to select a ZIP file, extracts and converts its
# content to the standardized marker format, and then imports this data into the
# active table editor.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
#     editor_instance: The instance of the table editor.
# Outputs:
#     None.
def append_wwb_zip_action(importer_tab_instance, editor_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".zip",
        filetypes=[("Shure Wireless Workbench files", "*.zip"), ("All files", "*.*")],
    )
    if not file_path:
        debug_logger(
            message="🟢️️️🟡 'Append WWB.zip' action cancelled by user.",
            file=importer_tab_instance.current_file,
            version=importer_tab_instance.current_version,
            function=f"{current_function}",
        )
        return
    headers, new_data = Marker_convert_wwb_zip_report_to_csv(file_path=file_path)
    if headers and new_data:
        editor_instance.import_data(new_data)
        save_markers_file_internally(importer_tab_instance)


# Appends data from a Sound Base PDF report (version 1) to the marker table.
# This function prompts the user to select a PDF file, converts its content
# to the standardized marker format, and then imports this new data into the
# active table editor.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
#     editor_instance: The instance of the table editor.
# Outputs:
#     None.
def append_sb_pdf_action(importer_tab_instance, editor_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
    )
    if not file_path:
        debug_logger(
            message="🟢️️️🟡 'Append SB PDF' action cancelled by user.",
            file=importer_tab_instance.current_file,
            version=importer_tab_instance.current_version,
            function=f"{current_function}",
        )
        return
    headers, new_data = Marker_convert_SB_PDF_File_report_to_csv(
        pdf_file_path=file_path
    )
    if headers and new_data:
        editor_instance.import_data(new_data)
        save_markers_file_internally(importer_tab_instance)


# Appends data from a Sound Base PDF report (version 2) to the marker table.
# This function prompts the user to select a PDF file, converts its content
# to the standardized marker format, and then imports this new data into the
# active table editor.
# Inputs:
#     importer_tab_instance: The instance of the importer tab.
#     editor_instance: The instance of the table editor.
# Outputs:
#     None.
def append_sb_v2_pdf_action(importer_tab_instance, editor_instance):
    current_function = inspect.currentframe().f_code.co_name
    file_path = filedialog.askopenfilename(
        defaultextension=".pdf",
        filetypes=[("Sound Base V2 PDF files", "*.pdf"), ("All files", "*.*")],
    )
    if not file_path:
        debug_logger(
            message="🟢️️️🟡 'Append SB V2.pdf' action cancelled by user.",
            file=importer_tab_instance.current_file,
            version=importer_tab_instance.current_version,
            function=f"{current_function}",
        )
        return
    headers, new_data = Marker_convert_SB_v2_PDF_File_report_to_csv(
        pdf_file_path=file_path
    )
    if headers and new_data:
        editor_instance.import_data(new_data)
        save_markers_file_internally(importer_tab_instance)