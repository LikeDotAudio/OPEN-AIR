from loguru import logger
from workers.importers.loader import maker_file_check_for_markers_file

class ShowtimeReadMixin:
    """
    Mixin for loading marker data from file systems for the Showtime tab.
    """

    def load_marker_data(self):
        """
        ⚡ DATA LOADER: Reads MARKERS.csv and populates internal state.
        Updates: self.marker_data, self.column_headers
        """
        logger.debug("🟢️️️🟢 Loading raw marker data from file.")

        raw_headers, raw_data = maker_file_check_for_markers_file()

        if not raw_data:
            self.marker_data = []
            self.column_headers = []
            logger.debug("🟡 No marker data found in MARKERS.csv. No buttons will be created.")
            return

        self.marker_data = [
            dict(zip(raw_headers, row)) for row in raw_data if len(row) == len(raw_headers)
        ]
        self.column_headers = raw_headers

        logger.success(f"✅ Loaded {len(self.marker_data)} rows. Converted to dictionaries for sorting and display.")
