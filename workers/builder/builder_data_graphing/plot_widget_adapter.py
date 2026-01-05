from workers.builder.builder_data_graphing.dynamic_graph import FluxPlotter

class PlotWidgetAdapterMixin:
    """Mixin to handle the creation of Plot/Graph widgets."""
    
    def _create_plot_widget(self, parent_frame, config, base_mqtt_topic_from_path, state_mirror_engine, subscriber_router, **kwargs):
        widget_id = config.get("id", "plot_widget")
        return FluxPlotter(
            parent=parent_frame,
            config=config,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router
        )
