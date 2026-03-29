# Core/tune_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from loguru import logger
from oaGuiTelemetry.Methods.marker_logic import calculate_frequency_range

class ShowtimeTuneMixin:
    """
    Mixin for coordinating hardware tuning requests from the Showtime tab.
    """

    def on_tune_request_from_selection(self):
        """
        ⚡ TUNE COORDINATOR: Translates UI selections into hardware commands.
        Uses internal state to determine frequency ranges.
        """
        logger.debug("🟢️️️🟢 Initiating tuning request based on current selection.")

        if self.selected_device_button:
            # Case 1: Specific Device
            marker_data = self.selected_device_button.marker_data
            logger.debug(f"🔍 Device selected: {marker_data.get('NAME', 'N/A')}.")
            # self.mqtt_util.publish_tuning(...) # Future logic
            
        elif self.selected_group:
            # Case 2: Selected Group
            logger.debug(f"🔍 Tuning to start/stop of selected Group: {self.selected_group}.")
            group_devices = self.grouped_markers[self.selected_zone][self.selected_group]
            min_f, max_f = calculate_frequency_range(group_devices)
            
            if min_f is not None and max_f is not None:
                pass # self.mqtt_util.publish_span(...)
            else:
                logger.error("❌ No valid frequencies in selected group.")

        elif self.selected_zone:
            # Case 3: Selected Zone
            logger.debug(f"🔍 Tuning to start/stop of selected Zone: {self.selected_zone}.")
            all_zone_devices = []
            for g_name in self.grouped_markers[self.selected_zone]:
                all_zone_devices.extend(self.grouped_markers[self.selected_zone][g_name])
            
            min_f, max_f = calculate_frequency_range(all_zone_devices)
            if min_f is not None and max_f is not None:
                pass # self.mqtt_util.publish_span(...)
            else:
                logger.error("❌ No valid frequencies in selected zone.")
        
        else:
            # Case 4: Global
            logger.debug("🔍 No filters selected. Tuning to span of all markers.")
            min_f, max_f = calculate_frequency_range(self.marker_data)
            if min_f is not None and max_f is not None:
                pass # self.mqtt_util.publish_span(...)
            else:
                logger.error("❌ No valid frequencies in marker data.")
