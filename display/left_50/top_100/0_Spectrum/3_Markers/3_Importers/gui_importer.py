# display/left_50/top_100/3_markers/3_importers/gui_importer.py
#
# This file provides a basic GUI component with buttons for importing marker data.
# It now serves as the presentation layer, with all file handling logic moved
# to a dedicated worker file.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
#
# Version 20251127.000000.1

import tkinter as tk
from tkinter import filedialog, ttk
import os
import inspect
import pathlib

# --- Graceful Dependency Importing ---
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

# --- Module Imports ---
from workers.logger.logger import  debug_logger
from workers.importers.worker_marker_file_import_handling import (
    maker_file_check_for_markers_file
)
from workers.styling.style import THEMES, DEFAULT_THEME
from workers.importers.worker_importer_loader import *
from workers.importers.worker_importer_appender import *
from workers.importers.worker_importer_editor import *
from workers.importers.worker_importer_saver import *
from managers.configini.config_reader import Config
app_constants = Config.get_instance() # Get the singleton instance
from workers.logger.log_utils import _get_log_args

# --- Global Scope Variables ---
current_version = "20251226.000000.1"
current_version_hash = (20251127 * 0 * 1)
current_file_path = pathlib.Path(__file__).resolve()
project_root = current_file_path.parents[5]
current_file = str(current_file_path.relative_to(project_root)).replace("\\", "/")


# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2

class MarkerImporterTab(ttk.Frame):
    """
    A stripped-down Tkinter Frame focused on displaying marker data and triggering
    actions via a separate worker module.
    """
    def __init__(self, master=None, app_instance=None, **kwargs):
        current_function = inspect.currentframe().f_code.co_name
        if 'config' in kwargs:
            kwargs.pop('config')
        super().__init__(master, **kwargs)

        self.app_instance = app_instance
        self.tree_headers = []
        self.tree_data = []
        self.sort_column = None
        self.sort_direction = False
        self.current_file = current_file
        self.current_version = current_version

        debug_logger(
            message="🟢️️️🟢 Initializing MarkerImporterTab. The GUI is now lean and mean! 🎉",
          **_get_log_args()
            
        )

        self._apply_styles(theme_name=DEFAULT_THEME)
        self._create_widgets()

        if not PANDAS_AVAILABLE:
            debug_logger(
                message="❌ Critical dependency 'pandas' or 'numpy' not found. Marker Importer will have limited functionality.",
**_get_log_args()
                
            )
            # Optionally, disable the whole tab or show an error message
            error_label = ttk.Label(self, text="🔴 ERROR: NumPy and Pandas libraries are required for this tab.", foreground="red")
            error_label.pack(pady=20)
            return

        # Call the worker to check for an existing file on startup
        self.tree_headers, self.tree_data = maker_file_check_for_markers_file()
        self._update_treeview()

        debug_logger(
            message="🟢️️️🟢 MarkerImporterTab has been fully instantiated. Now creating widgets!",
          **_get_log_args()
            
        )

    def _apply_styles(self, theme_name: str):
        colors = THEMES.get(theme_name, THEMES["dark"])
        style = ttk.Style(self)
        style.theme_use("clam")

        # General widget styling
        style.configure('TFrame', background=colors["bg"])
        style.configure('TLabel', background=colors["bg"], foreground=colors["fg"])
        style.configure('TLabelframe', background=colors["bg"], foreground=colors["fg"])

        # Table (Treeview) styling
        style.configure('Treeview',
                        background=colors["table_bg"],
                        foreground=colors["table_fg"],
                        fieldbackground=colors["table_bg"],
                        bordercolor=colors["table_border"],
                        borderwidth=colors["border_width"])

        style.configure('Treeview.Heading',
                        background=colors["table_heading_bg"],
                        foreground=colors["fg"],
                        relief=colors["relief"],
                        borderwidth=colors["border_width"])

        style.configure('Markers.TEntry',
                        fieldbackground=colors["entry_bg"],
                        foreground=colors["entry_fg"],
                        insertbackground=colors["fg"],
                        selectbackground=colors["hover_blue"],
                        selectforeground=colors["text"])
        
        style.configure('TButton',
                        background=colors["secondary"],
                        foreground=colors["text"],
                        padding=10, relief=colors["relief"],
                        borderwidth=colors["border_width"])
        style.map('TButton',
                  background=[('pressed', colors["accent"]), 
                              ('active', colors["hover_blue"])])
        
        style.configure('Green.TButton', background='#6a9955', foreground='#ffffff')
        style.map('Green.TButton',
                  background=[('pressed', '!disabled', '#4a6f3b'),
                              ('active', '#8ab97c')],
                  foreground=[('pressed', '!disabled', '#ffffff'),
                              ('active', '#ffffff')])
        
        style.configure('Blue.TButton', 
                        background=colors["button_style_toggle"]["background"], 
                        foreground=colors["button_style_toggle"]["foreground"])
        style.map('Blue.TButton',
                  background=[('pressed', '!disabled', colors["button_style_toggle"]["Button_Pressed_Bg"]),
                              ('active', colors["button_style_toggle"]["Button_Hover_Bg"])],
                  foreground=[('pressed', '!disabled', colors["button_style_toggle"]["foreground"]),
                              ('active', colors["button_style_toggle"]["foreground"])])

        style.configure('Orange.TButton', 
                        background=colors["button_style_toggle"]["background"], 
                        foreground=colors["button_style_toggle"]["foreground"])
        style.map('Orange.TButton',
                  background=[('pressed', '!disabled', colors["button_style_toggle"]["Button_Pressed_Bg"]),
                              ('active', colors["button_style_toggle"]["Button_Hover_Bg"])],
                  foreground=[('pressed', '!disabled', colors["button_style_toggle"]["foreground"]),
                              ('active', colors["button_style_toggle"]["foreground"])])
        
        style.configure('Red.TButton', 
                        background=colors["button_style_toggle"]["background"], 
                        foreground=colors["button_style_toggle"]["foreground"])
        style.map('Red.TButton',
                  background=[('pressed', '!disabled', colors["button_style_toggle"]["Button_Pressed_Bg"]),
                              ('active', colors["button_style_toggle"]["Button_Hover_Bg"])],
                  foreground=[('pressed', '!disabled', colors["button_style_toggle"]["foreground"]),
                              ('active', colors["button_style_toggle"]["foreground"])])

    def _create_widgets(self):
        self.pack(fill=tk.BOTH, expand=True)
        
        load_markers_frame = ttk.LabelFrame(self, text="Load Markers", padding=(5,5,5,5))
        load_markers_frame.pack(fill=tk.X, padx=DEFAULT_PAD_X, pady=DEFAULT_PAD_Y)
        
        self.load_csv_button = ttk.Button(load_markers_frame, text="Load CSV Marker Set", style='Action.TButton', command=lambda: load_markers_file_action(self))
        self.load_csv_button.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        
        self.load_ias_html_button = ttk.Button(load_markers_frame, text="Load IAS HTML", style='Action.TButton', command=lambda: load_ias_html_action(self))
        self.load_ias_html_button.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        
        self.load_wwb_shw_button = ttk.Button(load_markers_frame, text="Load WWB.shw", style='Action.TButton', command=lambda: load_wwb_shw_action(self))
        self.load_wwb_shw_button.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)

        self.load_wwb_zip_button = ttk.Button(load_markers_frame, text="Load WWB.zip", style='Action.TButton', command=lambda: load_wwb_zip_action(self))
        self.load_wwb_zip_button.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)

        self.load_sb_pdf_button = ttk.Button(load_markers_frame, text="Load SB PDF", style='Action.TButton', command=lambda: load_sb_pdf_action(self))
        self.load_sb_pdf_button.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        
        self.load_sb_v2_pdf_button = ttk.Button(load_markers_frame, text="Load SB V2.pdf", style='Action.TButton', command=lambda: load_sb_v2_pdf_action(self))
        self.load_sb_v2_pdf_button.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)

        marker_table_frame = ttk.LabelFrame(self, text="Marker Editor", padding=(5,5,5,5))
        marker_table_frame.pack(fill=tk.BOTH, expand=True, padx=DEFAULT_PAD_X, pady=DEFAULT_PAD_Y)
        
        self.marker_tree = ttk.Treeview(marker_table_frame, show=("headings", "tree"))
        self.marker_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=DEFAULT_PAD_X, pady=DEFAULT_PAD_Y)
        self.marker_tree.column("#0", width=0, stretch=tk.NO)
        
        tree_yscroll = ttk.Scrollbar(marker_table_frame, orient="vertical", command=self.marker_tree.yview)
        tree_yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.marker_tree.configure(yscrollcommand=tree_yscroll.set)
        
        tree_xscroll = ttk.Scrollbar(marker_table_frame, orient="horizontal", command=self.marker_tree.xview)
        tree_xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.marker_tree.configure(xscrollcommand=tree_xscroll.set)

        self.marker_tree.bind("<Double-1>", lambda event: on_tree_double_click(self, event))
        self.marker_tree.bind("<Button-1>", lambda event: on_tree_header_click(self, event), add="+ ")
        self.marker_tree.bind("<Delete>", lambda event: delete_selected_row(self, event))

        append_markers_frame = ttk.LabelFrame(self, text="Append Markers", padding=(5,5,5,5))
        append_markers_frame.pack(fill=tk.X, padx=DEFAULT_PAD_X, pady=DEFAULT_PAD_Y)
        
        self.append_csv_button = ttk.Button(append_markers_frame, text="Append CSV Marker Set", style='Action.TButton', command=lambda: append_markers_file_action(self))
        self.append_csv_button.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        
        self.append_ias_html_button = ttk.Button(append_markers_frame, text="Append IAS HTML", style='Action.TButton', command=lambda: append_ias_html_action(self))
        self.append_ias_html_button.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        
        self.append_wwb_shw_button = ttk.Button(append_markers_frame, text="Append WWB.shw", style='Action.TButton', command=lambda: append_wwb_shw_action(self))
        self.append_wwb_shw_button.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)

        self.append_wwb_zip_button = ttk.Button(append_markers_frame, text="Append WWB.zip", style='Action.TButton', command=lambda: append_wwb_zip_action(self))
        self.append_wwb_zip_button.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)

        self.append_sb_pdf_button = ttk.Button(append_markers_frame, text="Append SB PDF", style='Action.TButton', command=lambda: append_sb_pdf_action(self))
        self.append_sb_pdf_button.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        
        self.append_sb_v2_pdf_button = ttk.Button(append_markers_frame, text="Append SB V2.pdf", style='Action.TButton', command=lambda: append_sb_v2_pdf_action(self))
        self.append_sb_v2_pdf_button.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)

        self.save_open_air_button = ttk.Button(self, text="Save Markers as Open Air.csv", style='Orange.TButton', command=lambda: save_open_air_file_action(self))
        self.save_open_air_button.pack(fill=tk.X, padx=DEFAULT_PAD_X, pady=DEFAULT_PAD_Y)

    def _update_treeview(self):
        self.marker_tree.delete(*self.marker_tree.get_children())
        standardized_headers = self.tree_headers if self.tree_headers else ["ZONE", "GROUP", "DEVICE", "NAME", "FREQ_MHZ", "PEAK"]
        self.marker_tree["columns"] = standardized_headers
        debug_logger(
            message=f"🔁🔵 Now adding {len(self.tree_data)} rows to the Treeview. Headers: {standardized_headers}",
           **_get_log_args()
            
        )
        for col in standardized_headers:
            self.marker_tree.heading(col, text=col, command=lambda c=col: on_tree_header_click(self, None))
            self.marker_tree.column(col, width=100)

        for row in self.tree_data:
            if isinstance(row, list):
                # Convert list to dictionary using headers
                row_dict = dict(zip(standardized_headers, row))
                values = [row_dict.get(raw_header, '') for raw_header in standardized_headers]
            elif isinstance(row, dict):
                values = [row.get(raw_header, '') for raw_header in standardized_headers]
            else:
                values = ["🔴 ERROR: Invalid row format"] * len(standardized_headers)
            self.marker_tree.insert("", "end", values=values)