# oaGuiBuilder/Core/base_widget_creator.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Modular.1
#
# Description: Template Method base class for all UI widget creators.
# Standardizes extraction, registration, and industrial background synchronization.

import tkinter as tk

from oaGuiManager.Core.transparency.transparency_mixin import TransparencyMixin
from oaLogging.Core.logger import BUILDER_LOGGER


class BaseWidgetCreator(TransparencyMixin):
    """
    Template Method orchestrator for constructing GUI widgets.
    Decomposes monolithic build logic into specialized initialization phases.
    """

    # ⚡ COMPOSITE FLAG: Subclasses can set this to True to bypass automatic ghost box
    # generation and handle ghosting recursively in their _assemble_ui.
    is_composite = False

    @classmethod
    def build(cls, parent_widget, config_data, context=None, **kwargs):
        """
        Main entry point for widget construction.
        Coordinates assembly, synchronization, and system registration.
        """
        instance = cls()

        # 1. Resolve Construction Context
        ctx = cls._resolve_context(context, kwargs)

        # ⚡ ROBUSTNESS: Handle case where ctx['builder'] might be None
        builder = ctx.get('builder')
        render_tier = kwargs.get('render_tier') or (getattr(builder, '_render_tier', 'high_res') if builder else 'high_res')

        path = config_data.get("path")
        label = config_data.get("label_active") or config_data.get("label", "Unknown")

        try:
            # 2. UI Assembly Phase
            # ⚡ GHOST BYPASS: Standard widgets show a box; composite widgets descend.
            if render_tier == 'ghost' and not instance.is_composite:
                widget, canvas = instance._assemble_ghost_ui(parent_widget, config_data, context, **kwargs)
            else:
                result = instance._assemble_ui(parent_widget, config_data, context, **kwargs)
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
                instance.register_for_bg_sync(widget, canvas, config_data, context)

                # Global State & Communication Registration
                if path and ctx['mirror']:
                    cls._register_with_system(widget, path, config_data, ctx, kwargs)

            return widget

        except Exception as e:
            BUILDER_LOGGER.exception(f"{cls.__name__}: Error building widget '{label}' at {path}: {e}")
            return None

    @staticmethod
    def _resolve_context(context, kwargs):
        """Extracts and standardizes various engine references from the construction context."""
        return {
            "builder": getattr(context, 'builder_instance', None) if context else kwargs.get('builder_instance'),
            "mirror": getattr(context, 'state_mirror_engine', None) if context else kwargs.get('state_mirror_engine'),
            "router": getattr(context, 'subscriber_router', None) if context else kwargs.get('subscriber_router'),
            "topic": getattr(context, 'base_mqtt_topic_from_path', None) if context else kwargs.get('base_mqtt_topic_from_path')
        }

    @classmethod
    def _register_with_system(cls, widget, path, config, ctx, kwargs):
        """Registers the widget variable with the State Mirror and MQTT router."""
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

    def _assemble_ui(self, parent_widget, config_data, context, **kwargs):
        """Subclasses MUST implement this to return (widget, main_canvas_or_none)."""
        raise NotImplementedError("Subclasses must implement _assemble_ui")

    def _assemble_ghost_ui(self, parent_widget, config_data, context, **kwargs):
        """
        Industrial Placeholder Rendering (Ghost Mode).
        Renders a lightweight high-contrast box for design-time interaction.
        """
        geom = config_data.get("geometry", {})
        w, h = geom.get("width", 100), geom.get("height", 100)
        label = config_data.get("label", config_data.get("_type", "Unknown"))

        ghost = tk.Frame(parent_widget, width=w, height=h, bg="#333333",
                         highlightbackground="#00FF00", highlightthickness=1)
        ghost.pack_propagate(False)

        tk.Label(ghost, text=label, fg="#00FF00", bg="#333333", font=("Arial", 8, "bold")).pack(pady=(h//4, 0))
        tk.Label(ghost, text=f"{w}x{h}", fg="#aaaaaa", bg="#333333", font=("Arial", 7)).pack()

        return ghost, None
