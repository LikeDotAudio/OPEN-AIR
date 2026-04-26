# Interface/Window/editor_layout.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Interface.1
#
# Description: Modularized layout builder for the WYSIWYG editor.

import tkinter as tk
from tkinter import ttk

from oaLogging.Methods.matrix_gate import matrix_log

from ..Tabs.ElementProperties.Entry import ElementProperties
from ..Tabs.GrabBagView.grab_bag_view import GrabBagView
from ..Tabs.InteractiveLayout.interactive_layout import InteractiveLayout
from ..Tabs.JsonEditor.json_editor import JsonCodeWorkspace, JsonTreeWorkspace
from .editor_toolbar import EditorToolbar


class EditorLayoutBuilder:
    """Orchestrates the assembly of the WYSIWYG Editor UI."""

    @staticmethod
    def assemble(editor):
        """Assembles the main interface layout from modular components."""
        matrix_log("ui", "gui_builder", "layout", "🎨🎨🎨 [RENDER] Assemble Editor Layout", "DEBUG")

        # 1. Status Bar
        editor.status_bar = EditorStatusBar(editor.window)

        # 1.5 Global Toolbar
        editor.toolbar = EditorToolbar(editor.window, editor)
        editor.toolbar.pack(side="top", fill="x")

        # 2. Main Container (PanedWindow)
        editor.main_pane = tk.PanedWindow(editor.window, orient=tk.HORIZONTAL, bg="#2b2b2b", sashwidth=6, bd=0)
        editor.main_pane.pack(fill="both", expand=True, padx=5, pady=5)

        # 3. Assemble Regions
        SidebarBuilder.build_left(editor)
        CanvasBuilder.build_center(editor)
        SidebarBuilder.build_right(editor)

        # 4. Finalize
        SashManager.setup(editor)

class SidebarBuilder:
    """Responsible for building left and right sidebars."""

    @staticmethod
    def build_left(editor):
        """Builds the left navigation sidebar with Structure, Code, and Library tabs."""
        editor.left_sidebar = tk.Frame(editor.main_pane, bg="#252526")
        editor.main_pane.add(editor.left_sidebar, width=250, stretch="never")

        editor.left_notebook = ttk.Notebook(editor.left_sidebar)
        editor.left_notebook.pack(fill="both", expand=True)

        # Initialize library cache
        from ...FileReaders.grab_bag_loader import GrabBagLoader
        editor.global_library = GrabBagLoader().scan_library()

        # Combined Structure/JSON Navigation
        editor.json_tab = JsonTreeWorkspace(editor.left_notebook)
        editor.left_notebook.add(editor.json_tab, text=" Structure ")

        editor.code_tab = JsonCodeWorkspace(editor.left_notebook)
        editor.left_notebook.add(editor.code_tab, text=" Code ")

        editor.grab_tab = GrabBagView(editor.left_notebook, library_cache=editor.global_library)
        editor.left_notebook.add(editor.grab_tab, text=" Library ")

        # ⚡ BINDING: Auto-switch render tier based on active tab
        def _on_tab_changed(event):
            tab_id = editor.left_notebook.index("current")
            tier_map = {
                0: "Fast",      # Structure
                1: "High-Res",  # Code
                2: "Ghost"      # Library
            }
            target_tier = tier_map.get(tab_id)
            if target_tier and hasattr(editor, 'layout_view'):
                matrix_log("ui", "gui_builder", "layout", f"🎯 [ACTION] Tab Switch: Updating render tier to {target_tier}", "DEBUG")
                editor.layout_view.render_tier_var.set(target_tier)
                editor.layout_view._on_render_tier_change()

        editor.left_notebook.bind("<<NotebookTabChanged>>", _on_tab_changed)

    @staticmethod
    def build_right(editor):
        """Builds the right sidebar containing the property editor."""
        editor.right_sidebar = tk.Frame(editor.main_pane, bg="#2d2d2d")
        editor.main_pane.add(editor.right_sidebar, width=300, minsize=300, stretch="never")

        editor.props_tab = ElementProperties(editor.right_sidebar, library_cache=editor.global_library)
        editor.props_tab.pack(fill="both", expand=True)

class CanvasBuilder:
    """Responsible for building the center interactive design canvas."""

    @staticmethod
    def build_center(editor):
        """Builds the center canvas where the layout is visually edited."""
        editor.layout_container = tk.Frame(editor.main_pane, bg="#1a1a1a")
        editor.main_pane.add(editor.layout_container, stretch="always")

        editor.layout_view = InteractiveLayout(editor.layout_container)
        editor.layout_view.pack(fill="both", expand=True)

class SashManager:
    """Handles the positioning of PanedWindow sashes."""

    @staticmethod
    def setup(editor):
        """Sets up the initial sash positions after the window is mapped."""
        def _on_map(e):
            # ⚡ [UI] Unbind after first map to prevent "snapping back" on minimize/restore
            if hasattr(editor, 'window') and editor.window.winfo_exists():
                editor.window.unbind("<Map>", map_id)
            editor.window.after(100, lambda: SashManager.set_initial(editor))

        map_id = editor.window.bind("<Map>", _on_map, add="+")

    @staticmethod
    def set_initial(editor):
        """Calculates and applies the initial sash positions using percentage-based logic."""
        try:
            editor.main_pane.update_idletasks()
            width = editor.main_pane.winfo_width()
            if width <= 1:
                editor.window.after(200, lambda: SashManager.set_initial(editor))
                return

            matrix_log("ui", "gui_builder", "layout", f"📐📐📐 [RENDER] Setting initial sashes for width: {width}", "DEBUG")

            # 1. Left Sidebar: 30% of width
            left_pos = int(width * 0.30)

            # 2. Right Sidebar: 30% of width (measured from the right)
            right_pos = int(width * (1.0 - 0.30))

            editor.main_pane.sash_place(0, left_pos, 0)
            editor.main_pane.sash_place(1, right_pos, 0)
        except Exception as e:
            matrix_log("ui", "gui_builder", "layout", f"⚠️🎨🤦‍♂️ [RENDER] Sash placement failed: {e}", "TRACE")

class EditorStatusBar:
    """Encapsulates the status bar UI and feedback logic."""
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg="#007acc", height=22)
        self.frame.pack(side="bottom", fill="x")

        self.status_lbl = tk.Label(self.frame, text="Modular Editor Active",
                                   bg="#007acc", fg="white", font=("Arial", 8, "bold"))
        self.status_lbl.pack(side="left", padx=10)

        self.pending_lbl = tk.Label(self.frame, text="Changes: 0",
                                    bg="#007acc", fg="white", font=("Arial", 8))
        self.pending_lbl.pack(side="right", padx=10)

    def set_status(self, text, color="white"):
        """Updates the status text and color."""
        self.status_lbl.config(text=text, fg=color)

    def set_changes(self, count):
        """Updates the pending changes count and its highlighting."""
        self.pending_lbl.config(text=f"Changes: {count}")
        self.pending_lbl.config(fg="white" if count == 0 else "#FF9900")
