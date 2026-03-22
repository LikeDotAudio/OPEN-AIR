# Core/tab.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
import pathlib
from loguru import logger

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file

class TabManagerMixin:
    """
    Handles notebook tab changes, visibility events, and context menu actions.
    """

    def _trigger_initial_tab_selection(self):
        """Triggers _on_tab_change for initially selected tabs."""
        if LOCAL_DEBUG: logger.debug("🔍🔵 Triggering initial tab selection for all notebooks.")
        notebooks = getattr(self, '_notebooks', {})
        for notebook_path, notebook_widget in list(notebooks.items()):
            try:
                dummy_event = type("Event", (object,), {"widget": notebook_widget})()
                self._on_tab_change(dummy_event)
            except Exception:
                logger.exception(f"❌🔴 Error during initial tab selection for {notebook_path}")

    def _on_tab_change(self, event):
        if LOCAL_DEBUG: logger.debug("▶️ _on_tab_change detected.")
        try:
            notebook = event.widget
            selected_tab_id = notebook.select()
            if not selected_tab_id: return
            selected_tab_frame = notebook.nametowidget(selected_tab_id)
            newly_selected_tab_name = notebook.tab(selected_tab_id, "text")

            if not getattr(selected_tab_frame, "is_populated", False) and not getattr(selected_tab_frame, "is_populating", False):
                selected_tab_frame.is_populating = True
                build_path = getattr(selected_tab_frame, "build_path", None)
                if build_path:
                    if isinstance(build_path, str): build_path = pathlib.Path(build_path)
                    def _populate():
                        try:
                            self._build_from_directory(path=build_path, parent_widget=selected_tab_frame)
                            selected_tab_frame.is_populated = True
                        finally:
                            selected_tab_frame.is_populating = False
                    self.after(10, _populate)

            self.last_selected_tab_name = newly_selected_tab_name
            if selected_tab_frame.winfo_children():
                content_widget = selected_tab_frame.winfo_children()[0]
                if hasattr(content_widget, "_on_tab_selected") and callable(getattr(content_widget, "_on_tab_selected")):
                    content_widget._on_tab_selected(event)
        except Exception as e:
            if LOCAL_DEBUG: logger.exception("❌ Error in _on_tab_change")

    def _handle_tab_visibility(self, event):
        notebook = event.widget
        selected_tab_id = notebook.select()
        for tab_id in notebook.tabs():
            tab_frame = notebook.nametowidget(tab_id)
            if tab_frame.winfo_children():
                content_widget = tab_frame.winfo_children()[0]
                if tab_id == selected_tab_id:
                    if hasattr(content_widget, "_on_gui_visible"):
                        content_widget._on_gui_visible(event)
                else:
                    if hasattr(content_widget, "_on_gui_hidden"):
                        content_widget._on_gui_hidden(event)

    def _on_notebook_right_click(self, event):
        """Handles right-click on notebook tabs."""
        try:
            notebook = event.widget
            index = notebook.index(f"@{event.x},{event.y}")
            tab_id = notebook.tabs()[index]
            tab_frame = notebook.nametowidget(tab_id)
            self._trigger_wysiwyg_editor(tab_frame)
        except Exception:
            pass

    def _trigger_wysiwyg_editor(self, widget):
        """Traverses widget hierarchy to find and invoke editor."""
        queue = [widget]
        while queue:
            curr = queue.pop(0)
            if hasattr(curr, "_show_wysiwyg_editor"):
                curr._show_wysiwyg_editor()
                return
            if hasattr(curr, "dynamic_gui"):
                if hasattr(curr.dynamic_gui, "_show_wysiwyg_editor"):
                    curr.dynamic_gui._show_wysiwyg_editor()
                    return
            for child in curr.winfo_children():
                queue.append(child)
