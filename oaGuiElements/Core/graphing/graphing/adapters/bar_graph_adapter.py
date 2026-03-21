# adapters/bar_graph_adapter.py
from oaGuiElements.Core.graphing.graphing.dynamic_bar_graph import DynamicBarGraph
from oaLogging.Core.logger import builder_logger

class BarGraphAdapter:
    """Adapter for creating Bar Graph widgets."""

    @staticmethod
    def create(parent_widget, config_data, context=None, **kwargs):
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
        else:
            state_mirror_engine = kwargs.get("state_mirror_engine")
            subscriber_router = kwargs.get("subscriber_router")
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance")

        widget_id = config_data.get("path", config_data.get("id", "bar_graph"))
        
        builder_logger.debug(f"🔬🏗️📊 [BUILDER] bar_graph_adapter: Spawning DynamicBarGraph '{widget_id}'.")
        
        return DynamicBarGraph(
            parent=parent_widget,
            config=config_data,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router,
            builder_instance=builder_instance,
        )
