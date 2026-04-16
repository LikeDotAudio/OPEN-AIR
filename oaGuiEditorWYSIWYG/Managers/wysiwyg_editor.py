# Managers/wysiwyg_editor.py
#
# Main Entry Point for the modular WYSIWYG Definition Builder.
# Orchestrates interactive layout, property editing, and JSON serialization.
#
# Author: Gemini CLI (Contributor to this project)
# Version: 20260405.1700.1

import tkinter as tk
from tkinter import ttk
import pathlib
from oaLogging.Core.logger import WYSIWYG_LOGGER
logger = WYSIWYG_LOGGER.bind(protocol="WYSIWYG")
from oaLogging.Methods.matrix_gate import matrix_log

# Import Modular Components
from oaComBroker.Core.event_bus import event_bus
from ..Core.state import state_manager
from ..Core.file_io_handler import FileIOHandler
from ..Core.workspaces.interactive_layout import InteractiveLayout
from ..Core.workspaces.json_editor import JsonEditor
from ..Core.workspaces.tree_refactor import TreeRefactor
from ..Core.workspaces.element_properties import ElementProperties
from ..Methods.grab_bag.grab_bag_view import GrabBagView

from oaConfigurationManager.FileReaders.config_reader import Config
app_constants = Config.get_instance()

class WysiwygEditor:
    """The modular GUI definition editor."""
    _instance = None

    @classmethod
    def launch(cls, parent_window, json_filepath=None, config_data=None, on_test_callback=None, on_save_callback=None, is_standalone=False):
        """Standard static launcher for the editor."""
        
        # SINGLETON ENFORCEMENT
        if not is_standalone and cls._instance and hasattr(cls._instance, 'window') and cls._instance.window.winfo_exists():
            inst = cls._instance
            inst.window.lift()
            inst.window.focus_set()
            matrix_log("ui", "gui_builder", "launch", "🚀🚀🚀 [LAUNCHING] WysiwygEditor: Switching context to new data in existing instance.", "INFO")
            state_manager.initialize(config_data, pathlib.Path(json_filepath) if json_filepath else None)
            return

        matrix_log("ui", "gui_builder", "launch", f"🚀🚀🚀 [LAUNCHING] WysiwygEditor: Launching new editor instance for {json_filepath} (Standalone: {is_standalone})", "INFO")
        return cls(parent_window, json_filepath, config_data, on_test_callback, on_save_callback, is_standalone)

    def __init__(self, parent_window, json_filepath=None, config_data=None, on_test_callback=None, on_save_callback=None, is_standalone=False):
        self.parent = parent_window
        self.on_test = on_test_callback
        self.on_save = on_save_callback
        self.is_standalone = is_standalone
        
        # Initialize State Manager
        state_manager.initialize(config_data, pathlib.Path(json_filepath) if json_filepath else None)
        
        # Build UI
        self._build_ui()
        
        # Subscribe to internal events
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)
        
        if not is_standalone:
            WysiwygEditor._instance = self

    def _build_ui(self):
        """Builds the main interface with 20/80 split."""
        matrix_log("ui", "gui_builder", "_build_ui", "🎨🎨🎨 [RENDER] WysiwygEditor: Starting UI build...", "DEBUG")
        
        if self.is_standalone:
            self.window = self.parent
        else:
            self.window = tk.Toplevel(self.parent)
            
        # Standard Window Configuration
        self.window.title(f"WYSIWYG Editor - {state_manager.get_file_path().name if state_manager.get_file_path() else 'Unsaved'}")
        self.window.geometry("1400x900")
        self.window.configure(bg="#2b2b2b")
        
        # INTERCEPT WM_DELETE_WINDOW to ensure clean cleanup
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Main Toolbar (DEPRECATED - Moved to Menubar)
        # matrix_log("ui", "gui_builder", "_build_ui", "🎨🎨🎨 [RENDER] WysiwygEditor: Creating Toolbar...", "DEBUG")
        
        # Standard Menu Bar
        self.menubar = tk.Menu(self.window)
        self.window.config(menu=self.menubar)
        
        # 1. FILE MENU
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_workspace, accelerator="Ctrl+O")
        file_menu.add_command(label="Save & Backup", command=self.save_workspace, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Abandon Changes", command=self.abandon_changes)
        file_menu.add_command(label="Save & Close", command=self._save_and_close)
        self.menubar.add_cascade(label="FILE", menu=file_menu)
        
        # 2. TEST MENU
        test_menu = tk.Menu(self.menubar, tearoff=0)
        test_menu.add_command(label="Test UI", command=self._test_config, accelerator="F5")
        self.menubar.add_cascade(label="TEST", menu=test_menu)

        # Status Bar (Bottom)
        self.status_frame = tk.Frame(self.window, bg="#007acc", height=22)
        self.status_frame.pack(side="bottom", fill="x")
        
        self.status_lbl = tk.Label(self.status_frame, text="Modular Editor Active", 
                                   bg="#007acc", fg="white", font=("Arial", 8, "bold"))
        self.status_lbl.pack(side="left", padx=10)
        
        self.pending_lbl = tk.Label(self.status_frame, text="Changes: 0", 
                                    bg="#007acc", fg="white", font=("Arial", 8))
        self.pending_lbl.pack(side="right", padx=10)

        # Subscribe to change counts for status bar
        event_bus.subscribe("CHANGES_PENDING", self._on_changes_pending)

        # PANED WINDOW FOR SIDEBAR | CANVAS | PROPERTIES
        matrix_log("ui", "gui_builder", "_build_ui", "🎨🎨🎨 [RENDER] WysiwygEditor: Initializing Main PanedWindow...", "DEBUG")
        self.main_pane = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, bg="#2b2b2b", sashwidth=6, bd=0)
        self.main_pane.pack(fill="both", expand=True, padx=5, pady=5)

        # 1. LEFT SIDE: Tools Notebook (Structure/Code/Library)
        matrix_log("ui", "gui_builder", "_build_ui", "🎨🎨🎨 [RENDER] WysiwygEditor: Initializing Left Sidebar...", "DEBUG")
        self.left_sidebar = tk.Frame(self.main_pane, bg="#252526")
        self.main_pane.add(self.left_sidebar, width=300)
        
        self.left_notebook = ttk.Notebook(self.left_sidebar)
        self.left_notebook.pack(fill="both", expand=True)
        
        # Initialize library cache once
        from ..FileReaders.grab_bag_loader import GrabBagLoader
        self.global_library = GrabBagLoader().scan_library()

        # Structure Tab
        self.tree_tab = TreeRefactor(self.left_notebook)
        self.left_notebook.add(self.tree_tab, text=" Structure ")
        
        # JSON Code Tab
        self.code_tab = JsonEditor(self.left_notebook)
        self.left_notebook.add(self.code_tab, text=" JSON Code ")
        
        # Library Tab
        self.grab_tab = GrabBagView(self.left_notebook, library_cache=self.global_library)
        self.left_notebook.add(self.grab_tab, text=" Library ")

        # 2. CENTER: Interactive Layout
        matrix_log("ui", "gui_builder", "_build_ui", "🎨🎨🎨 [RENDER] WysiwygEditor: Initializing Center Canvas...", "DEBUG")
        self.layout_container = tk.Frame(self.main_pane, bg="#1a1a1a")
        self.main_pane.add(self.layout_container, stretch="always")
        
        self.layout_view = InteractiveLayout(self.layout_container)
        self.layout_view.pack(fill="both", expand=True)
        
        # ⚡ CONSOLIDATION: Fill RENDER/GRID/VIEW menus from layout view
        self.layout_view.fill_menus(self.menubar)

        # 3. RIGHT SIDE: Properties
        matrix_log("ui", "gui_builder", "_build_ui", "🎨🎨🎨 [RENDER] WysiwygEditor: Initializing Right Sidebar (Properties)...", "DEBUG")
        self.right_sidebar = tk.Frame(self.main_pane, bg="#2d2d2d")
        self.main_pane.add(self.right_sidebar, width=300, stretch="never")
        
        self.props_tab = ElementProperties(self.right_sidebar, library_cache=self.global_library)
        self.props_tab.pack(fill="both", expand=True)

        # ⚡ SASH SPACING: Set initial split (20/60/20)
        # We must wait for the window to be mapped or use specific widths.
        # Based on 1400 geometry: 280 | 840 | 280
        self.window.update_idletasks()
        try:
            self.main_pane.sash_place(0, 300, 0)
            self.main_pane.sash_place(1, 1100, 0)
        except:
             # Fallback if window not ready
             pass
        
        matrix_log("ui", "gui_builder", "_build_ui", "🎨🎨🎨 [RENDER] WysiwygEditor: UI Build Complete.", "INFO")

    def _on_changes_pending(self, count):
        """Updates the status bar change counter."""
        if hasattr(self, 'pending_lbl') and self.pending_lbl.winfo_exists():
            self.pending_lbl.config(text=f"Changes: {count}")
            self.pending_lbl.config(fg="white" if count == 0 else "#FF9900")

    def close_window(self):
        """Explicitly cleans up and destroys the UI window."""
        matrix_log("ui", "gui_builder", "close_window", "🛑🛑🛑 [STOPPED] WysiwygEditor: Shutdown Sequence Initiated.", "INFO")
        event_bus.unsubscribe("FOCUS_REQUESTED", self._on_focus_requested)
        
        # Reset State Manager to avoid cross-pollination on relaunch
        matrix_log("ui", "gui_builder", "close_window", "🧹🧹🧹 [SWEEPING] WysiwygEditor: Resetting StateManager...", "DEBUG")
        state_manager.reset()

        # Destroy window
        try:
            matrix_log("ui", "gui_builder", "close_window", "🧹🧹🧹 [SWEEPING] WysiwygEditor: Destroying Window...", "DEBUG")
            self.window.destroy()
        except:
            pass
            
        # Reset instance
        WysiwygEditor._instance = None
        matrix_log("ui", "gui_builder", "close_window", "🛑🛑🛑 [STOPPED] WysiwygEditor: Editor Closed.", "INFO")

    def _on_focus_requested(self, path, source=None):
        """Visual feedback for item selection."""
        if not hasattr(self, 'status_lbl') or not self.status_lbl.winfo_exists():
            return
            
        self.status_lbl.config(text=f"Focused: {path}")
        
        # ⚡ HIGHLIGHT: Visual feedback in the properties sidebar
        if hasattr(self, 'props_tab') and hasattr(self.props_tab, 'highlight_item'):
            self.props_tab.highlight_item(path)

    def save_workspace(self):
        """Triggers the File IO handler to serialize the workspace to disk."""
        matrix_log("ui", "gui_builder", "save_workspace", f"🖱️🖱️🖱️ [ACTION] WysiwygEditor: Manual Save Triggered for file: {state_manager.get_file_path()}", "INFO")
        
        # Attempt Save
        if FileIOHandler.save_file(on_save_callback=self.on_save):
            if self.status_lbl.winfo_exists():
                self.status_lbl.config(text="Saved successfully!", foreground="#00ff00")
            return True
        else:
            if self.status_lbl.winfo_exists():
                self.status_lbl.config(text="SAVE FAILED! Check logs.", foreground="#ff3333")
            return False

    def open_workspace(self):
        """Triggers the File IO handler to open a file and refreshes the UI."""
        matrix_log("ui", "gui_builder", "open_workspace", "🖱️🖱️🖱️ [ACTION] WysiwygEditor: Open operation triggered.", "INFO")
        if FileIOHandler.open_file():
            # The file is loaded into StateManager. 
            # InteractiveLayout and other workspaces are subscribed to STATE_UPDATED 
            # but StateManager.initialize broadcasts it already.
            # We just update the window title.
            new_path = state_manager.get_file_path()
            if not self.is_standalone:
                self.window.title(f"WYSIWYG Editor - {new_path.name if new_path else 'Unsaved'}")
            
            if self.status_lbl.winfo_exists():
                self.status_lbl.config(text=f"Opened: {new_path.name if new_path else 'Unknown'}", foreground="#33A1FD")
            
            # Force a rebuild of the interactive layout
            if hasattr(self, 'layout_view'):
                self.layout_view._manual_rebuild()
            
            return True
        return False

    def _save_and_close(self):
        """Saves the file and then closes the editor."""
        matrix_log("ui", "gui_builder", "_save_and_close", "🖱️🖱️🖱️ [ACTION] WysiwygEditor: 'SAVE AND CLOSE' triggered.", "INFO")
        if self.save_workspace():
            self.close_window()

    def abandon_changes(self):
        """Discards all changes, restores original state in the main UI, and closes."""
        matrix_log("ui", "gui_builder", "abandon_changes", "🖱️🖱️🖱️ [ACTION] WysiwygEditor: 'ABANDON CHANGES' triggered.", "INFO")
        
        # 1. Restore original state in main UI if possible
        if self.on_test:
            orig = state_manager.get_original_state()
            if orig:
                matrix_log("ui", "gui_builder", "abandon_changes", "🧹🧹🧹 [SWEEPING] WysiwygEditor: Restoring original state in main application...", "DEBUG")
                self.on_test(orig)
        
        # 2. Close window
        self.close_window()

    def _test_config(self):
        """Triggers the test callback with current master state_manager."""
        matrix_log("ui", "gui_builder", "_test_config", "🎨🎨🎨 [RENDER] WysiwygEditor: Rebuilding main UI with current editor state_manager...", "INFO")
        if self.on_test:
            self.on_test(state_manager.get_state())
            if self.status_lbl.winfo_exists():
                self.status_lbl.config(text="Main UI Rebuilt", foreground="#FF9900")

    def shutdown(self):
        """
        ⚡ V3.1.29 GRACEFUL SHUTDOWN: Orchestrates the safe termination of the 
        editor, ensuring original states are restored if needed.
        """
        matrix_log("ui", "gui_builder", "shutdown", "🛑🛑🛑 [STOPPED] WysiwygEditor: Shutdown sequence initiated.", "INFO")
        self.abandon_changes()
