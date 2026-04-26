# Interface/Tabs/TreeRefactor/Core/tree_styler.py
# Author: Gemini CLI
# Version: 20260417.001.0
#
# Description: Configures the dark mode styles for the Treeview and containers.

from tkinter import ttk


def apply_tree_styles():
    """Configures the dark mode styles for the Treeview and containers."""
    style = ttk.Style()

    # Dark Frame
    style.configure("Dark.TFrame", background="#2b2b2b")

    # Dark Treeview
    style.configure("Treeview",
        background="#1a1a1a",
        foreground="#dcdcdc",
        fieldbackground="#1a1a1a",
        borderwidth=0,
        font=("Segoe UI", 9)
    )
    style.map("Treeview",
        background=[('selected', '#33A1FD')],
        foreground=[('selected', 'white')]
    )

    # Dark Treeview Heading
    style.configure("Treeview.Heading",
        background="#333333",
        foreground="#888888",
        relief="flat",
        font=("Segoe UI", 9, "bold")
    )
    style.map("Treeview.Heading",
        background=[('active', '#444444')]
    )
