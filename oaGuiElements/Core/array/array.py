# oaGuiElements/Core/array/array.py
# Author: Anthony Peter Kuzub
# Version: 20260415.2355.1
#
# Description: Generates a data-driven grid of widgets by expanding a blueprint.

import inspect
import tkinter as tk
from typing import Any

from oaConfigurationManager.FileReaders.config_reader import Config
from oaGui.Core.context.cache_widget_context import WidgetContext
from oaGui.Workers.compositing.sync_behavior import SyncBehavior
from oaLogging.Methods.matrix_gate import matrix_log

from oaGui.Managers.interaction.interaction_view_states import InteractionViewStates
from oaGui.Methods.rendering.grid_column_configurator import GridColumnConfigurator
from oaGui.Methods.formatting.array_data_expander import ArrayDataExpander

app_constants = Config.get_instance()

class BuilderArrayCreator(SyncBehavior):
    """
    Main orchestrator for data-driven Array widgets.
    Coordinates container setup, data expansion, and batch rendering handoff.
    """

    @staticmethod
    def make(parent_widget, config_data, context: WidgetContext = None, **kwargs):
        """Factory entry point."""
        return BuilderArrayCreator().create(parent_widget, config_data, context, **kwargs)

    def create(self, parent_widget, config_data, context: WidgetContext = None, **kwargs):
        """Orchestrates the full lifecycle of array widget creation."""
        matrix_log("UI", "GUI_MANAGER", inspect.currentframe().f_code.co_name,
                   f"🧱 ArrayCreator: Initializing data-driven array at {config_data.get('path')}", level="DEBUG")

        # 1. Scaffolding
        main_container = self._setup_scaffolding(parent_widget, config_data, context, **kwargs)
        builder = getattr(context, 'builder_instance', kwargs.get('builder_instance'))
        interaction_view_states = InteractionViewStates(main_container, builder=builder)
        main_container.bind("<Button-3>", interaction_view_states.show_menu)

        # 2. Grid Management
        grid_container = self._setup_grid_container(main_container, config_data, context, interaction_view_states, **kwargs)

        # 3. Data-Driven Expansion
        synthetic_fields = self._expand_data_to_fields(config_data, interaction_view_states)

        # 4. Asynchronous Build Handoff
        self._dispatch_batch_build(grid_container, config_data, synthetic_fields, context, **kwargs)

        return main_container

    def _setup_scaffolding(self, parent, config, context, **kwargs) -> tk.Canvas:
        """Creates and configures the outer shell container."""
        p_bg = "#2b2b2b"
        try: p_bg = parent.cget("bg")
        except: pass

        container = tk.Canvas(parent, bd=0, highlightthickness=0, relief="flat", bg=p_bg)

        geom = config.get("geometry", {})
        width = config.get("width") or geom.get("width")
        height = config.get("height") or geom.get("height")

        if width or height:
            container.grid_propagate(False)
            container.pack_propagate(False)
            if width: container.config(width=width)
            if height: container.config(height=height)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        builder = getattr(context, 'builder_instance', kwargs.get('builder_instance', self))
        self._apply_transparency(container, container, config, builder)
        return container

    def _setup_grid_container(self, parent, config, context, interaction_view_states, **kwargs) -> tk.Canvas:
        """Creates the inner grid container and configures its columns."""
        grid_container = tk.Canvas(parent, bd=0, highlightthickness=0, relief="flat")
        grid_container.grid(row=0, column=0, sticky="nsew")
        grid_container.bind("<Button-3>", interaction_view_states.show_menu)

        builder = getattr(context, 'builder_instance', kwargs.get('builder_instance'))
        self._apply_transparency(grid_container, grid_container, config, builder)

        layout_cols = config.get("layout_columns", 8)
        GridColumnConfigurator.apply_sizing(grid_container, layout_cols, config.get("column_sizing", []))

        return grid_container

    def _expand_data_to_fields(self, config: dict, interaction_view_states: InteractionViewStates) -> dict:
        """Transforms data array into a set of item configurations using the blueprint."""
        data_array = config.get("data", [])
        blueprint = config.get("blueprint", {})
        blocks = config.get("blocks") or config.get("fields")

        if data_array:
            return ArrayDataExpander.expand_blueprint(blueprint, data_array, interaction_view_states)

        return blocks or {}

    def _dispatch_batch_build(self, container, config, fields, context, **kwargs):
        """Hands off the expanded item set to the BatchBuilder engine."""
        if not fields:
            on_complete = getattr(context, 'on_complete', kwargs.get('on_complete'))
            if on_complete: on_complete()
            return

        batch_config = {
            "type": "OcaBlock",
            "layout_columns": config.get("layout_columns", 8),
            "column_sizing": config.get("column_sizing", []),
            "fields": fields,
            "show_label": False,
            "layout": config.get("layout", {})
        }

        builder = getattr(context, 'builder_instance', kwargs.get('builder_instance'))
        if builder:
            builder._create_dynamic_widgets(
                container, batch_config,
                path_prefix=config.get("path", ""),
                on_complete=getattr(context, 'on_complete', kwargs.get('on_complete')),
                context=context
            )
