# Core/read_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import inspect

from oaFileHandlers.oaFileImportShow.FileReaders.loader import maker_file_check_for_markers_file
from oaLogging.Methods.matrix_gate import matrix_log


class ShowtimeReadMixin:
    """
    Mixin for loading marker data from file systems for the Showtime tab.
    """

    def load_marker_data(self):
        """
        ⚡ DATA LOADER: Reads MARKERS.csv and populates internal state.
        Updates: self.marker_data, self.column_headers
        """
        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "🟢️️️🟢 Loading raw marker data from file.", level="DEBUG")

        raw_headers, raw_data = maker_file_check_for_markers_file()

        if not raw_data:
            self.marker_data = []
            self.column_headers = []
            matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "🟡 No marker data found in MARKERS.csv. No buttons will be created.", level="DEBUG")
            return

        self.marker_data = [
            dict(zip(raw_headers, row)) for row in raw_data if len(row) == len(raw_headers)
        ]
        self.column_headers = raw_headers

        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, f"✅ Loaded {len(self.marker_data)} rows. Converted to dictionaries for sorting and display.", level="SUCCESS")
