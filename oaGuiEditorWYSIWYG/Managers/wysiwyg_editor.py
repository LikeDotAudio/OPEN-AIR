# oaGuiEditorWYSIWYG/Managers/wysiwyg_editor.py
# Author: Anthony Peter Kuzub / Gemini CLI
# Version: 20260416.0230.1
#
# Description: High-level orchestrator for the modular WYSIWYG Definition Editor.

import pathlib
import tkinter as tk

from oaComBroker.Core.event_bus import event_bus
from oaLogging.Methods.matrix_gate import matrix_log

from ..Core.state import state_manager
from ..FileReaders.file_reader import FileReader
from ..FileWriters.file_writer import FileWriter
from ..Interface.Window.editor_layout import EditorLayoutBuilder
from ..Interface.Window.editor_menus import EditorMenuBuilder


class WysiwygEditor:
    """
    Main Controller for the GUI Definition Builder.
    Coordinates state, UI assembly, menus, and file operations.
    """
    _instance = None

    @classmethod
    def launch(cls, parent_window, json_filepath=None, config_data=None, **kwargs):
        """
        Standard static launcher to prevent multiple instances.
        Focuses existing instance if available.
        """
        if not kwargs.get('is_standalone') and cls._instance and cls._instance._is_alive():
            cls._instance._refocus(json_filepath, config_data)
            return cls._instance

        matrix_log("ui", "gui_builder", "launch", f"🚀🚀🚀 [LAUNCHING] WysiwygEditor: New instance for {json_filepath}", "INFO")
        return cls(parent_window, json_filepath, config_data, **kwargs)

    def __init__(self, parent_window, json_filepath=None, config_data=None, on_test_callback=None, on_save_callback=None, is_standalone=False):
        self.parent = parent_window
        self.on_test = on_test_callback
        self.on_save = on_save_callback
        self.is_standalone = is_standalone

        # 1. Initialize Global Editor State
        state_manager.initialize(config_data, pathlib.Path(json_filepath) if json_filepath else None)

        # 2. Build UI Components
        self._initialize_window()
        EditorLayoutBuilder.assemble(self)
        EditorMenuBuilder.build(self)

        # 3. Wire Event Bus
        self._subscribe_events()

        if not is_standalone:
            WysiwygEditor._instance = self

    def _initialize_window(self):
        """Sets up the editor window (Toplevel or standalone Root)."""
        if self.is_standalone:
            self.window = self.parent
        else:
            self.window = tk.Toplevel(self.parent)

        title_suffix = state_manager.get_file_path().name if state_manager.get_file_path() else 'Unsaved'
        self.window.title(f"WYSIWYG Editor - {title_suffix}")
        self.window.geometry("1400x900")
        self.window.configure(bg="#2b2b2b")
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)

    def _subscribe_events(self):
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)
        event_bus.subscribe("CHANGES_PENDING", self._on_changes_pending)

    def _unsubscribe_events(self):
        event_bus.unsubscribe("FOCUS_REQUESTED", self._on_focus_requested)
        event_bus.unsubscribe("CHANGES_PENDING", self._on_changes_pending)

    def _is_alive(self):
        return hasattr(self, 'window') and self.window.winfo_exists()

    def _refocus(self, json_filepath, config_data):
        """Brings an existing editor to the front and re-initializes state."""
        self.window.lift()
        self.window.focus_set()
        matrix_log("ui", "gui_builder", "launch", "🚀🚀🚀 [LAUNCHING] WysiwygEditor: Focusing existing instance.", "INFO")
        state_manager.initialize(config_data, pathlib.Path(json_filepath) if json_filepath else None)

    def _on_changes_pending(self, count):
        if hasattr(self, 'status_bar'):
            self.status_bar.set_changes(count)

    def _on_focus_requested(self, path, source=None):
        if hasattr(self, 'status_bar'):
            self.status_bar.set_status(f"Focused: {path}")
        if hasattr(self, 'props_tab'):
            self.props_tab.highlight_item(path)

    def close_window(self):
        """Lifecycle hook for closing the editor window."""
        matrix_log("ui", "gui_builder", "close_window", "🛑🛑🛑 [STOPPED] WysiwygEditor: Shutdown Initiated.", "INFO")
        self.shutdown()

    def save_workspace(self):
        """Triggers the persistence layer to save current definition."""
        matrix_log("ui", "gui_builder", "save", "🖱️🖱️🖱️ [ACTION] WysiwygEditor: Manual Save Triggered", "INFO")
        if FileWriter.save_file(on_save_callback=self.on_save):
            self.status_bar.set_status("Saved successfully!", "#00ff00")
            return True
        self.status_bar.set_status("SAVE FAILED!", "#ff3333")
        return False

    def new_workspace(self):
        """Forces the user to Save As, then creates an empty canvas."""
        matrix_log("ui", "gui_builder", "new", "🖱️🖱️🖱️ [ACTION] WysiwygEditor: NEW WORKSPACE triggered.", "INFO")

        # 1. Force Save As (User MUST pick a file name)
        if FileWriter.save_as(on_save_callback=self.on_save):
            # 2. Reset State to empty structure
            state_manager.initialize({}, state_manager.get_file_path())

            # 3. Update UI
            new_path = state_manager.get_file_path()
            if not self.is_standalone:
                self.window.title(f"WYSIWYG Editor - {new_path.name if new_path else 'Unsaved'}")
            self.status_bar.set_status(f"New Workspace: {new_path.name if new_path else 'Unknown'}", "#00ffcc")

            if hasattr(self, 'layout_view'):
                self.layout_view._manual_rebuild()
            return True

        # User cancelled Save As or it failed
        self.status_bar.set_status("NEW WORKSPACE CANCELLED - Save required.", "#ff8800")
        return False

    def _save_and_close(self):
        """Saves current state and then closes the editor instance."""
        matrix_log("ui", "gui_builder", "save_close", "🖱️🖱️🖱️ [ACTION] WysiwygEditor: 'Save & Close' triggered.", "INFO")
        if self.save_workspace():
            self.close_window()

    def open_workspace(self):
        """Triggers the loading layer to open a new definition."""
        matrix_log("ui", "gui_builder", "open", "🖱️🖱️🖱️ [ACTION] WysiwygEditor: Open operation triggered.", "INFO")
        if FileReader.open_file():
            new_path = state_manager.get_file_path()
            if not self.is_standalone:
                self.window.title(f"WYSIWYG Editor - {new_path.name if new_path else 'Unsaved'}")
            self.status_bar.set_status(f"Opened: {new_path.name if new_path else 'Unknown'}", "#33A1FD")
            if hasattr(self, 'layout_view'):
                self.layout_view._manual_rebuild()
            return True
        return False

    def abandon_changes(self):
        """Exits the editor without saving, optionally notifying external listeners."""
        matrix_log("ui", "gui_builder", "abandon", "🖱️🖱️🖱️ [ACTION] WysiwygEditor: 'ABANDON CHANGES' triggered.", "INFO")
        if self.on_test:
            orig = state_manager.get_original_state()
            if orig: self.on_test(orig)
        self.close_window()

    def _test_config(self):
        """Triggers a preview/rebuild in external applications."""
        matrix_log("ui", "gui_builder", "test", "🎨🎨🎨 [RENDER] WysiwygEditor: Rebuilding main UI...", "INFO")
        if self.on_test:
            self.on_test(state_manager.get_state())
            self.status_bar.set_status("Main UI Rebuilt", "#FF9900")

    def change_language(self, lang_code):
        """Updates the global system language and triggers a preview refresh."""
        from oaConfigurationManager.FileReaders.config_reader import Config
        config = Config.get_instance()
        config.SYSTEM_LANGUAGE = lang_code
        matrix_log("ui", "gui_builder", "language", f"🌐🌐🌐 [CONFIG] System language changed to: {lang_code}", "INFO")

        # Trigger a rebuild of the interactive layout to see translations
        if hasattr(self, 'layout_view'):
            self.layout_view._manual_rebuild()
            self.status_bar.set_status(f"Language set to: {lang_code}", "#00ffcc")

    def shutdown(self):
        """Full cleanup of resources, event subscriptions, and state."""
        matrix_log("ui", "gui_builder", "shutdown", "🛑🛑🛑 [STOPPED] WysiwygEditor: Shutdown sequence initiated.", "INFO")
        self._unsubscribe_events()
        state_manager.reset()

        try:
            self.window.destroy()
        except Exception:
            pass

        WysiwygEditor._instance = None
        matrix_log("ui", "gui_builder", "close_window", "🛑🛑🛑 [STOPPED] WysiwygEditor: Editor Closed.", "INFO")
