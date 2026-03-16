from workers.builder.graphing.dynamic_graph import FluxPlotter
from workers.builder.graphing.dynamic_bar_graph import DynamicBarGraph

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()


class PlotWidgetAdapterMixin:
    """Mixin to handle the creation of Plot/Graph widgets."""

    def _create_plot_widget(
        self, parent_widget, config_data, context=None, **kwargs
    ):  # Updated signature
        if BUILDER_DEBUG: builder_logger.debug(f"📊📈📉 [BUILDER] plot_adapter: Spawning FluxPlotter '{config_data.get('path', 'Unknown')}'.")
        # ⚡ HARDENED INTERFACE: Extract from context if available
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
        else:
            state_mirror_engine = kwargs.get("state_mirror_engine")
            subscriber_router = kwargs.get("subscriber_router")
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        config = config_data  # config_data is the config
        widget_id = config.get("path", "plot_widget")
        if BUILDER_DEBUG: builder_logger.trace(f"🏗️📊📈 [CONSTRUCT] Instantiating FluxPlotter core for '{widget_id}'")
        return FluxPlotter(
            parent=parent_widget,  # Use parent_widget here
            config=config,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router,
            builder_instance=self,
        )

    def _create_bar_graph_widget(self, parent_widget, config_data, context=None, **kwargs):
        if BUILDER_DEBUG: builder_logger.debug(f"📊💹📊 [BUILDER] plot_adapter: Spawning DynamicBarGraph '{config_data.get('path', 'Unknown')}'.")
        # ⚡ HARDENED INTERFACE: Extract from context if available
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
        else:
            state_mirror_engine = kwargs.get("state_mirror_engine")
            subscriber_router = kwargs.get("subscriber_router")
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")

        config = config_data  # config_data is the config
        widget_id = config.get("path", "bar_graph")
        if BUILDER_DEBUG: builder_logger.trace(f"🏗️💹📊 [CONSTRUCT] Instantiating DynamicBarGraph core for '{widget_id}'")
        return DynamicBarGraph(
            parent=parent_widget,  # Use parent_widget here
            config=config,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router,
            builder_instance=self,
        )
