# Interface/Tabs/ElementProperties/Interface/properties_ui.py
# Author: Anthony Peter Kuzub
# Version: 20260417.001.0
#
# Description: Assembly of the properties panel UI components.

import tkinter as tk
from tkinter import ttk
from ..Core.auto_scrollbar import AutoScrollbar

class PropertiesUI:
    """Orchestrates the construction of the Element Properties user interface."""

    def __init__(self, parent, delete_command):
        self.parent = parent
        self.delete_command = delete_command
        self.path_lbl = None
        self.canvas = None
        self.scroll_frame = None
        self.canvas_win = None

    def build(self):
        """Assembles the header and the scrollable canvas area."""
        self._build_header()
        self._build_scrollable_area()
        return self

    def _build_header(self):
        header = tk.Frame(self.parent, bg="#333333", height=35)
        header.pack(side="top", fill="x")
        
        tk.Label(header, text="PROPERTIES", bg="#333333", fg="white", 
                 font=("Arial", 9, "bold")).pack(side="left", padx=10)
        
        tk.Button(header, text="DELETE WIDGET", bg="#cc0000", fg="white", 
                  font=("Arial", 7, "bold"), relief="flat", padx=5, 
                  command=self.delete_command).pack(side="right", padx=5)

        self.path_lbl = tk.Label(header, text="No Selection", bg="#333333", 
                                 fg="#33A1FD", font=("Arial", 8))
        self.path_lbl.pack(side="right", padx=10)

    def _build_scrollable_area(self):
        # Main Workspace Container
        ws_container = tk.Frame(self.parent, bg="#2b2b2b")
        ws_container.pack(fill="both", expand=True)
        ws_container.grid_rowconfigure(0, weight=1)
        ws_container.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(ws_container, bg="#2b2b2b", bd=0, highlightthickness=0)
        v_scrollbar = AutoScrollbar(ws_container, orient="vertical", command=self.canvas.yview)
        h_scrollbar = AutoScrollbar(ws_container, orient="horizontal", command=self.canvas.xview)
        
        self.scroll_frame = tk.Frame(self.canvas, bg="#2b2b2b")
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        self.canvas_win = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        self.scroll_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Initial placeholder message
        tk.Label(self.scroll_frame, text="Select a widget to edit properties.", 
                 bg="#2b2b2b", fg="#888888").pack(pady=50)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_win, width=max(event.width, self.scroll_frame.winfo_reqwidth()))

    def update_path_display(self, path):
        """Updates the path label in the header."""
        self.path_lbl.config(text=f"Path: {path}" if path else "No Selection")

    def clear_content(self):
        """Removes all widgets from the scroll frame."""
        for child in self.scroll_frame.winfo_children():
            child.destroy()
