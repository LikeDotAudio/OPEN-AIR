# Managers/wysiwyg_editor.py
#
# Main Entry Point for the modular WYSIWYG Definition Builder.
# Orchestrates interactive layout, property editing, and JSON serialization.
#
# Author: Gemini CLI (Contributor to this project)
# Blog: www.Like.audio
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
from tkinter import ttk
import pathlib
from loguru import logger
from oaLogging.Methods.matrix_gate import matrix_log

# Import Modular Components
from ..Core.event_bus import event_bus
from ..Core.state import state_manager
from ..Core.file_io_handler import FileIOHandler
from ..Core.workspaces.interactive_layout import InteractiveLayout
from ..Core.workspaces.json_editor import JsonEditor
from ..Core.workspaces.tree_refactor import TreeRefactor
from ..Core.workspaces.element_properties import ElementProperties
from ..Methods.grab_bag.grab_bag_view import GrabBagView
from .palette_manager import PaletteManager # Added PaletteManager import

from oaConfiguration.FileReaders.config_reader import Config
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
            matrix_log("ui", "gui_builder", "launch", f"WysiwygEditor: Switching context to new data in existing instance: {json_filepath}", "INFO")
            state_manager.initialize(config_data, pathlib.Path(json_filepath) if json_filepath else None)
            return

        matrix_log("ui", "gui_builder", "launch", f"WysiwygEditor: Launching new editor instance for {json_filepath} (Standalone: {is_standalone})", "INFO")
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
        matrix_log("ui", "gui_builder", "_build_ui", "WysiwygEditor: Starting UI build...", "DEBUG")
        
        if self.is_standalone:
            self.window = self.parent
        else:
            self.window = tk.Toplevel(self.parent)
            self.window.title(f"WYSIWYG Editor - {state_manager.get_file_path() or 'Unsaved'}")
            self.window.geometry("1400x900")
            self.window.configure(bg="#2b2b2b")
        
        # INTERCEPT WM_DELETE_WINDOW to ensure clean cleanup
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Main Toolbar
        matrix_log("ui", "gui_builder", "_build_ui", "WysiwygEditor: Creating Toolbar...", "DEBUG")
        toolbar = ttk.Frame(self.window)
        toolbar.pack(side="top", fill="x", padx=5, pady=5)
        
        ttk.Button(toolbar, text="Save & Backup", command=self.save_workspace).pack(side="left", padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side="left", fill="y", padx=10)
        
        ttk.Button(toolbar, text="TEST UI", command=self._test_config).pack(side="left", padx=2)
        ttk.Button(toolbar, text="ABANDON CHANGES", command=self.abandon_changes).pack(side="left", padx=2)
        ttk.Button(toolbar, text="SAVE & CLOSE", command=self._save_and_close).pack(side="left", padx=2)
        
        self.status_lbl = ttk.Label(toolbar, text="Modular Editor Active", foreground="#33A1FD")
        self.status_lbl.pack(side="right", padx=10)

        # PANED WINDOW FOR 20/80 SPLIT
        matrix_log("ui", "gui_builder", "_build_ui", "WysiwygEditor: Initializing PanedWindow...", "DEBUG")
        self.main_pane = tk.PanedWindow(self.window, orient=tk.HORIZONTAL, bg="#2b2b2b", sashwidth=6, bd=0)
        self.main_pane.pack(fill="both", expand=True, padx=5, pady=5)

        # LEFT SIDE (~25%): Tool Palettes Manager
        matrix_log("ui", "gui_builder", "_build_ui", "WysiwygEditor: Initializing Palette Manager (Tree/JSON/Props/Library)...", "DEBUG")
        
        # Create instances of the widgets that will be managed by the PaletteManager
        self.tree_tab = TreeRefactor(self.main_pane) # Parent needs to be the main_pane for potential undocking
        self.code_tab = JsonEditor(self.main_pane)   # Parent needs to be the main_pane for potential undocking
        self.props_tab = ElementProperties(self.main_pane) # Parent needs to be the main_pane for potential undocking
        self.grab_tab = GrabBagView(self.main_pane)  # Parent needs to be the main_pane for potential undocking

        # Instantiate and configure the Palette Manager
        # This is a conceptual replacement. A full PaletteManager implementation would be needed.
        # For now, we'll place them directly in a frame and simulate the palette behavior.
        # A proper PaletteManager would handle dropdowns, expansion, collapse, and undocking.

        self.palette_frame = ttk.Frame(self.main_pane, style="Dark.TFrame") # Use a dark theme style if available
        self.main_pane.add(self.palette_frame, width=430)
        
        # Simplified representation: pack widgets into the frame.
        # A real PaletteManager would manage the visibility and docking of these.
        # For now, we'll assume they are visible or managed by the PaletteManager's internal logic.
        
        # Example of how a PaletteManager might organize them (e.g., using buttons for dropdowns)
        # This part would be heavily customized based on PaletteManager implementation.
        
        # For now, let's just pack them for visibility, acknowledging this is a placeholder
        # for the actual PaletteManager logic.
        
        # In a real implementation, you'd have a structure for collapsible/expandable sections
        # managed by the PaletteManager. For example:
        
        # self.palette_manager = PaletteManager(self.main_pane, [
        #     {"widget": self.tree_tab, "name": "Structure", "icon": "structure.png"},
        #     {"widget": self.code_tab, "name": "JSON Code", "icon": "json.png"},
        #     {"widget": self.props_tab, "name": "Properties", "icon": "props.png"},
        #     {"widget": self.grab_tab, "name": "Library", "icon": "library.png"},
        # ])
        # self.main_pane.add(self.palette_manager.get_widget(), width=430) # Add the manager's widget

        # --- Placeholder for Palette Manager functionality ---
        # Since PaletteManager class is not defined, we'll use a simplified approach for now
        # by packing the widgets into the palette_frame. A full implementation would require
        # defining the PaletteManager class itself.
        
        # Example: Add buttons to expand/collapse or to undock (conceptually)
        
        # Placeholder for structure tab
        structure_header = ttk.Frame(self.palette_frame, style="DarkHeader.TFrame")
        structure_header.pack(fill='x', pady=(0,1))
        ttk.Label(structure_header, text="Structure", style="DarkLabel.TLabel").pack(side='left', padx=5)
        ttk.Button(structure_header, text="[-]", width=2, command=lambda: self.tree_tab.pack_forget() if self.tree_tab.winfo_ismapped() else self.tree_tab.pack(fill='both', expand=True)).pack(side='right', padx=2)
        
        self.tree_tab.pack(fill='both', expand=True)

        # Placeholder for JSON Code tab
        json_header = ttk.Frame(self.palette_frame, style="DarkHeader.TFrame")
        json_header.pack(fill='x', pady=(0,1))
        ttk.Label(json_header, text="JSON Code", style="DarkLabel.TLabel").pack(side='left', padx=5)
        ttk.Button(json_header, text="[-]", width=2, command=lambda: self.code_tab.pack_forget() if self.code_tab.winfo_ismapped() else self.code_tab.pack(fill='both', expand=True)).pack(side='right', padx=2)
        
        self.code_tab.pack(fill='both', expand=True)
        
        # Placeholder for Properties tab
        props_header = ttk.Frame(self.palette_frame, style="DarkHeader.TFrame")
        props_header.pack(fill='x', pady=(0,1))
        ttk.Label(props_header, text="Properties", style="DarkLabel.TLabel").pack(side='left', padx=5)
        ttk.Button(props_header, text="[-]", width=2, command=lambda: self.props_tab.pack_forget() if self.props_tab.winfo_ismapped() else self.props_tab.pack(fill='both', expand=True)).pack(side='right', padx=2)
        
        self.props_tab.pack(fill='both', expand=True)
        
        # Placeholder for Library tab
        grab_header = ttk.Frame(self.palette_frame, style="DarkHeader.TFrame")
        grab_header.pack(fill='x', pady=(0,1))
        ttk.Label(grab_header, text="Library", style="DarkLabel.TLabel").pack(side='left', padx=5)
        ttk.Button(grab_header, text="[-]", width=2, command=lambda: self.grab_tab.pack_forget() if self.grab_tab.winfo_ismapped() else self.grab_tab.pack(fill='both', expand=True)).pack(side='right', padx=2)
        
        self.grab_tab.pack(fill='both', expand=True)
        # --- End of Placeholder ---

        # RIGHT SIDE (80%): Visual Layout
        matrix_log("ui", "gui_builder", "_build_ui", "WysiwygEditor: Initializing Interactive Layout Canvas...", "DEBUG")
        self.layout_container = tk.Frame(self.main_pane, bg="#1a1a1a")
        self.main_pane.add(self.layout_container)
        
        self.layout_view = InteractiveLayout(self.layout_container)
        self.layout_view.pack(fill="both", expand=True)
        
        matrix_log("ui", "gui_builder", "_build_ui", "WysiwygEditor: UI Build Complete.", "INFO")

    def close_window(self):
        """Explicitly cleans up and destroys the UI window."""
        matrix_log("ui", "gui_builder", "close_window", "WysiwygEditor: Shutdown Sequence Initiated.", "INFO")
        event_bus.unsubscribe("FOCUS_REQUESTED", self._on_focus_requested)
        
        # Reset State Manager to avoid cross-pollination on relaunch
        matrix_log("ui", "gui_builder", "close_window", "WysiwygEditor: Resetting StateManager...", "DEBUG")
        state_manager.reset()

        # Destroy window
        try:
            matrix_log("ui", "gui_builder", "close_window", "WysiwygEditor: Destroying Window...", "DEBUG")
            self.window.destroy()
        except:
            pass
            
        # Reset instance
        WysiwygEditor._instance = None
        matrix_log("ui", "gui_builder", "close_window", "WysiwygEditor: Editor Closed.", "INFO")

    def _on_focus_requested(self, path, source=None):
        """Optionally switches tabs when an element is focused."""
        if not hasattr(self, 'status_lbl') or not self.status_lbl.winfo_exists():
            return
            
        self.status_lbl.config(text=f"Focused: {path}")
        # Switch to Props tab (index 2) if focus comes from layout
        if source == self.layout_view:
            matrix_log("ui", "gui_builder", "_on_focus_requested", f"WysiwygEditor: Focus Event - Switching to Props tab for element at path: {path}", "DEBUG")
            self.left_notebook.select(2)

    def save_workspace(self):
        """Triggers the File IO handler to serialize the workspace to disk."""
        matrix_log("ui", "gui_builder", "save_workspace", f"WysiwygEditor: Manual Save Triggered for file: {state_manager.get_file_path()}", "INFO")
        
        # Attempt Save
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
        matrix_log("ui", "gui_builder", "_save_and_close", "WysiwygEditor: 'SAVE AND CLOSE' triggered.", "INFO")
        if self.save_workspace():
            self.close_window()

    def abandon_changes(self):
        """Discards all changes, restores original state in the main UI, and closes."""
        matrix_log("ui", "gui_builder", "abandon_changes", "WysiwygEditor: 'ABANDON CHANGES' triggered.", "INFO")
        
        # 1. Restore original state in main UI if possible
        if self.on_test:
            orig = state_manager.get_original_state()
            if orig:
                matrix_log("ui", "gui_builder", "abandon_changes", "WysiwygEditor: Restoring original state in main application...", "DEBUG")
                self.on_test(orig)
        
        # 2. Close window
        self.close_window()

    def _test_config(self):
        """Triggers the test callback with current master state_manager."""
        matrix_log("ui", "gui_builder", "_test_config", "WysiwygEditor: Rebuilding main UI with current editor state_manager...", "INFO")
        if self.on_test:
            self.on_test(state_manager.get_state())
            if self.status_lbl.winfo_exists():
                self.status_lbl.config(text="Main UI Rebuilt", foreground="#FF9900")
