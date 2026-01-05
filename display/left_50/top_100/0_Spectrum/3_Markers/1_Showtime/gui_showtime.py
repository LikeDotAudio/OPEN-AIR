import os
import inspect
import datetime
import tkinter as tk
from tkinter import ttk
import pathlib
from tkinter import filedialog
from collections import defaultdict
from managers.configini.config_reader import Config
app_constants = Config.get_instance() # Get the singleton instance

# --- Global Scope Variables ---
current_file_path = pathlib.Path(__file__).resolve()
project_root = current_file_path.parents[5]
current_file = str(current_file_path.relative_to(project_root)).replace("\\", "/")
Current_Date = 20251226
Current_Time = 120000
Current_iteration = 44





# --- Graceful Dependency Importing ---
try:
    import pandas as pd
    import numpy as np
    PANDAS_NUMPY_AVAILABLE = True
except ImportError:
    pd = None
    np = None
    PANDAS_NUMPY_AVAILABLE = False

# --- Module Imports ---
from workers.logger.logger import  debug_logger
from workers.logger.log_utils import _get_log_args 
from workers.importers.worker_importer_loader import maker_file_check_for_markers_file
# FIXED: Importing tuning functions from the correct location.
# from workers.active.worker_active_marker_tune_and_collect import Push_Marker_to_Center_Freq, Push_Marker_to_Start_Stop_Freq
# NEW: Import the refactored logic function
from workers.markers.worker_marker_logic import calculate_frequency_range
from workers.styling.style import THEMES, DEFAULT_THEME
from workers.Showtime.worker_showtime_read import load_marker_data
from workers.Showtime.worker_showtime_group import process_and_sort_markers
from workers.Showtime.worker_showtime_tune import on_tune_request_from_selection
from workers.Showtime.worker_showtime_on_marker_button_click import on_marker_button_click
from workers.Showtime.worker_showtime_clear_group_buttons import clear_group_buttons
from workers.Showtime.worker_showtime_on_zone_toggle import on_zone_toggle
current_version = f"{Current_Date}.{Current_Time}.{Current_iteration}"

class ShowtimeTab(ttk.Frame):
    """
    A Tkinter Frame that dynamically creates buttons for each marker in the MARKERS.csv file.
    """
    def __init__(self, parent, *args, **kwargs):
        current_function = inspect.currentframe().f_code.co_name
        
        # Extract arguments intended for ShowtimeTab, not for Frame
        module_file_path_str = None
        config = None
        
        # Check if 'config' was passed as a keyword argument first
        if 'config' in kwargs:
            config = kwargs.pop('config')
        
        # If not in kwargs, check positional arguments in *args
        if not config and args:
            # Assume the first positional argument after parent is module_file_path_str
            module_file_path_str = args[0] if args else None
            if len(args) > 1:
                # Assume the second positional argument is config
                config = args[1]
        
        # Call the superclass constructor with the parent and any remaining keyword arguments
        # ttk.Frame expects master and then keyword arguments. We don't pass *args here.
        super().__init__(parent, **kwargs)
        
        self.module_file_path_str = module_file_path_str
        self.config = config
        
        # Store state_mirror_engine and subscriber_router extracted from config
        self.state_mirror_engine = config.get('state_mirror_engine') if config else None
        self.subscriber_router = config.get('subscriber_router') if config else None
        
        # State variables
        self.marker_data = []
        self.grouped_markers = defaultdict(lambda: defaultdict(list))
        self.column_headers = []
        
        # Selection state
        self.selected_zone = None
        self.selected_group = None
        self.selected_device_button = None # Track the currently selected button widget
        
        self._apply_styles(theme_name=DEFAULT_THEME)
        self._create_widgets()

        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🟢️️️🟢 Initialized ShowtimeTab.",
                **_get_log_args()
            )

    def _apply_styles(self, theme_name):
        colors = THEMES.get(theme_name, THEMES["dark"])
        style = ttk.Style(self)
        style.theme_use("clam")
        
        style.configure('TFrame', background=colors["bg"])
        style.configure('TLabelframe', background=colors["bg"], foreground=colors["fg"])
        style.configure('TLabelframe.Label', background=colors["bg"], foreground=colors["fg"])
        # Configure generic TButton, using unselected state for default
        
        # Get relevant colors from the currently applied theme
        dark_grey = colors.get("secondary", "#4e5254")
        selected_orange = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggle"]["Button_Selected_Bg"]
        selected_fg = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggle"]["Button_Selected_Fg"]
        hover_bg = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggle"]["Button_Hover_Bg"]
        hover_fg = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggle"]["Button_Hover_Fg"]

        style.configure('TButton', background=dark_grey, foreground=colors["text"])
        style.map('TButton',
                  background=[('active', hover_bg), ('!active', dark_grey)],
                  foreground=[('active', hover_fg), ('!active', colors["text"])])
        
        # Custom button styles for toggle states
        style.configure('Custom.TButton', background=dark_grey, foreground=colors["text"])
        style.map('Custom.TButton',
                  background=[('active', hover_bg), ('!active', dark_grey)],
                  foreground=[('active', hover_fg), ('!active', colors["text"])])

        # Configure Custom.TogglerUnselected.TButton (unselected state for toggler buttons)
        toggler_unselected_bg = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggler_unselected"]["background"]
        toggler_unselected_fg = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggler_unselected"]["foreground"]
        toggler_hover_bg = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggler_unselected"]["Button_Hover_Bg"]
        toggler_hover_fg = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggler_unselected"]["Button_Hover_Fg"]

        style.configure('Custom.TogglerUnselected.TButton', background=toggler_unselected_bg, foreground=toggler_unselected_fg)
        style.map('Custom.TogglerUnselected.TButton',
                  background=[('active', toggler_hover_bg), ('!active', toggler_unselected_bg)],
                  foreground=[('active', toggler_hover_fg), ('!active', toggler_unselected_fg)])

        style.configure('Custom.Selected.TButton', background=selected_orange, foreground=selected_fg, relief="sunken")
        style.map('Custom.Selected.TButton',
                  background=[('active', hover_bg), ('!active', selected_orange)],
                  foreground=[('active', hover_fg), ('!active', selected_fg)])

    def _create_widgets(self):
        current_function = inspect.currentframe().f_code.co_name
        
        # Main layout
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Zones section
        self.zones_frame = ttk.LabelFrame(main_frame, text="Zones")
        self.zones_frame.pack(fill=tk.X, padx=5, pady=2)
        # Create zone buttons will go here.

        # Groups section
        self.group_frame = ttk.LabelFrame(main_frame, text="Groups")
        self.group_frame.pack(fill=tk.X, padx=5, pady=2)
        # Create group buttons will go here.

        # Devices section
        self.device_frame = ttk.LabelFrame(main_frame, text="Devices")
        self.device_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        # Create device buttons will go here.

        # Tune button
        tune_frame = ttk.Frame(main_frame)
        tune_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tune_button = ttk.Button(tune_frame, text="Tune", command=lambda: on_tune_request_from_selection(self))
        tune_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        debug_logger(
            message=f"✅ Widgets created for ShowtimeTab.",
            **_get_log_args()
        )

    def _on_tab_selected(self, event):
        current_function = inspect.currentframe().f_code.co_name
        
        if event is None or event.widget.tab(event.widget.select(), "text") == "Showtime":
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message="🟢️️️🟢 'Showtime' tab activated. Reloading marker data and buttons.",
                    file=current_file,
                    version=current_version,
                    function=f"{self.__class__.__name__}.{current_function}",
                )
            load_marker_data(self)
            process_and_sort_markers(self)
            self._create_zone_buttons()
            self._create_group_buttons()
            self._create_device_buttons()
    
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message="✅ 'Showtime' tab setup complete.",
                    file=current_file,
                    version=current_version,
                    function=f"{self.__class__.__name__}.{current_function}",
                )

    # --- BUTTON CREATION METHODS ---

    def _create_zone_buttons(self):
        current_function = inspect.currentframe().f_code.co_name
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message="🟢️️️🟢 Creating Zone buttons.",
                **_get_log_args()
            )
        
        # Clear existing zone buttons
        for widget in self.zones_frame.winfo_children():
            widget.destroy()

        zone_buttons_frame = ttk.Frame(self.zones_frame)
        zone_buttons_frame.pack(fill=tk.X, padx=5, pady=2)

        for zone_name in sorted(self.grouped_markers.keys()):
            zone_button = ttk.Button(
                zone_buttons_frame,
                text=zone_name,
                command=lambda zn=zone_name: self._on_zone_toggle(zn),
                style='Custom.TButton'
            )
            zone_button.pack(side=tk.LEFT, padx=2, pady=2)
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"✅ Created button for Zone: {zone_name}.",
                    **_get_log_args()
                )

    def _create_group_buttons(self):
        current_function = inspect.currentframe().f_code.co_name
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message="🟢️️️🟢 Creating Group filter buttons.",
                **_get_log_args()
            )
        
        for widget in self.group_frame.winfo_children():
            widget.destroy()
        
        if self.selected_zone:
            self.group_frame.configure(text=f"GROUPS")
            self.group_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
            
            sorted_groups = sorted(self.grouped_markers[self.selected_zone].keys())
            for i, group_name in enumerate(sorted_groups):
                is_selected = self.selected_group == group_name

                group_devices = self.grouped_markers[self.selected_zone][group_name]
                # UPDATED: Use the imported utility function
                min_freq, max_freq = calculate_frequency_range(group_devices)
                
                freq_range_text = ""
                if min_freq is not None and max_freq is not None:
                    freq_range_text = f"\\n{min_freq} MHz - {max_freq} MHz"
                
                button_text = f"{group_name}{freq_range_text}"
                
                button = ttk.Button(
                    self.group_frame,
                    text=button_text,
                    command=lambda g=group_name: self._on_group_toggle(g),
                    style='Custom.TButton' if not is_selected else 'Custom.Selected.TButton'
                )
                row = i // 4
                col = i % 4
                button.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        else:
            self.group_frame.grid_remove()
            
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"✅ Group buttons updated for selected zone.",
                **_get_log_args()
            )

    def _create_device_buttons(self):
        current_function = inspect.currentframe().f_code.co_name
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message="🟢️️️🟢 Creating Device buttons.",
                **_get_log_args()
            )
        
        if self.selected_device_button:
            self.selected_device_button.config(style='Custom.TButton')
        self.selected_device_button = None

        for widget in self.device_frame.winfo_children():
            widget.destroy()
        
        filtered_devices = []
        if self.selected_zone and self.selected_group:
            filtered_devices = self.grouped_markers[self.selected_zone][self.selected_group]
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"🔍 Showing devices for Zone: {self.selected_zone} and Group: {self.selected_group}.",
                    **_get_log_args()               
                )
        elif self.selected_zone:
            for group_name in self.grouped_markers[self.selected_zone]:
                filtered_devices.extend(self.grouped_markers[self.selected_zone][group_name])
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"🔍 Showing all devices for selected Zone: {self.selected_zone}.",
                    **_get_log_args()               
                )
        else:
            filtered_devices = self.marker_data
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message="🔍 Showing all devices from MARKERS.csv.",
                    **_get_log_args()               
                )

        for i, row_data in enumerate(filtered_devices):
            button_text = (
                           f"{row_data.get('NAME', 'N/A')}\\n"
                           f"{row_data.get('DEVICE', 'N/A')}\\n"
                           f"{row_data.get('FREQ_MHZ', 'N/A')} MHz\\n"
                           f"[********************]"
                          )
            
            button = ttk.Button(
                self.device_frame,
                text=button_text,
                style='Custom.TButton'
            )
            # Store data directly on the button object
            button.marker_data = row_data
            button.configure(command=lambda b=button: self._on_marker_button_click(b))
            
            row = i // 4
            col = i % 4
            button.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"✅ Created {len(filtered_devices)} device buttons.",
                **_get_log_args()
            )

    # --- WRAPPER METHODS ---

    def _on_zone_toggle(self, zone_name):
        """Wrapper to call the imported on_zone_toggle function."""
        on_zone_toggle(self, zone_name)

    def _on_group_toggle(self, group_name):
        """Wrapper to call the imported on_group_toggle function."""
        on_group_toggle(self, group_name)

    def _on_marker_button_click(self, button):
        """Wrapper to call the imported on_marker_button_click function."""
        on_marker_button_click(self, button)