# Core/factory/base_widget_creator.py
#
# Template Method base class for all UI widget creators. Standardizes
# extraction, registration, and industrial background synchronization.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your
# specific application can be negotiated. There is no charge to use, modify,
# or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260501.1020.1
#
# This file defines the foundational contract for widget construction in the
# OPEN-AIR system. It employs the Template Method design pattern to enforce a
# standardized assembly lifecycle while allowing subclasses to define specific
# rendering logic. It also handles "Ghost Mode" rendering for high-performance
# design-time layouts.

import tkinter as tk

from oaGui.Constants.builder_constants import GHOST_WIDGET_DEFAULT_SIZE
from oaGui.Workers.compositing.sync_behavior import SyncBehavior
from oaLogging.Core.logger import BUILDER_LOGGER


class BaseWidgetCreator(SyncBehavior):
    """
    Template Method orchestrator for constructing GUI widgets.
    Decomposes monolithic build logic into specialized initialization phases.
    """

    # ⚡ COMPOSITE FLAG: Subclasses can set this to True to bypass automatic ghost box
    # generation and handle ghosting recursively in their _assemble_ui.
    is_composite = False

    @classmethod
    def build(cls, parent_widget, configuration, context=None, **kwargs):
        """
        Main entry point for widget construction.
        
        Coordinates the entire assembly, synchronization, and system 
        registration lifecycle.
        
        Inputs:
            parent_widget (tk.Widget): The parent container in the UI tree.
            configuration (dict): The homogenized schema defining the widget.
            context (object): Shared service context (Builder, Mirror, etc.).
            **kwargs: Additional overrides (e.g., render_tier, variable).
            
        Returns:
            tk.Widget: The constructed widget instance, or None on failure.
            
        Side Effects:
            - Instantiates a new widget in the UI tree.
            - Registers the widget with the State Mirror and MQTT Router.
            - Logs detailed exceptions if construction fails.
        """
        instance = cls()

        # 1. Resolve Construction Context
        ctx = cls._resolve_context(context, kwargs)

        # ⚡ ROBUSTNESS: Handle case where ctx['builder'] might be None
        builder = ctx.get('builder')
        render_tier = kwargs.get('render_tier') or (getattr(builder, '_render_tier', 'high_res') if builder else 'high_res')

        path = configuration.get("path")
        label = configuration.get("label_active") or configuration.get("label", "Unknown")

        try:
            # 2. UI Assembly Phase
            # ⚡ GHOST BYPASS: Standard widgets show a box; composite widgets descend.
            if render_tier == 'ghost' and not instance.is_composite:
                widget, canvas = instance._assemble_ghost_ui(parent_widget, configuration, context, **kwargs)
            else:
                result = instance._assemble_ui(parent_widget, configuration, context, **kwargs)
                # Subclasses should return (widget, canvas) or just widget
                if isinstance(result, tuple):
                    widget, canvas = result
                else:
                    widget, canvas = result, None

            if not widget:
                return None

            # 3. Post-Assembly Lifecycle
            if render_tier != 'ghost':
                # Industrial Background Sync
                instance.register_for_bg_sync(widget, canvas, configuration, context)

                # Global State & Communication Registration
                if path and ctx['mirror']:
                    cls._register_with_system(widget, path, configuration, ctx, kwargs)

            return widget

        except Exception as e:
            BUILDER_LOGGER.exception(f"{cls.__name__}: Error building widget '{label}' at {path}: {e}")
            return None

    @staticmethod
    def _resolve_context(context, kwargs):
        """
        Extracts and standardizes engine references from the construction context.
        
        Inputs:
            context (object): The formal context object.
            kwargs (dict): The caller's keyword arguments.
            
        Returns:
            dict: A mapping of canonical service names to their references.
        """
        return {
            "builder": getattr(context, 'builder_instance', None) if context else kwargs.get('builder_instance'),
            "mirror": getattr(context, 'state_mirror_engine', None) if context else kwargs.get('state_mirror_engine'),
            "router": getattr(context, 'subscriber_router', None) if context else kwargs.get('subscriber_router'),
            "topic": getattr(context, 'base_mqtt_topic_from_path', None) if context else kwargs.get('base_mqtt_topic_from_path')
        }

    @classmethod
    def _register_with_system(cls, widget, path, config, ctx, kwargs):
        """
        Registers the widget variable with the State Mirror and MQTT router.
        
        Inputs:
            widget (tk.Widget): The widget being registered.
            path (str): The unique widget path ID.
            config (dict): Configuration data.
            ctx (dict): Resolved services.
            kwargs (dict): Optional variable override.
            
        Side Effects:
            - Subscribes the MQTT router to the widget's topic.
            - Updates the State Mirror's widget registry.
        """
        variable = getattr(widget, 'variable', None) or kwargs.get('variable')
        if not variable:
            return

        topic = ctx['mirror'].register_widget(
            path, variable, ctx['topic'], config, instance=widget
        )

        if ctx['router'] and topic:
            ctx['router'].subscribe_to_topic(
                topic, ctx['mirror'].sync_incoming_mqtt_to_gui
            )

        ctx['mirror'].initialize_widget_state(path)

    def _assemble_ui(self, parent_widget, configuration, context, **kwargs):
        """
        Abstract method to be implemented by concrete creators.
        
        Returns:
            tuple: (widget, main_canvas_or_none)
        """
        raise NotImplementedError("Subclasses must implement _assemble_ui")

    def _assemble_ghost_ui(self, parent_widget, configuration, context, **kwargs):
        """
        Industrial Placeholder Rendering (Ghost Mode).
        
        Renders a lightweight high-contrast box for design-time interaction.
        This provides instant visual feedback in the WYSIWYG editor without 
        the overhead of high-fidelity rendering.
        
        Returns:
            tuple: (ghost_frame, None)
        """
        geom = configuration.get("geometry", {})
        width = geom.get("width", GHOST_WIDGET_DEFAULT_SIZE)
        height = geom.get("height", GHOST_WIDGET_DEFAULT_SIZE)
        label = configuration.get("label", configuration.get("_type", "Unknown"))

        ghost = tk.Frame(parent_widget, width=width, height=height, bg="#333333",
                         highlightbackground="#00FF00", highlightthickness=1)
        ghost.pack_propagate(False)

        tk.Label(ghost, text=label, fg="#00FF00", bg="#333333", font=("Arial", 8, "bold")).pack(pady=(height//4, 0))
        tk.Label(ghost, text=f"{width}x{height}", fg="#aaaaaa", bg="#333333", font=("Arial", 7)).pack()

        return ghost, None
