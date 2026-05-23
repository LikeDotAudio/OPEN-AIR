# oaGui/Workers/layout_building/default_layout_builder.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Fallback builder for standard directory listings in GUI layouts.

from .base_layout_builder import BaseLayoutBuilder


class DefaultLayoutBuilder(BaseLayoutBuilder):
    """Fallback builder for standard directory listings."""

    def build(self, path, parent_widget, layout_data, on_complete=None):
        sub_dirs = layout_data.get("sub_dirs", [])
        gui_files = layout_data.get("gui_files", [])

        def _process_items(dir_idx=0, file_idx=0):
            if dir_idx < len(sub_dirs):
                self.scanner._build_from_directory(path=sub_dirs[dir_idx]["path"], parent_widget=parent_widget,
                                           on_complete=lambda: _process_items(dir_idx + 1, file_idx))
                return
            if file_idx < len(gui_files):
                instance = self.scanner.loader_facade.load_and_instantiate_gui(path=gui_files[file_idx], parent_widget=parent_widget)
                self.scanner._add_instance_to_parent(parent_widget, instance, file_idx)
                self.scanner.after(1, lambda: _process_items(dir_idx, file_idx + 1))
                return
            if on_complete: on_complete()

        _process_items()
