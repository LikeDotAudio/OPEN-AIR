# Core/group_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from collections import defaultdict
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from loguru import logger

class ShowtimeGroupMixin:
    """
    Mixin for processing and grouping marker data for the Showtime tab.
    Encapsulates state-based grouping and sorting logic.
    """

    def process_and_sort_markers(self):
        """
        ⚡ ORCHESTRATOR: Coordinates the grouping and sorting pipeline using internal state.
        Accesses: self.marker_data
        Updates: self.grouped_markers
        """
        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "🟢️️️🔵 Starting marker processing pipeline.", level="INFO")

        # 1. Grouping
        self.grouped_markers = self._group_markers_by_zone_and_group()

        # 2. Sorting
        self._sort_markers_alphabetically()

        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "✅ Markers grouped and sorted successfully.", level="SUCCESS")

    def _group_markers_by_zone_and_group(self):
        """⚡ DATA TRANSFORMATION: Organizes internal marker list into nested structure."""
        if not hasattr(self, 'marker_data'):
            logger.warning("⚠️ No marker_data found on instance. Initializing empty grouping.")
            return defaultdict(lambda: defaultdict(list))

        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "🟢 [DATA] Grouping marker data by Zone and Group.", level="DEBUG")
        grouped = defaultdict(lambda: defaultdict(list))
        for row in self.marker_data:
            zone = row.get("ZONE", "N/A")
            group = row.get("GROUP", "N/A")
            grouped[zone][group].append(row)
        return grouped

    def _sort_markers_alphabetically(self):
        """⚡ DATA ORDERING: Alphabetically sorts devices within the internal grouped structure."""
        if not hasattr(self, 'grouped_markers'): return

        matrix_log("UI", "SHOWTIME", inspect.currentframe().f_code.co_name, "🔵 [DATA] Sorting markers by Device Name.", level="DEBUG")
        for zone, groups in self.grouped_markers.items():
            for group, devices in groups.items():
                devices.sort(key=lambda x: x.get("NAME", ""))
