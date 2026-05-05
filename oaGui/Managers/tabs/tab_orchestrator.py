# Managers/tab_orchestrator.py
# Author: Anthony Peter Kuzub
# Version 20260502.1001.1
#
# Description: Mixin for managing Tkinter Notebook tab events and visibility.

from oaLogging.Methods.matrix_gate import matrix_log
from .tab_lazy_populator import populate_tab_on_demand
from .tab_visibility_dispatcher import dispatch_tab_visibility_events
from .tab_editor_launcher import find_tab_orchestrator

class TabOrchestratorMixin:
    """
    Mixin for managing Tkinter Notebook tab events and visibility using atomic services.
    """

    def _trigger_initial_tab_selection(self):
        """Triggers _on_tab_change for initially selected tabs."""
        matrix_log("gui", "gui_manager", "_trigger_initial_tab_selection",
                   "🔍🔵 Triggering initial tab selection for all notebooks.", "DEBUG")

        notebooks = getattr(self, '_notebooks', {})
        for notebook_path, notebook_widget in list(notebooks.items()):
            try:
                dummy_event = type("Event", (object,), {"widget": notebook_widget})()
                self._on_tab_change(dummy_event)
            except Exception:
                matrix_log("gui", "gui_manager", "_trigger_initial_tab_selection",
                           f"❌🔴 Error during initial tab selection for {notebook_path}", "ERROR")

    def _on_tab_change(self, event):
        """Processes tab selection changes via lazy population service."""
        try:
            notebook = event.widget
            selected_tab_id = notebook.select()
            if not selected_tab_id: return
            
            selected_tab_frame = notebook.nametowidget(selected_tab_id)
            tab_name = notebook.tab(selected_tab_id, "text")

            matrix_log("gui", "gui_manager", "_on_tab_change", f"▶️ Tab Selected: {tab_name}", "DEBUG")

            # ⚡ LAZY POPULATION
            populate_tab_on_demand(self, selected_tab_frame, tab_name)

            self.last_selected_tab_name = tab_name
            
            if selected_tab_frame.winfo_children():
                content_widget = selected_tab_frame.winfo_children()[0]
                if hasattr(content_widget, "_on_tab_selected") and callable(content_widget._on_tab_selected):
                    content_widget._on_tab_selected(event)
                    
        except Exception as e:
            matrix_log("gui", "gui_shell", "_on_tab_change", f"❌ Error in _on_tab_change: {e}", "ERROR")

    def _handle_tab_visibility(self, event):
        """Dispatches visibility events via atomic service."""
        dispatch_tab_visibility_events(event.widget, event)

    def _on_notebook_right_click(self, event):
        """Handles right-click to trigger editor via atomic service."""
        try:
            notebook = event.widget
            # Identify what was clicked (tab, padding, or empty space)
            element = notebook.identify(event.x, event.y)
            matrix_log("gui", "gui_shell", "_on_notebook_right_click", f"🖱️ Notebook right-click at {event.x},{event.y}. Element: {element}", "DEBUG")
            
            # ⚡ ROBUST IDENTIFICATION: Catch 'tab', 'label', 'text' or numeric indices
            is_tab_area = any(s in element for s in ["tab", "label", "text"]) or element.isdigit()
            
            if not is_tab_area:
                return

            index = notebook.index(f"@{event.x},{event.y}")
            tab_id = notebook.tabs()[index]
            tab_frame = notebook.nametowidget(tab_id)
            tab_name = notebook.tab(tab_id, "text")

            matrix_log("gui", "gui_shell", "_on_notebook_right_click", f"🎯 Target Tab: {tab_name} (ID: {tab_id})", "DEBUG")

            # ⚡ ENSURE POPULATED: If the user right-clicks a tab they haven't visited,
            # we must populate it first so the orchestrator exists.
            def _launch_after_population():
                matrix_log("gui", "gui_shell", "_on_notebook_right_click", f"🔍 Searching orchestrator for {tab_name} after population...", "DEBUG")
                orchestrator = find_tab_orchestrator(tab_frame)
                if orchestrator:
                    matrix_log("gui", "gui_shell", "_on_notebook_right_click", f"🚀 Launching editor for {tab_name} via {orchestrator}", "DEBUG")
                    if hasattr(orchestrator, "_show_wysiwyg_editor"):
                        orchestrator._show_wysiwyg_editor()
                    else:
                        matrix_log("gui", "gui_shell", "_on_notebook_right_click", f"❌ Orchestrator {orchestrator} missing _show_wysiwyg_editor!", "WARNING")
                else:
                    matrix_log("gui", "gui_shell", "_on_notebook_right_click", f"❌ Failed to find orchestrator for tab {tab_name}", "WARNING")

            populate_tab_on_demand(self, tab_frame, tab_name, on_complete=_launch_after_population)
        except Exception as e:
            matrix_log("gui", "gui_shell", "_on_notebook_right_click", f"🛑 Tab right-click failure: {e}", "ERROR")
            from oaLogging.Entry import vocal_capture
            vocal_capture("UI", "Failed to trigger WYSIWYG editor from right-click.")
