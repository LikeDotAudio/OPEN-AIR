# graphing/meter_widget_adapter.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: data_graphing/meter_widget_adapter.py

import inspect

from oaConfigurationManager.FileReaders.config_reader import Config
from oaGuiElements.Core.graphing.Methods.Meter_to_display_units import (
    HorizontalMeterWithText,
    VerticalMeter,
)

# --- Standard Debug Logging Setup ---
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()


class MeterWidgetAdapterMixin:
    """Mixin to handle the creation of Meter widgets."""

    # Creates a HorizontalMeterWithText widget.
    # This method instantiates and configures a horizontal meter, passing in the
    # necessary configuration, MQTT topic information, and state management engines.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the horizontal meter.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     HorizontalMeterWithText: The created HorizontalMeterWithText widget.
    def _create_horizontal_meter(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] meter_adapter: Instantiating HorizontalMeter '{config_data.get('id', 'Unknown')}'.", level="DEBUG")

        # Extract arguments from config_data
        config = config_data  # config_data is the config
        base_mqtt_topic_from_path = config_data.get("base_mqtt_topic_from_path")
        state_mirror_engine = config_data.get("state_mirror_engine")
        subscriber_router = config_data.get("subscriber_router")

        widget_id = config.get("id", "h_meter")

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] Spawning HorizontalMeterWithText core for '{widget_id}'", level="TRACE")

        return HorizontalMeterWithText(
            parent=parent_widget,  # Use parent_widget here
            config=config,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router,
        )

    # Creates a VerticalMeter widget.
    # This method instantiates and configures a vertical meter, providing it with
    # configuration details, MQTT topic information, and state management engines.
    # Inputs:
    #     parent_widget: The parent tkinter widget.
    #     config_data (dict): Configuration for the vertical meter.
    #     **kwargs: Additional keyword arguments.
    # Outputs:
    #     VerticalMeter: The created VerticalMeter widget.
    def _create_vertical_meter(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] meter_adapter: Instantiating VerticalMeter '{config_data.get('id', 'Unknown')}'.", level="DEBUG")

        # Extract arguments from config_data
        config = config_data  # config_data is the config
        base_mqtt_topic_from_path = config_data.get("base_mqtt_topic_from_path")
        state_mirror_engine = config_data.get("state_mirror_engine")
        subscriber_router = config_data.get("subscriber_router")

        widget_id = config.get("id", "v_meter")

        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] Spawning VerticalMeter core for '{widget_id}'", level="TRACE")

        return VerticalMeter(
            parent=parent_widget,  # Use parent_widget here
            config=config,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router,
        )
