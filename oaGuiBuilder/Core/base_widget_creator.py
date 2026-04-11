# Core/base_widget_creator.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from oaLogging.Core.logger import BUILDER_LOGGER
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
        builder_instance = getattr(context, 'builder_instance', None) if context else kwargs.get('builder_instance')
        state_mirror_engine = getattr(context, 'state_mirror_engine', None) if context else kwargs.get('state_mirror_engine')
        subscriber_router = getattr(context, 'subscriber_router', None) if context else kwargs.get('subscriber_router')
        base_mqtt_topic = getattr(context, 'base_mqtt_topic_from_path', None) if context else kwargs.get('base_mqtt_topic_from_path')
        
        # ⚡ RENDER TIER: Detect if we are in ghost mode for WYSIWYG editing.
        render_tier = kwargs.get('render_tier') or getattr(builder_instance, '_render_tier', 'high_res')
        
        path = config_data.get("path")
        label = config_data.get("label_active") or config_data.get("label", "Unknown")

        try:
            # 2. Call subclass implementation to assemble UI elements
            if render_tier == 'ghost':
                widget, canvas = instance._assemble_ghost_ui(parent_widget, config_data, context, **kwargs)
            else:
                widget, canvas = instance._assemble_ui(parent_widget, config_data, context, **kwargs)
            
            if not widget:
                return None

            # 3. Centralized Background Synchronization and Transparency
            if render_tier != 'ghost':
                # widget and canvas are already unpacked from the assembly tuple above
                instance.register_for_bg_sync(widget, canvas, config_data, context)

            # 4. Standard MQTT and State Mirror Registration
            # Note: widget here is already unpacked from the assembly tuple
            if path and state_mirror_engine and render_tier != 'ghost':
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
            BUILDER_LOGGER.exception(f"{cls.__name__}: Error building widget '{label}' at {path}: {e}")
            return None

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Subclasses MUST implement this to return (widget, main_canvas_or_none)."""
        raise NotImplementedError("Subclasses must implement _assemble_ui")

    def _assemble_ghost_ui(self, parent_widget, config_data, context, **kwargs):
        """
        Default implementation for Ghost Item rendering.
        Renders a simple box with the name and dimensions of the element.
        """
        geometry = config_data.get("geometry", {})
        width = geometry.get("width", 100)
        height = geometry.get("height", 100)
        label = config_data.get("label", config_data.get("_type", "Unknown"))
        
        # Create a frame as the ghost container
        ghost_frame = tk.Frame(parent_widget, width=width, height=height, bg="#333333", 
                               highlightbackground="#00FF00", highlightthickness=1)
        ghost_frame.pack_propagate(False)
        
        # Add label for the name
        name_lbl = tk.Label(ghost_frame, text=label, fg="#00FF00", bg="#333333", font=("Arial", 8, "bold"))
        name_lbl.pack(pady=(height//4, 0))
        
        # Add label for dimensions
        dim_lbl = tk.Label(ghost_frame, text=f"{width}x{height}", fg="#aaaaaa", bg="#333333", font=("Arial", 7))
        dim_lbl.pack()
        
        return ghost_frame, None
