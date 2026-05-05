# Managers/tab_orchestrator.py
# Author: Anthony Peter Kuzub
# Version 20260502.1001.1
#
# Description: Mixin for managing Tkinter Notebook tab events and visibility.

from oaLogging.Methods.matrix_gate import matrix_log
from .tab_lazy_populator import populate_tab_on_demand
from .tab_visibility_dispatcher import dispatch_tab_visibility_events
from .tab_editor_launcher import launch_tab_editor

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
            if "tab" not in element:
                return

            index = notebook.index(f"@{event.x},{event.y}")
            tab_id = notebook.tabs()[index]
            tab_frame = notebook.nametowidget(tab_id)
            launch_tab_editor(self, tab_frame)
        except Exception:
            from oaLogging.Entry import vocal_capture
            vocal_capture("UI", "Failed to trigger WYSIWYG editor from right-click.")
