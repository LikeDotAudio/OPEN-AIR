# 3_Importers/gui_importer.py
#
# This module provides the MarkerImporterTab, a GUI component with buttons for importing and appending marker data from various file formats.
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
# Version 20250821.200641.1

import tkinter as tk
from tkinter import filedialog, ttk
import inspect
import pathlib
from workers.setup.worker_project_paths import GLOBAL_PROJECT_ROOT # Import GLOBAL_PROJECT_ROOT

# --- Graceful Dependency Importing ---
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

# --- Module Imports ---
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args
from workers.styling.style import THEMES, DEFAULT_THEME
from managers.configini.config_reader import Config
from workers.builder.builder_table.dynamic_gui_table import GuiTableCreatorMixin

# --- WORKER IMPORTS (EXPLICIT) ---
# Connecting the jumper cables directly to the engine!
try:
    from workers.importers.worker_importer_loader import (
        maker_file_check_for_markers_file,
        load_markers_file_action,
        load_ias_html_action,
        load_wwb_shw_action,
        load_wwb_zip_action,
        load_sb_pdf_action,
        load_sb_v2_pdf_action,
    )
    from workers.importers.worker_importer_appender import (
        append_markers_file_action,
        append_ias_html_action,
        append_wwb_shw_action,
        append_wwb_zip_action,
        append_sb_pdf_action,
        append_sb_v2_pdf_action,
    )
    from workers.importers.worker_importer_saver import save_open_air_file_action

    WORKERS_CONNECTED = True
except ImportError as e:
    # ⚠️ Warning: If workers are missing, we deploy the dummy plugs.
    print(f"❌ CRITICAL FAILURE: Could not link to Worker Modules! {e}")
    WORKERS_CONNECTED = False

    # Dummy sinks to prevent crashes
    def dummy_action(*args):
        print("⚠️ Worker not connected!")

    load_markers_file_action = dummy_action
    load_ias_html_action = dummy_action
    load_wwb_shw_action = dummy_action
    load_wwb_zip_action = dummy_action
    load_sb_pdf_action = dummy_action
    load_sb_v2_pdf_action = dummy_action
    append_markers_file_action = dummy_action
    append_ias_html_action = dummy_action
    append_wwb_shw_action = dummy_action
    append_wwb_zip_action = dummy_action
    append_sb_pdf_action = dummy_action
    append_sb_v2_pdf_action = dummy_action
    save_open_air_file_action = dummy_action
    maker_file_check_for_markers_file = lambda: ([], [])


app_constants = Config.get_instance()  # Get the singleton instance

# --- Global Scope Variables ---
current_version = "20260104.200500.3"
current_version_hash = 20260104 * 200500 * 3
current_file_path = pathlib.Path(__file__).resolve()
# Use GLOBAL_PROJECT_ROOT for consistency
current_file = str(current_file_path.relative_to(GLOBAL_PROJECT_ROOT)).replace("\", "/")


# --- Constants ---
DEFAULT_PAD_X = 5
DEFAULT_PAD_Y = 2


class MarkerImporterTab(ttk.Frame, GuiTableCreatorMixin):
    """
    A stripped-down Tkinter Frame focused on displaying marker data and triggering
    actions via a separate worker module.
    """

    # Initializes the MarkerImporterTab.
    # This constructor sets up the internal state for marker data, headers, and sorting.
    # It also initializes helper classes for CSV export/import, applies styling,
    # and creates the GUI widgets for loading, appending, and saving marker data.
    # Inputs:
    #     master: The parent Tkinter widget.
    #     app_instance: A reference to the main application instance.
    #     config_data (dict, optional): Configuration data for the tab.
    #     *args: Positional arguments for the Frame.
    #     **kwargs: Keyword arguments for the Frame.
    # Outputs:
    #     None.
    def __init__(
        self, master=None, app_instance=None, config_data=None, *args, **kwargs
    ):
        current_function = inspect.currentframe().f_code.co_name

        # Clean up kwargs just in case
        if "config" in kwargs:
            kwargs.pop("config")

        super().__init__(master, **kwargs)

        self.app_instance = app_instance
        self.config_data = config_data  # Store the config if we need it later

        self.tree_headers = []
        self.tree_data = []
        self.sort_column = None
        self.sort_direction = False
        self.current_file = current_file
        self.current_version = current_version
        self.LOCAL_DEBUG_ENABLE = True

        # 🧪 Safe Logging: We pass explicit arguments to avoid collisions
        debug_logger(
            message=f"🧪 Great Scott! Initializing '{current_function}'! The Importer Tab is online.",
            **_get_log_args(),
        )

        self._apply_styles(theme_name=DEFAULT_THEME)

        # Arguments for _create_gui_table
        self.table_label = "Marker Editor"  # A descriptive label
        self.table_path = "markers_importer"  # Unique path for this table instance
        self.base_mqtt_topic_from_path =
            self.app_instance.state_mirror_engine.base_topic
        self.state_mirror_engine = self.app_instance.state_mirror_engine
        self.subscriber_router = self.app_instance.subscriber_router

        self._create_widgets()

        if not WORKERS_CONNECTED:
            debug_logger(
                message="❌ ERROR! The bridge is out! Worker modules could not be imported. Buttons disabled.",
                **_get_log_args(),
            )
            return

        if not PANDAS_AVAILABLE:
            debug_logger(
                message="⚠️ Warning: Pandas not found. The Flux Capacitor is running at 50% efficiency.",
                **_get_log_args(),
            )

        # Call the worker to check for an existing file on startup
        try:
            self.tree_headers, self.tree_data = maker_file_check_for_markers_file()
            self._update_treeview()
        except Exception as e:
            debug_logger(
                message=f"💥 A paradox! Failed to load initial marker file: {e}",
                **_get_log_args(),
            )

        debug_logger(
            message="✅ It works! MarkerImporterTab instantiated successfully!",
            **_get_log_args(),
        )

    # Applies theme-specific styles to the widgets within the MarkerImporterTab.
    # This method configures the appearance of various ttk widgets, ensuring
    # consistent styling across the application.
    # Inputs:
    #     theme_name (str): The name of the theme to apply (e.g., "dark").
    # Outputs:
    #     None.
    def _apply_styles(self, theme_name: str):
        colors = THEMES.get(theme_name, THEMES["dark"])
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame", background=colors["bg"])
        style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
        style.configure("TLabelframe", background=colors["bg"], foreground=colors["fg"])

        # Ensure Action.TButton is defined for the buttons below
        style.configure(
            "Action.TButton", background=colors["secondary"], foreground=colors["text"]
        )
        style.map("Action.TButton", background=[("active", colors["hover_blue"])]
        )

        style.configure(
            "Treeview",
            background=colors["table_bg"],
            foreground=colors["table_fg"],
            fieldbackground=colors["table_bg"],
            bordercolor=colors["table_border"],
            borderwidth=colors["border_width"],
        )
        style.configure(
            "Treeview.Heading",
            background=colors["table_heading_bg"],
            foreground=colors["fg"],
        )
        style.configure(
            "Orange.TButton",
            background=colors.get("button_style_toggle", {}).get(
                "background", "orange"
            ),
            foreground="black",
        )

    # Creates and arranges all the GUI widgets for the MarkerImporterTab.
    # This method sets up sections for loading, appending, and saving marker data,
    # including buttons for various file formats and the central Treeview table
    # for displaying and editing markers.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def _create_widgets(self):
        self.pack(fill=tk.BOTH, expand=True)

        # --- LOAD FRAME ---
        load_markers_frame = ttk.LabelFrame(
            self, text="Load Markers (Temporal Injection)", padding=(5, 5, 5, 5)
        )
        load_markers_frame.pack(fill=tk.X, padx=DEFAULT_PAD_X, pady=DEFAULT_PAD_Y)

        # Helper to create buttons cleanly
        def create_btn(parent, text, cmd):
            btn = ttk.Button(parent, text=text, style="Action.TButton", command=cmd)
            btn.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
            return btn

        create_btn(
            load_markers_frame, "Load CSV", lambda: load_markers_file_action(self)
        )
        create_btn(
            load_markers_frame, "Load IAS HTML", lambda: load_ias_html_action(self)
        )
        create_btn(
            load_markers_frame, "Load WWB.shw", lambda: load_wwb_shw_action(self)
        )
        create_btn(
            load_markers_frame, "Load WWB.zip", lambda: load_wwb_zip_action(self)
        )
        create_btn(load_markers_frame, "Load SB PDF", lambda: load_sb_pdf_action(self))
        create_btn(
            load_markers_frame, "Load SB V2.pdf", lambda: load_sb_v2_pdf_action(self)
        )

        # --- TABLE FRAME ---
        # Use _create_gui_table from GuiTableCreatorMixin
        self.marker_table_container = self._create_gui_table(
            parent_frame=self,  # MarkerImporterTab is the parent frame
            label=self.table_label,
            config=self.config_data,
            path=self.table_path,
            base_mqtt_topic_from_path=self.base_mqtt_topic_from_path,
            state_mirror_engine=self.state_mirror_engine,
            subscriber_router=self.subscriber_router,
        )
        self.marker_table_container.pack(
            fill=tk.BOTH, expand=True, padx=DEFAULT_PAD_X, pady=DEFAULT_PAD_Y
        )
        self.marker_tree = self.marker_table_container.tree  # Get the Treeview widget
        # The TableEditingManager is already attached to self.marker_tree as .editor

        # --- APPEND FRAME ---
        append_markers_frame = ttk.LabelFrame(
            self, text="Append Markers (Merge Timelines)", padding=(5, 5, 5, 5)
        )
        append_markers_frame.pack(fill=tk.X, padx=DEFAULT_PAD_X, pady=DEFAULT_PAD_Y)

        create_btn(
            append_markers_frame,
            "Append CSV",
            lambda: append_markers_file_action(self, self.marker_tree.editor),
        )
        create_btn(
            append_markers_frame,
            "Append IAS HTML",
            lambda: append_ias_html_action(self, self.marker_tree.editor),
        )
        create_btn(
            append_markers_frame,
            "Append WWB.shw",
            lambda: append_wwb_shw_action(self, self.marker_tree.editor),
        )
        create_btn(
            append_markers_frame,
            "Append WWB.zip",
            lambda: append_wwb_zip_action(self, self.marker_tree.editor),
        )
        create_btn(
            append_markers_frame,
            "Append SB PDF",
            lambda: append_sb_pdf_action(self, self.marker_tree.editor),
        )
        create_btn(
            append_markers_frame,
            "Append SB V2.pdf",
            lambda: append_sb_v2_pdf_action(self, self.marker_tree.editor),
        )

        # --- SAVE BUTTON ---
        self.save_open_air_button = ttk.Button(
            self,
            text="Save Markers as Open Air.csv",
            style="Orange.TButton",
            command=lambda: save_open_air_file_action(self),
        )
        self.save_open_air_button.pack(
            fill=tk.X, padx=DEFAULT_PAD_X, pady=DEFAULT_PAD_Y
        )

        if not WORKERS_CONNECTED:
            debug_logger(
                message="❌ ERROR! The bridge is out! Worker modules could not be imported. Buttons disabled.",
                **_get_log_args(),
            )
            return

        if not PANDAS_AVAILABLE:
            debug_logger(
                message="⚠️ Warning: Pandas not found. The Flux Capacitor is running at 50% efficiency.",
                **_get_log_args(),
            )

        # Call the worker to check for an existing file on startup
        try:
            self.tree_headers, self.tree_data = maker_file_check_for_markers_file()
            # Initial load should go through the table editor as well
            if self.tree_data:
                self.marker_tree.editor.import_data(self.tree_data)
        except Exception as e:
            debug_logger(
                message=f"💥 A paradox! Failed to load initial marker file: {e}",
                **_get_log_args(),
            )

        debug_logger(
            message="✅ It works! MarkerImporterTab instantiated successfully!",
            **_get_log_args(),
        )