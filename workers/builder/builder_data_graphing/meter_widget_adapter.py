# builder_data_graphing/meter_widget_adapter.py
#
# Mixin to handle the creation of Meter widgets.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1
from workers.builder.builder_data_graphing.Meter_to_display_units import (
    HorizontalMeterWithText,
    VerticalMeter,
)


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
        # Extract arguments from config_data
        config = config_data  # config_data is the config
        base_mqtt_topic_from_path = config_data.get("base_mqtt_topic_from_path")
        state_mirror_engine = config_data.get("state_mirror_engine")
        subscriber_router = config_data.get("subscriber_router")

        widget_id = config.get("id", "h_meter")
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
        # Extract arguments from config_data
        config = config_data  # config_data is the config
        base_mqtt_topic_from_path = config_data.get("base_mqtt_topic_from_path")
        state_mirror_engine = config_data.get("state_mirror_engine")
        subscriber_router = config_data.get("subscriber_router")

        widget_id = config.get("id", "v_meter")
        return VerticalMeter(
            parent=parent_widget,  # Use parent_widget here
            config=config,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router,
        )