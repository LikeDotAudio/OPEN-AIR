# Core/base_widget_creator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from loguru import logger
from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin

class BaseWidgetCreator(TransparencyMixin):
    """
    Template Method base class for all UI widget creators.
    Centralizes common extraction, registration, and error handling.
    """

    @classmethod
    def build(cls, parent_widget, config_data, context=None, **kwargs):
        """
        Template Method for constructing a widget.
        """
        instance = cls()
        
        # 1. Standard Context Extraction
        builder_instance = getattr(context, 'builder_instance', None) or kwargs.get('builder_instance')
        state_mirror_engine = getattr(context, 'state_mirror_engine', None) or kwargs.get('state_mirror_engine')
        subscriber_router = getattr(context, 'subscriber_router', None) or kwargs.get('subscriber_router')
        base_mqtt_topic = getattr(context, 'base_mqtt_topic_from_path', None) or kwargs.get('base_mqtt_topic_from_path')
        
        path = config_data.get("path")
        label = config_data.get("label_active") or config_data.get("label", "Unknown")

        try:
            # 2. Call subclass implementation to assemble UI elements
            widget, canvas = instance._assemble_ui(parent_widget, config_data, context, **kwargs)
            
            if not widget:
                return None

            # 3. Centralized Background Synchronization and Transparency
            instance.register_for_bg_sync(widget, canvas, config_data, context)

            # 4. Standard MQTT and State Mirror Registration
            if path and state_mirror_engine:
                variable = getattr(widget, 'variable', None) or kwargs.get('variable')
                if variable:
                    topic = state_mirror_engine.register_widget(
                        path, variable, base_mqtt_topic, config_data, instance=widget
                    )
                    if subscriber_router and topic:
                        subscriber_router.subscribe_to_topic(
                            topic, state_mirror_engine.sync_incoming_mqtt_to_gui
                        )
                    state_mirror_engine.initialize_widget_state(path)

            return widget

        except Exception as e:
            logger.exception(f"❌ {cls.__name__}: Error building widget '{label}' at {path}: {e}")
            return None

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Subclasses MUST implement this to return (widget, main_canvas_or_none)."""
        raise NotImplementedError("Subclasses must implement _assemble_ui")
