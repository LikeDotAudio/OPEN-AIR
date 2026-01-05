from workers.builder.builder_data_graphing.Meter_to_display_units import HorizontalMeterWithText, VerticalMeter

class MeterWidgetAdapterMixin:
    """Mixin to handle the creation of Meter widgets."""

    def _create_horizontal_meter(self, parent_frame, config, base_mqtt_topic_from_path, state_mirror_engine, subscriber_router, **kwargs):
        widget_id = config.get("id", "h_meter")
        return HorizontalMeterWithText(
            parent=parent_frame,
            config=config,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router
        )

    def _create_vertical_meter(self, parent_frame, config, base_mqtt_topic_from_path, state_mirror_engine, subscriber_router, **kwargs):
        widget_id = config.get("id", "v_meter")
        return VerticalMeter(
            parent=parent_frame,
            config=config,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router
        )
