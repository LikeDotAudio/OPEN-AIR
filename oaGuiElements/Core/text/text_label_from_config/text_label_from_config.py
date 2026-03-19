# text_label_from_config/dynamic_guimake_text_label_from_config.py
#
# A mixin class for the DynamicGuiBuilder that handles creating a label from a config dictionary.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260221.Proxy.1

import os
import inspect

# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

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
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🔡 [BUILDER] Entering make_text_label_from_config")
        
        # ⚡ PROXY: Directly call the standardized implementation
        # Uses the static make method of the concrete label creator
        if BUILDER_DEBUG: builder_logger.trace(f"🔄🚀🔡 [PROXY] Routing label creation to BuilderTextLabelCreator.make")
        return BuilderTextLabelCreator.make(parent_widget, config_data, context=context, **kwargs)

    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        creator = BuilderTextLabelFromConfigCreator()
        return creator.make_text_label_from_config(parent_widget, config_data, context, **kwargs)
