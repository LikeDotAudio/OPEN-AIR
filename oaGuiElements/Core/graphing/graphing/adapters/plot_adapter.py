# adapters/plot_adapter.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from oaGuiElements.Core.graphing.graphing.dynamic_graph import FluxPlotter
from oaLogging.Core.logger import builder_logger

class PlotAdapter:
    """Adapter for creating standard Plot widgets."""

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

        widget_id = config_data.get("path", config_data.get("id", "plot_widget"))
        
        builder_logger.debug(f"🔬🏗️📊 [BUILDER] plot_adapter: Spawning FluxPlotter '{widget_id}'.")
        
        return FluxPlotter(
            parent=parent_widget,
            config=config_data,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router,
            builder_instance=builder_instance,
        )
