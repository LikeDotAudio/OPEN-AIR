# Interface/Window/editor_menus.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Interface.1
#
# Description: Modularized menu builder for the WYSIWYG editor.

import tkinter as tk

class EditorMenuBuilder:
    """Orchestrates the construction of the Editor's menu system."""

    @staticmethod
    def build(editor):
        """Builds the main menubar and attaches it to the editor window."""
        editor.menubar = tk.Menu(editor.window)
        editor.window.config(menu=editor.menubar)

        # Bind shortcuts
        editor.window.bind("<Control-n>", lambda e: editor.new_workspace())
        editor.window.bind("<Control-o>", lambda e: editor.open_workspace())
        editor.window.bind("<Control-s>", lambda e: editor.save_workspace())

        EditorMenuBuilder._build_file_menu(editor)
        EditorMenuBuilder._build_test_menu(editor)
        EditorMenuBuilder._build_language_menu(editor)
        EditorMenuBuilder._inject_layout_menus(editor)

    @staticmethod
    def _build_file_menu(editor):
        """Builds the FILE menu with new, open, save, and exit actions."""
        file_menu = tk.Menu(editor.menubar, tearoff=0)
        file_menu.add_command(label="New", command=editor.new_workspace, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=editor.open_workspace, accelerator="Ctrl+O")
        file_menu.add_command(label="Save & Backup", command=editor.save_workspace, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Abandon Changes", command=editor.abandon_changes)
        file_menu.add_command(label="Save & Close", command=editor._save_and_close)
        editor.menubar.add_cascade(label="FILE", menu=file_menu)

    @staticmethod
    def _build_test_menu(editor):
        """Builds the TEST menu for live UI testing."""
        test_menu = tk.Menu(editor.menubar, tearoff=0)
        test_menu.add_command(label="Test UI", command=editor._test_config, accelerator="F5")
        editor.menubar.add_cascade(label="TEST", menu=test_menu)

    @staticmethod
    def _build_language_menu(editor):
        """Builds the LANGUAGE menu for switching UI translation."""
        lang_menu = tk.Menu(editor.menubar, tearoff=0)
        languages = [("English", "En"), ("French", "Fr"), ("Spanish", "Es"), ("German", "De")]
        for label, code in languages:
            lang_menu.add_command(label=label, command=lambda c=code: editor.change_language(c))
        editor.menubar.add_cascade(label="LANGUAGE", menu=lang_menu)

    @staticmethod
    def _inject_layout_menus(editor):
        """Injects dynamic menus from the layout view if available."""
        if hasattr(editor, 'layout_view'):
            editor.layout_view.fill_menus(editor.menubar)

