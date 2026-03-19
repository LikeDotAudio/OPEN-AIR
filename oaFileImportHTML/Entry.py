"""
oaFileImportHTML/Entry.py - The sole orchestrator for the HTML Import Module.
"""
from .FileReaders.from_ias_html import convert_ias_html_to_markers

# Alias for backward compatibility (referenced in other modules)
Marker_convert_IAShtml_report_to_csv = convert_ias_html_to_markers

__all__ = [
    "convert_ias_html_to_markers",
    "Marker_convert_IAShtml_report_to_csv"
]
