# oaGui/Managers/engine_engine_engine_widget_instantiator.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Handles instantiation of GUI widgets and their integration into the layout.

import tkinter as tk
from typing import List

from oaLogging.Methods.matrix_gate import matrix_log
from oaGui.Workers.orchestration.loader_orchestrator import LoaderOrchestrator

class WidgetInstantiator:
    """
    Handles instantiation of GUI widgets and their integration into the layout.
    """

    def __init__(self, theme_colors, state_mirror_engine=None, subscriber_router=None, app_instance=None):
        self.theme_colors = theme_colors
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = subscriber_router
        self.app_instance = app_instance
        self.builders: List[LoaderOrchestrator] = []

    def instantiate(self, widget_class, parent_widget):
        """
        Instantiates a widget class into the parent frame.
        """
        config_dict = {
            "theme_colors": self.theme_colors,
            "state_mirror_engine": self.state_mirror_engine,
            "subscriber_router": self.subscriber_router,
            "mqtt_connection_manager": getattr(self.app_instance, 'mqtt_connection_manager', None),
            "app_instance": self.app_instance,
        }

        # Wrap pure Python modules in a LoaderOrchestrator
        builder = LoaderOrchestrator(parent_widget, json_path=None, config=config_dict)
        self.builders.append(builder)

        # Manually attach based on parent's geometry manager
        try:
            if parent_widget.grid_slaves():
                 builder.grid(row=0, column=0, sticky="nsew")
            else:
                 builder.pack(fill=tk.BOTH, expand=True)
        except tk.TclError:
             builder.pack(fill=tk.BOTH, expand=True)

        builder.start()
        config_dict["builder_instance"] = builder

        # Instantiate the actual Python GUI
        try:
            matrix_log("ui", "gui_builder", "instantiate_widget",
                       f"🔨 Instantiating {widget_class.__name__} (Parent: {parent_widget})", "DEBUG")

            instance = widget_class(builder.scroll_frame, config=config_dict, json_path=None)

            if hasattr(instance, "pack"):
                instance.pack(fill=tk.BOTH, expand=True)
            elif hasattr(instance, "grid"):
                instance.grid(row=0, column=0, sticky="nsew")
        except Exception as e:
            matrix_log("ui", "gui_builder", "instantiate_widget",
                       f"🛑 [ERROR] Failed to instantiate {widget_class.__name__}: {e}", "ERROR")

        return builder
