# oaFileImportPDF/Entry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

"""
oaFileImportPDF/Entry.py - The sole orchestrator for the PDF Import Module.
"""
from .FileReaders.from_soundbase_pdf_v1 import convert_soundbase_pdf_v1_to_markers
from .FileReaders.from_soundbase_pdf_v2 import convert_soundbase_pdf_v2_to_markers

# Aliases for backward compatibility
Marker_convert_SB_PDF_File_report_to_csv = convert_soundbase_pdf_v1_to_markers
Marker_convert_SB_v2_PDF_File_report_to_csv = convert_soundbase_pdf_v2_to_markers

__all__ = [
    "convert_soundbase_pdf_v1_to_markers",
    "convert_soundbase_pdf_v2_to_markers",
    "Marker_convert_SB_PDF_File_report_to_csv",
    "Marker_convert_SB_v2_PDF_File_report_to_csv"
]
