# text_label_from_config/text_label_from_config.py
from oaGuiFramework.Methods.i18n_utils import get_text
# Author: Anthony Peter Kuzub
# Version: 20260221.Proxy.1
#
# Description: A mixin class for the DynamicGuiBuilder that handles creating a label from a config dictionary.

import os
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
import inspect

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaGuiManager.Core.context.widget_context import WidgetContext
from oaGuiManager.Core.factory.widget_registry import WidgetRegistry
from .text_label.text_label import BuilderTextLabelCreator

@WidgetRegistry.register("_LabelFromConfig")
class BuilderTextLabelFromConfigCreator(TransparencyMixin):
    """
    A mixin class that provides a wrapper for creating a label widget
    from a configuration dictionary.
    """

    def make_text_label_from_config(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        """Standardized factory wrapper for creating label widgets."""
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔬🏗️🔡 [BUILDER] Entering make_text_label_from_config", level="TRACE")
    
        # ⚡ PROXY: Directly call the standardized implementation
        # Uses the static make method of the concrete label creator
        matrix_log("UI", "GUI_ELEMENTS", inspect.currentframe().f_code.co_name, f"🔄🚀🔡 [PROXY] Routing label creation to BuilderTextLabelCreator.make", level="TRACE")
        return BuilderTextLabelCreator.make(parent_widget, config_data, context=context, **kwargs)

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderTextLabelFromConfigCreator()
        return creator.make_text_label_from_config(parent_widget, config_data, context, **kwargs)