# Core/interaction_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from loguru import logger

class ShowtimeInteractionMixin:
    """
    Mixin for handling UI interactions in the Showtime tab using internal state.
    """

    def on_zone_toggle(self, zone_name):
        """Updates selection when a zone button is toggled."""
        logger.debug(f"🟢️️️🔵 Zone toggle clicked for: {zone_name}. Current selection: {self.selected_zone}.")
        
        if self.selected_zone == zone_name:
            self.selected_zone = None
            self.selected_group = None
            logger.debug("🟢️️️🟡 Deselected Zone. Clearing Group selection.")
        else:
            self.selected_zone = zone_name
            self.selected_group = None
            logger.debug(f"🟢️️️🟢 Selected new Zone: {self.selected_zone}. Clearing Group selection.")

        self._refresh_showtime_ui()
        self.on_tune_request_from_selection()

    def on_group_toggle(self, group_name):
        """Updates selection when a group button is toggled."""
        logger.debug(f"🟢️️️🔵 Group toggle clicked for: {group_name}. Current selection: {self.selected_group}.")
        
        if self.selected_group == group_name:
            self.selected_group = None
        else:
            self.selected_group = group_name
            logger.debug(f"🟢️️️🟢 Selected new Group: {self.selected_group}.")

        self._create_group_buttons()
        self._create_device_buttons()
        self.on_tune_request_from_selection()

    def on_marker_button_click(self, button):
        """Handles selection of a specific device/marker button."""
        if self.selected_device_button == button:
            self.selected_device_button.config(style="Custom.TButton")
            self.selected_device_button = None
        else:
            if self.selected_device_button:
                self.selected_device_button.config(style="Custom.TButton")
            
            self.selected_device_button = button
            self.selected_device_button.config(style="Selected.TButton")

        self.on_tune_request_from_selection()

    def _refresh_showtime_ui(self):
        """Helper to trigger re-creation of all dynamic button layers."""
        self._create_zone_buttons()
        self._create_group_buttons()
        self._create_device_buttons()
