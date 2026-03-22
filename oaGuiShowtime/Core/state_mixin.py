# Core/state_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from collections import defaultdict

class ShowtimeStateMixin:
    """
    Mixin for managing the reactive state of the Showtime tab.
    """

    def _initialize_showtime_state(self):
        """Sets up the baseline state variables for Showtime tracking."""
        self.marker_data = []
        self.column_headers = []
        self.grouped_markers = defaultdict(lambda: defaultdict(list))
        
        # UI Selection State
        self.selected_zone = None
        self.selected_group = None
        self.selected_device_button = None
        
        # UI References
        self.zone_frame = None
        self.group_frame = None
        self.device_frame = None
