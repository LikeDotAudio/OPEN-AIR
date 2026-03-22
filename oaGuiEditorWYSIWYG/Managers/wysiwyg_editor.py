# Managers/wysiwyg_editor.py
# Author: Gemini CLI
# Version: 1.0.0
#
# Description: The main Entry Point for the new Modular WYSIWYG Definition Builder.

import tkinter as tk
from tkinter import ttk
import pathlib

# Import Modular Components
from .Core.event_bus import event_bus
from .Core.state import state_manager
from .Core.file_io_handler import FileIOHandler
from .workspaces.interactive_layout import InteractiveLayout
from .workspaces.json_editor import JsonEditor
from .workspaces.tree_refactor import TreeRefactor
from .workspaces.element_properties import ElementProperties
from .grab_bag.grab_bag_view import GrabBagView

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file

app_constants = Config.get_instance()

class WysiwygEditor:
    """The modular GUI definition editor."""
    _instance = None

    def __init__(self, parent_window, config_data, json_filepath, on_test_callback, on_save_callback, is_standalone=False):
        # SINGLETON ENFORCEMENT
        if not is_standalone and WysiwygEditor._instance and hasattr(WysiwygEditor._instance, 'window') and WysiwygEditor._instance.window.winfo_exists():
            inst = WysiwygEditor._instance
            inst.window.lift()
            inst.window.focus_set()
            if LOCAL_DEBUG: logger.info(f"🏗️ WysiwygEditor: Switching context to new data in existing instance: {json_filepath}")
            state_manager.initialize(config_data, pathlib.Path(json_filepath) if json_filepath else None)
            return

        if LOCAL_DEBUG: logger.info(f"🏗️ WysiwygEditor: Launching new editor instance for {json_filepath} (Standalone: {is_standalone})")
        self.parent = parent_window
        self.on_test = on_test_callback
        self.on_save = on_save_callback
        self.is_standalone = is_standalone
        
        self._build_ui()
        
        # Subscribe to focus events AFTER UI is built
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)
        
        # Initialize State AFTER UI is built so subscribers (tabs) receive the event
        state_manager.initialize(config_data, pathlib.Path(json_filepath) if json_filepath else None)
        
        if not is_standalone:
            WysiwygEditor._instance = self

    def _build_ui(self):
        """Builds the main interface with 20/80 split."""
        if LOCAL_DEBUG: logger.debug("🏗️ WysiwygEditor: Starting UI build...")
        
        if self.is_standalone:
            self.window = self.parent
        else:
            self.window = tk.Toplevel(self.parent)

        self.window.title(f"Modular WYSIWYG Definition Builder - {pathlib.Path(state_manager.get_file_path()).name if state_manager.get_file_path() else 'Unsaved'}")
        self.window.geometry("1600x900")
        self.window.configure(bg="#2b2b2b")
        
        # INTERCEPT WM_DELETE_WINDOW to ensure clean cleanup
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Main Toolbar
        if LOCAL_DEBUG: logger.debug("🏗️ WysiwygEditor: Creating Toolbar...")
        toolbar = ttk.Frame(self.window)
        toolbar.pack(side="top", fill="x", padx=5, pady=5)
        
        ttk.Button(toolbar, text="Save & Backup", command=self.save_workspace).pack(side="left", padx=2)
        
        # 🟢 NEW SAVE AND CLOSE BUTTON
        save_close_btn = tk.Button(toolbar, text="SAVE AND CLOSE", bg="#2ecc71", fg="white", 
                             font=("Arial", 8, "bold"), relief="flat", padx=10,
                             command=self._save_and_close)
        save_close_btn.pack(side="left", padx=2)
        
        ttk.Button(toolbar, text="Test in Main UI", command=self._test_config).pack(side="left", padx=2)
        
        # 🔴 NEW CLOSE BUTTON
        close_btn = tk.Button(toolbar, text="CLOSE (Unsaved)", bg="#FF3333", fg="white", 
                             font=("Arial", 8, "bold"), relief="flat", padx=10,
                             command=self.close_window)
        close_btn.pack(side="left", padx=20)
        
        self.status_lbl = ttk.Label(toolbar, text="Modular Editor Active", foreground="#33A1FD")
        self.status_lbl.pack(side="right", padx=10)

        # PANED WINDOW FOR 20/80 SPLIT
        if LOCAL_DEBUG: logger.debug("🏗️ WysiwygEditor: Initializing PanedWindow...")
        self.main_pane = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, bg="#2b2b2b", sashwidth=6, bd=0)
        self.main_pane.pack(fill="both", expand=True, padx=5, pady=5)

        # LEFT SIDE (~25%): Tools Notebook
        if LOCAL_DEBUG: logger.debug("🏗️ WysiwygEditor: Initializing Left Notebook (Code/Props/Library)...")
        self.left_notebook = ttk.Notebook(self.main_pane)
        self.main_pane.add(self.left_notebook, width=430)
        
        # 1. Tree Refactor Tab
        self.tree_tab = TreeRefactor(self.left_notebook)
        self.left_notebook.add(self.tree_tab, text=" Tree ")
        
        # 2. JSON Editor Tab
        self.json_tab = JsonEditor(self.left_notebook)
        self.left_notebook.add(self.json_tab, text=" Code ")
        
        # 3. Element Properties Tab
        self.props_tab = ElementProperties(self.left_notebook)
        self.left_notebook.add(self.props_tab, text=" Props ")
        
        # 4. Grab Bag Tab
        self.grab_tab = GrabBagView(self.left_notebook)
        self.left_notebook.add(self.grab_tab, text=" Library ")

        # RIGHT SIDE (80%): Visual Layout
        if LOCAL_DEBUG: logger.debug("🏗️ WysiwygEditor: Initializing Interactive Layout Canvas...")
        self.layout_container = tk.Frame(self.main_pane, bg="#1a1a1a")
        self.main_pane.add(self.layout_container)
        
        self.layout_view = InteractiveLayout(self.layout_container)
        self.layout_view.pack(fill="both", expand=True)
        
        if LOCAL_DEBUG: logger.info("🏗️ WysiwygEditor: UI Build Complete.")

    def close_window(self):
        """Explicitly cleans up and destroys the UI window."""
        if LOCAL_DEBUG: logger.info("🏗️ WysiwygEditor: Shutdown Sequence Initiated.")
        event_bus.unsubscribe("FOCUS_REQUESTED", self._on_focus_requested)
        
        # Reset State Manager to avoid cross-pollination on relaunch
        if LOCAL_DEBUG: logger.debug("🏗️ WysiwygEditor: Resetting StateManager...")
        state_manager.reset()

        # Destroy window
        try:
            if LOCAL_DEBUG: logger.debug("🏗️ WysiwygEditor: Destroying Window...")
            self.window.destroy()
        except:
            pass
            
        # Reset instance
        WysiwygEditor._instance = None
        if LOCAL_DEBUG: logger.info("🏗️ WysiwygEditor: Editor Closed.")

    def _on_focus_requested(self, path, source=None):
        """Optionally switches tabs when an element is focused."""
        if not hasattr(self, 'status_lbl') or not self.status_lbl.winfo_exists():
            return
            
        self.status_lbl.config(text=f"Focused: {path}")
        # Switch to Props tab (index 2) if focus comes from layout
        if source == self.layout_view:
            if LOCAL_DEBUG: logger.debug(f"🏗️ WysiwygEditor: Focus Event - Switching to Props tab for element at path: {path}")
            self.left_notebook.select(2)

    def save_workspace(self):
        """Triggers the File IO handler to serialize the workspace to disk."""
        if LOCAL_DEBUG: logger.info(f"🏗️ WysiwygEditor: Manual Save Triggered for file: {state_manager.get_file_path()}")
        
        # 🛡️ Attempt Save
        if FileIOHandler.save_file(on_save_callback=self.on_save):
            if self.status_lbl.winfo_exists():
                self.status_lbl.config(text="Saved successfully!", foreground="#00ff00")
            return True
        else:
            if self.status_lbl.winfo_exists():
                self.status_lbl.config(text="SAVE FAILED! Check logs.", foreground="#ff3333")
            return False

    def _save_and_close(self):
        """Saves the file and then closes the editor."""
        if LOCAL_DEBUG: logger.info("🏗️ WysiwygEditor: 'SAVE AND CLOSE' triggered.")
        # SRP REFACTOR: Orchestrate modular actions
        if self.save_workspace():
            self.close_window()

    def _test_config(self):
        """Triggers the test callback with current master state_manager."""
        if LOCAL_DEBUG: logger.info("🏗️ WysiwygEditor: Rebuilding main UI with current editor state_manager...")
        if self.on_test:
            self.on_test(state_manager.get_state())
            if self.status_lbl.winfo_exists():
                self.status_lbl.config(text="Main UI Rebuilt", foreground="#FF9900")
