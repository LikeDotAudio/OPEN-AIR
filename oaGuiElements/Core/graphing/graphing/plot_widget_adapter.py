from oaGuiElements.Core.graphing.graphing.dynamic_graph import FluxPlotter
from oaGuiElements.Core.graphing.graphing.dynamic_bar_graph import DynamicBarGraph

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

app_constants = Config.get_instance()

@WidgetRegistry.register("plot_widget", "bar_graph", "_GuiGraph")
class BuilderGraphingCreator:
    """Factory for creating Plot/Graph widgets."""

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """Unified entry point for graphing widgets."""
        w_type = config_data.get("type")
        if w_type in ["plot_widget", "_GuiGraph"]:
            return BuilderGraphingCreator._create_plot_widget(parent_widget, config_data, context, **kwargs)
        elif w_type == "bar_graph":
            return BuilderGraphingCreator._create_bar_graph_widget(parent_widget, config_data, context, **kwargs)
        return None

    @staticmethod
    def _create_plot_widget(parent_widget, config_data, context=None, **kwargs):
        if BUILDER_DEBUG:
            builder_logger.debug(f"🔬🏗️📊 [BUILDER] plot_adapter: Spawning FluxPlotter '{config_data.get('path', 'Unknown')}'.")
        
        # ⚡ HARDENED INTERFACE
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

        widget_id = config_data.get("path", "plot_widget")
        return FluxPlotter(
            parent=parent_widget,
            config=config_data,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router,
            builder_instance=builder_instance,
        )

    @staticmethod
    def _create_bar_graph_widget(parent_widget, config_data, context=None, **kwargs):
        if BUILDER_DEBUG:
            builder_logger.debug(f"🔬🏗️📊 [BUILDER] plot_adapter: Spawning DynamicBarGraph '{config_data.get('path', 'Unknown')}'.")
        
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

        widget_id = config_data.get("path", "bar_graph")
        return DynamicBarGraph(
            parent=parent_widget,
            config=config_data,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router,
            builder_instance=builder_instance,
        )

class PlotWidgetAdapterMixin:
    """Legacy mixin for backward compatibility."""
    def _create_plot_widget(self, *args, **kwargs):
        return BuilderGraphingCreator._create_plot_widget(*args, **kwargs)
    
    def _create_bar_graph_widget(self, *args, **kwargs):
        return BuilderGraphingCreator._create_bar_graph_widget(*args, **kwargs)
