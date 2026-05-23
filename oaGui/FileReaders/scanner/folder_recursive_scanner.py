# oaGui/FileReaders/folder_recursive_scanner.py
# Author: Anthony Peter Kuzub
# Version: 1.0.2
#
# Description: Handles recursively building the GUI structure from a directory structure.

import pathlib

from loguru import logger

from oaGui.Workers.layout_building.default_layout_builder import DefaultLayoutBuilder
from oaGui.Workers.layout_building.multi_window_builder import MultiWindowBuilder
from oaGui.Workers.layout_building.notebook_layout_builder import NotebookLayoutBuilder
from oaGui.Workers.layout_building.recursive_layout_builder import RecursiveLayoutBuilder
from oaGui.Workers.layout_building.split_layout_builder import SplitLayoutBuilder
from oaLogging.Methods.matrix_gate import matrix_log

from .layout_info_service import retrieve_cached_layout_info
from .widget_attachment_service import attach_widget_to_parent


class FolderRecursiveScannerMixin:
    """
    Handles recursively building the GUI structure from a directory structure.
    """

    def _initialize_layout_builders(self):
        """Registry of layout builders for modular UI construction."""
        self._layout_builders = {
            "multi_window": MultiWindowBuilder(self),
            "horizontal_split": SplitLayoutBuilder(self),
            "vertical_split": SplitLayoutBuilder(self),
            "notebook": NotebookLayoutBuilder(self),
            "monitors": RecursiveLayoutBuilder(self),
            "recursive_build": RecursiveLayoutBuilder(self)
        }
        self._default_builder = DefaultLayoutBuilder(self)

    def _get_layout_info(self, path: pathlib.Path):
        """Retrieves layout information via atomic service."""
        return retrieve_cached_layout_info(self, path)

    def _add_instance_to_parent(self, parent, instance, index=0):
        """Safely adds a widget instance via atomic service."""
        attach_widget_to_parent(parent, instance, index)

    def _build_from_directory(self, path: pathlib.Path, parent_widget, on_complete=None, layout_override=None):
        """Recursively builds the GUI via a modular dispatcher."""
        matrix_log("gui", "gui_builder", "_build_from_directory", f"🏗️ [BUILDER] Starting build for: {path}", "DEBUG")

        if not hasattr(self, '_layout_builders'):
            self._initialize_layout_builders()

        if isinstance(path, str):
            path = pathlib.Path(path)

        layout_info = layout_override and self.layout_parser.parse_layout_data(layout_override, source_path=path) or self._get_layout_info(path)

        layout_type = layout_info["type"]
        layout_data = layout_info["data"]

        if layout_type == "error":
            logger.error(f"❌🔴 Layout parsing failed for {path}: {layout_data.get('error_message')}")
            if on_complete: on_complete()
            return

        builder = self._layout_builders.get(layout_type, self._default_builder)

        try:
            builder.build(path, parent_widget, layout_data, on_complete)
        except Exception:
            from oaLogging.Methods.matrix_gate import is_debug_allowed
            if is_debug_allowed(system="gui", element="gui_builder"):
                logger.exception(f"❌🔴 Build failure for {path} ({layout_type})")
            if on_complete: on_complete()
