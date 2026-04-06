# Core/tab.py
from oaGuiFramework.Methods.i18n_utils import get_text
#
# Handles notebook tab changes, visibility events, and context menu actions.
# Manages the lifecycle of tab populations and inter-widget communication.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260330.1600.1

import tkinter as tk
import pathlib
from loguru import logger
from oaLogging.Methods.matrix_gate import matrix_log

# --- Standard Debug Logging Setup ---

class TabManagerMixin:
    """
    Mixin for managing Tkinter Notebook tab events and visibility.
    """

    def _trigger_initial_tab_selection(self):
        """Triggers _on_tab_change for initially selected tabs."""
        matrix_log("ui", "gui_shell", "_trigger_initial_tab_selection", 
                   "🔍🔵 Triggering initial tab selection for all notebooks.", "DEBUG")
        
        notebooks = getattr(self, '_notebooks', {})
        for notebook_path, notebook_widget in list(notebooks.items()):
            try:
                dummy_event = type("Event", (object,), {"widget": notebook_widget})()
                self._on_tab_change(dummy_event)
            except Exception:
                matrix_log("ui", "gui_shell", "_trigger_initial_tab_selection", 
                           f"❌🔴 Error during initial tab selection for {notebook_path}", "ERROR")

    def _on_tab_change(self, event):
        """Processes tab selection changes and populates lazy-loaded frames."""
        try:
            notebook = event.widget
            selected_tab_id = notebook.select()
            if not selected_tab_id: return
            selected_tab_frame = notebook.nametowidget(selected_tab_id)
            newly_selected_tab_name = notebook.tab(selected_tab_id, "text")
            
            matrix_log("ui", "gui_shell", "_on_tab_change", f"▶️ Tab Selected: {newly_selected_tab_name}", "DEBUG")

            if not getattr(selected_tab_frame, "is_populated", False) and \
               not getattr(selected_tab_frame, "is_populating", False):
                selected_tab_frame.is_populating = True
                build_path = getattr(selected_tab_frame, "build_path", None)
                matrix_log("ui", "gui_shell", "_on_tab_change", f"🏗️ Populating tab {newly_selected_tab_name} from {build_path}", "INFO")
                if build_path:
                    if isinstance(build_path, str): build_path = pathlib.Path(build_path)
                    def _populate():
                        try:
                            self._build_from_directory(path=build_path, parent_widget=selected_tab_frame)
                            selected_tab_frame.is_populated = True
                            matrix_log("ui", "gui_shell", "_on_tab_change", f"✅ Tab {newly_selected_tab_name} population complete.", "SUCCESS")
                        except Exception as ex:
                            matrix_log("ui", "gui_shell", "_on_tab_change", f"❌ Failed to populate tab {newly_selected_tab_name}: {ex}", "ERROR")
                        finally:
                            selected_tab_frame.is_populating = False
                    self.after(10, _populate)
            else:
                matrix_log("ui", "gui_shell", "_on_tab_change", f"ℹ️ Tab {newly_selected_tab_name} already populated or populating.", "DEBUG")

            self.last_selected_tab_name = newly_selected_tab_name
            if selected_tab_frame.winfo_children():
                content_widget = selected_tab_frame.winfo_children()[0]
                if hasattr(content_widget, "_on_tab_selected") and \
                   callable(getattr(content_widget, "_on_tab_selected")):
                    content_widget._on_tab_selected(event)
        except Exception as e:
            matrix_log("ui", "gui_shell", "_on_tab_change", f"❌ Error in _on_tab_change: {e}", "ERROR")

    def _handle_tab_visibility(self, event):
        """Dispatches visibility events to child widgets."""
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
        """Handles right-click on notebook tabs to trigger editor."""
        from oaLogging.Entry import vocal_capture
        try:
            notebook = event.widget
            index = notebook.index(f"@{event.x},{event.y}")
            tab_id = notebook.tabs()[index]
            tab_frame = notebook.nametowidget(tab_id)
            self._trigger_wysiwyg_editor(tab_frame)
        except Exception:
            vocal_capture("UI", "Failed to trigger WYSIWYG editor from right-click.")

    def _trigger_wysiwyg_editor(self, widget):
        """Traverses widget hierarchy to find and invoke the editor."""
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