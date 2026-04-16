# graphing/plot_widget_adapter.py
from oaGui.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

from oaGuiElements.Core.graphing.Methods.dynamic_graph import GraphPlotter
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from oaGuiElements.Core.graphing.Methods.dynamic_bar_graph import DynamicBarGraph

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry

app_constants = Config.get_instance()

@WidgetRegistry.register("plot_widget", "bar_graph", "_GuiGraph")
class BuilderGraphingCreator:
    """Factory for creating Plot/Graph widgets."""

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """Unified entry point for graphing widgets."""
        creator = BuilderGraphingCreator()
        w_type = config_data.get("type")
        if w_type in ["plot_widget", "_GuiGraph", "DynamicGraph"]:
            return creator._create_plot_widget(parent_widget, config_data, context, **kwargs)
        elif w_type in ["bar_graph", "DynamicBarGraph"]:
            return creator._create_bar_graph_widget(parent_widget, config_data, context, **kwargs)
        return None

    def _create_plot_widget(self, parent_widget, config_data, context=None, **kwargs):
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] plot_adapter: Spawning GraphPlotter '{config_data.get('path', 'Unknown')}'.", level="DEBUG")
    
        # ⚡ HARDENED INTERFACE
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
        else:
            builder_instance = kwargs.get("builder_instance")
            state_mirror_engine = kwargs.get("state_mirror_engine") or getattr(builder_instance, "state_mirror_engine", None)
            subscriber_router = kwargs.get("subscriber_router") or getattr(builder_instance, "subscriber_router", None)
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path") or getattr(builder_instance, "base_mqtt_topic_from_path", None)

        widget_id = config_data.get("path", "plot_widget")
        return GraphPlotter(
            parent=parent_widget,
            config=config_data,
            base_mqtt_topic_from_path=base_mqtt_topic_from_path,
            widget_id=widget_id,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router,
            builder_instance=builder_instance,
        )

    def _create_bar_graph_widget(self, parent_widget, config_data, context=None, **kwargs):
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️📊 [BUILDER] plot_adapter: Spawning DynamicBarGraph '{config_data.get('path', 'Unknown')}'.", level="DEBUG")
    
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
        else:
            builder_instance = kwargs.get("builder_instance")
            state_mirror_engine = kwargs.get("state_mirror_engine") or getattr(builder_instance, "state_mirror_engine", None)
            subscriber_router = kwargs.get("subscriber_router") or getattr(builder_instance, "subscriber_router", None)
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path") or getattr(builder_instance, "base_mqtt_topic_from_path", None)

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