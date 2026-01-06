from workers.builder.builder_data_graphing.dynamic_graph import FluxPlotter


class PlotWidgetAdapterMixin:
    """Mixin to handle the creation of Plot/Graph widgets."""

    def _create_plot_widget(
        self, parent_widget, config_data, **kwargs
    ):  # Updated signature
        # Extract arguments from config_data
        config = config_data  # config_data is the config
        base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
        state_mirror_engine = kwargs.get("state_mirror_engine")
        subscriber_router = kwargs.get("subscriber_router")

        widget_id = config.get("path", "plot_widget")
        return FluxPlotter(
            parent=parent_widget,  # Use parent_widget here
            config=config,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router,
        )
