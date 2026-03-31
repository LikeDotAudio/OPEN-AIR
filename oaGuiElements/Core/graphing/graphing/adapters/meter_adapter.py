# adapters/meter_adapter.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from oaGuiElements.Core.graphing.graphing.Meter_to_display_units import (
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
    HorizontalMeterWithText,
    VerticalMeter,
)
from oaLogging.Core.logger import builder_logger

class MeterAdapter:
    """Adapter for creating Meter widgets."""

    @staticmethod
    def create_horizontal(parent_widget, config_data, **kwargs):
        widget_id = config_data.get("id", "h_meter")
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] meter_adapter: Instantiating HorizontalMeter '{widget_id}'.", level="DEBUG")
        
        return HorizontalMeterWithText(
            parent=parent_widget,
            config=config_data,
            base_mqtt_topic_from_path=config_data.get("base_mqtt_topic_from_path"),
            widget_id=widget_id,
            state_mirror_engine=config_data.get("state_mirror_engine"),
            subscriber_router=config_data.get("subscriber_router"),
        )

    @staticmethod
    def create_vertical(parent_widget, config_data, **kwargs):
        widget_id = config_data.get("id", "v_meter")
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] meter_adapter: Instantiating VerticalMeter '{widget_id}'.", level="DEBUG")
        
        return VerticalMeter(
            parent=parent_widget,
            config=config_data,
            base_mqtt_topic_from_path=config_data.get("base_mqtt_topic_from_path"),
            widget_id=widget_id,
            state_mirror_engine=config_data.get("state_mirror_engine"),
            subscriber_router=config_data.get("subscriber_router"),
        )
