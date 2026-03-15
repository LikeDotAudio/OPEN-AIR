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
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

from managers.Display.transparency.transparency_mixin import TransparencyMixin
from managers.Display.context.widget_context import WidgetContext

class BuilderTextLabelFromConfigCreator(TransparencyMixin):
    """
    A mixin class that provides a wrapper for creating a label widget
    from a configuration dictionary.
    """

    def make_text_label_from_config(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        """Standardized factory wrapper for creating label widgets."""
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🔡 [BUILDER] Entering make_text_label_from_config")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")
        
        # ⚡ HARDENED INTERFACE: Extract from context if available
        if BUILDER_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            builder_instance = context.builder_instance
            if BUILDER_DEBUG: builder_logger.debug("✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.")
        else:
            state_mirror_engine = self.state_mirror_engine
            subscriber_router = self.subscriber_router
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path")
            builder_instance = kwargs.get("builder_instance") or self
            if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to self/kwargs.")

        # ⚡ PROXY: Directly call the standardized implementation
        # This mixin is assumed to be combined with BuilderTextLabelCreator in DynamicGuiBuilder
        if hasattr(self, 'make_text_label'):
            if BUILDER_DEBUG: builder_logger.trace(f"🔄🚀🔡 [PROXY] Routing label creation to 'make_text_label'")
            return self.make_text_label(parent_widget, config_data, context=context, **kwargs)
        
        if BUILDER_DEBUG: builder_logger.error("🏗️❌🚫 [ERROR] make_text_label method not found in factory context!")
        return None
