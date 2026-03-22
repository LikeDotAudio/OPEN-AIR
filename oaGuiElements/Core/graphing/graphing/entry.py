# graphing/entry.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: entry.py

from oaLogging.Core.logger import builder_logger
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry
from .adapters.plot_adapter import PlotAdapter
from .adapters.bar_graph_adapter import BarGraphAdapter

@WidgetRegistry.register("plot_widget", "bar_graph", "_GuiGraph")
class GraphEntry:
    """
    Unified Entry Point for all Graphing and Plotting Widgets.
    Handles initial JSON validation and dispatches to specific adapters.
    """

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """Unified entry point for graphing widgets."""
        
        # 1. Validation
        if not GraphEntry._validate_config(config_data):
            builder_logger.error(f"❌ [GRAPH] Validation failed for {config_data.get('id', 'Unknown')}")
            return None

        w_type = config_data.get("type")
        
        if w_type in ["plot_widget", "_GuiGraph"]:
            return PlotAdapter.create(parent_widget, config_data, context, **kwargs)
        elif w_type == "bar_graph":
            return BarGraphAdapter.create(parent_widget, config_data, context, **kwargs)
            
        return None

    @staticmethod
    def _validate_config(config):
        """Validates the incoming JSON structure."""
        if not config: return False
        if "type" not in config: return False
        # Add more deep validation if needed
        return True
