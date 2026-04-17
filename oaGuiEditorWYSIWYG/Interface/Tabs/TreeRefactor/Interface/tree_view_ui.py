# Interface/Tabs/TreeRefactor/Interface/tree_view_ui.py
# Author: Gemini CLI
# Version: 20260417.001.0
#
# Description: Creates the Treeview and control buttons.

import tkinter as tk
from tkinter import ttk

class TreeViewUI:
    """Responsible for building the TreeRefactor user interface components."""

    @staticmethod
    def build(parent, on_up, on_down, on_delete):
        """Assembles the treeview, scrollbars, and control buttons."""
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # 1. Main Treeview Container
        tree_container = ttk.Frame(parent, style="Dark.TFrame")
        tree_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        tree = ttk.Treeview(tree_container, selectmode="browse", style="Treeview")
        tree.grid(row=0, column=0, sticky="nsew")
        
        # Define Columns
        tree["columns"] = ("path", "type")
        tree.column("#0", width=300, minwidth=200)
        tree.column("path", width=0, stretch=tk.NO)
        tree.column("type", width=0, stretch=tk.NO)
        tree.heading("#0", text="GUI Hierarchy", anchor="w")
        
        # Scrollbars
        tree_vsb = ttk.Scrollbar(tree_container, orient="vertical", command=tree.yview)
        tree_hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=tree_vsb.set, xscrollcommand=tree_hsb.set)
        
        tree_vsb.grid(row=0, column=1, sticky="ns")
        tree_hsb.grid(row=1, column=0, sticky="ew")

        # 2. Control Buttons
        btn_frame = ttk.Frame(parent, style="Dark.TFrame")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Button(btn_frame, text="▲ UP", command=on_up, width=8).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="▼ DOWN", command=on_down, width=8).pack(side="left", padx=2)
        
        delete_btn = tk.Button(btn_frame, text="DELETE", bg="#e74c3c", fg="white", 
                               font=("Arial", 8, "bold"), relief="flat", padx=10,
                               command=on_delete)
        delete_btn.pack(side="right", padx=5)

        # 3. Instruction Label
        tk.Label(parent, text="Tip: Drag & Drop to move items between containers", 
                  font=("Helvetica", 8, "italic"), bg="#2b2b2b", fg="#888888").grid(row=2, column=0, sticky="w", padx=10, pady=(0,5))

        return tree
