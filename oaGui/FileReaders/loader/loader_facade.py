# oaGui/FileReaders/loader_facade.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1001.1
#
# Description: Handles dynamic loading of Python modules and instantiation of GUI classes.

import pathlib

from oaGui.Managers.assembler.engine_widget_instantiator import WidgetInstantiator
from oaGui.Methods.execution.loader_python_engine import LoaderPythonEngine

from .instance_factory import create_gui_instance
from .resource_resolver import resolve_gui_resource


class LoaderFacade:
    """
    Facade for resource resolution and GUI instantiation via atomic services.
    """

    def __init__(self, theme_colors, state_mirror_engine=None, subscriber_router=None, app_instance=None):
        self.theme_colors = theme_colors
        self.state_mirror_engine = state_mirror_engine
        self.subscriber_router = subscriber_router
        self.app_instance = app_instance
        self.instantiator = WidgetInstantiator(
            theme_colors=theme_colors,
            state_mirror_engine=state_mirror_engine,
            subscriber_router=subscriber_router,
            app_instance=app_instance
        )

    def get_all_builders(self):
        """Retrieves active builder instances."""
        return [b for b in self.instantiator.builders if b and b.winfo_exists()]

    def load_module_from_path(self, path: pathlib.Path):
        """Dynamically imports a Python module."""
        return LoaderPythonEngine.load(path)

    def instantiate_widget(self, widget_class, parent_widget, path_ref):
        """Instantiates a widget class."""
        return self.instantiator.instantiate(widget_class, parent_widget)

    def load_and_instantiate_gui(self, path: pathlib.Path, parent_widget, class_filter=None):
        """Loads and builds UI via atomic services."""
        py_path, json_path = resolve_gui_resource(path)
        return create_gui_instance(self, py_path, json_path, parent_widget)
