from workers.builder.builder_data_graphing.Meter_to_display_units import HorizontalMeterWithText, VerticalMeter

class MeterWidgetAdapterMixin:
    """Mixin to handle the creation of Meter widgets."""

    def _create_horizontal_meter(self, parent_widget, config_data): # Updated signature
        # Extract arguments from config_data
        config = config_data # config_data is the config
        base_mqtt_topic_from_path = config_data.get("base_mqtt_topic_from_path")
        state_mirror_engine = config_data.get("state_mirror_engine")
        subscriber_router = config_data.get("subscriber_router")

        widget_id = config.get("id", "h_meter")
        return HorizontalMeterWithText(
            parent=parent_widget, # Use parent_widget here
            config=config,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router
        )

    def _create_vertical_meter(self, parent_widget, config_data): # Updated signature
        # Extract arguments from config_data
        config = config_data # config_data is the config
        base_mqtt_topic_from_path = config_data.get("base_mqtt_topic_from_path")
        state_mirror_engine = config_data.get("state_mirror_engine")
        subscriber_router = config_data.get("subscriber_router")

        widget_id = config.get("id", "v_meter")
        return VerticalMeter(
            parent=parent_widget, # Use parent_widget here
            config=config,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router
        )
