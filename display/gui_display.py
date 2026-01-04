# display/gui_display.py
#
# The hash calculation drops the leading zero from the hour (e.g., 08 -> 8)
# Current time is 00:10, so the hash uses 10.
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
# Version 20251229.1725.1

from managers.configini.config_reader import Config
app_constants = Config.get_instance() # Get the singleton instance

# 📚 Python's standard library modules are our trusty sidekicks!
import os
import inspect
import tkinter as tk
from tkinter import ttk
import pathlib
import traceback 

# --- Module Imports ---
from workers.display.window_manager import WindowManager
from workers.display.module_loader import ModuleLoader
from workers.display.layout_parser import LayoutParser

# Import logger and styling utilities
# RESTORED: usage of _get_log_args to match the rest of the application protocol
from workers.logger.log_utils import _get_log_args 
from workers.logger.logger import debug_logger 
from workers.styling.style import THEMES, DEFAULT_THEME

# --- New MQTT and Logic Layer Imports ---
from workers.mqtt.mqtt_connection_manager import MqttConnectionManager
from workers.mqtt.mqtt_subscriber_router import MqttSubscriberRouter
from workers.logic.state_mirror_engine import StateMirrorEngine

class Application(ttk.Frame):
    """
    The main application class that orchestrates the GUI build process.
    OPTIMIZED: Implements Layout Caching and Guarded Logging.
    """
    def __init__(self, parent, root=None, mqtt_connection_manager=None, subscriber_router=None, state_mirror_engine=None, visa_proxy=None):
        super().__init__(parent)
        self.root = root
        self.app_constants = app_constants
        
        # ⚡ OPTIMIZATION: Initialize Cache for Directory Layouts
        # This prevents re-scanning the disk every time a tab is accessed.
        self._layout_cache = {}

        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message="🖥️🚦 The grand orchestrator is waking up! Let'S get this GUI built!",
                **_get_log_args()
            )
        
        # --- Initialize MQTT and Logic Layers (injected) ---
        self.mqtt_connection_manager = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self.state_mirror_engine = state_mirror_engine
        self.visa_proxy = visa_proxy # Store visa_proxy

            
        # Initialize utility classes
        self.theme_colors = self._apply_styles(theme_name="DEFAULT_THEME")
        self.window_manager = WindowManager(self)
        
        # Initialize LayoutParser
        self.layout_parser = LayoutParser(
            current_version=app_constants.CURRENT_VERSION, 
            # Pass debug_logger directly if LayoutParser needs it
            debug_log_func=debug_logger 
        )
        
        # Pass the state engine and subscriber router to the module loader
        self.module_loader = ModuleLoader(
            self.theme_colors,
            state_mirror_engine=self.state_mirror_engine,
            subscriber_router=self.subscriber_router
        )

        # Initialize storage
        self._notebooks = {}
        self._frames_by_path = {}
        self.last_selected_tab_name = None

        try:
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"🔍🔵 Applied theme: {DEFAULT_THEME}. The aesthetic enchantments are complete!",
                    **_get_log_args()
                )
            
            # Start the GUI build process
            self._build_from_directory(path=pathlib.Path(__file__).parent, parent_widget=self)
            
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message="🔍🔵 The architectural marvel is complete! Finished building GUI from directory structure.",
                    **_get_log_args()
                )
            
            # ⚡ OPTIMIZATION: 500ms delay to allow geometry to settle before heavy tab logic
            self.after(500, self._trigger_initial_tab_selection)

        except Exception as e:
            # Critical errors should always log, even if debug is off (optional, but good practice)
            # using print as fallback if logging fails
            error_msg = f"❌ Critical Error during application initialization: {e}"

            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"{error_msg}\nFull Traceback:\n{traceback.format_exc()}",
                    **_get_log_args()
                )

    def shutdown(self):
        """Gracefully shuts down the application."""
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message="Initiating application shutdown...",
                **_get_log_args()
            )
        
        self.mqtt_connection_manager.disconnect()
        if self.visa_proxy:
            self.visa_proxy.shutdown()

    def _trigger_initial_tab_selection(self):
        """Triggers the _on_tab_change event for the initially selected tab of each notebook."""
        if app_constants.global_settings['debug_enabled']:
             debug_logger(
                 message="🔍🔵 Triggering initial tab selection for all notebooks.",
                 **_get_log_args()
             )
        
        notebooks_to_process = list(self._notebooks.items())
        
        for notebook_path, notebook_widget in notebooks_to_process:
            try:
                # Create a dummy event object
                dummy_event = type('Event', (object,), {'widget': notebook_widget})()
                self._on_tab_change(dummy_event) 
                         
            except Exception as e:
                if app_constants.global_settings['debug_enabled']:
                    debug_logger(
                        message=f"❌🔴 Critical error during initial tab selection for {notebook_path}: {e}",
                        **_get_log_args()
                    )               
        
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message="✅ All initial tab selections triggered.",
                **_get_log_args()
            )

    def _apply_styles(self, theme_name: str):
        """Applies the specified theme to the entire application."""
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🔍🔵 Applying styles for theme: {theme_name}.",
                **_get_log_args()
            )
        
        colors = THEMES.get(theme_name, THEMES["dark"])
        style = ttk.Style(self)
        style.theme_use("clam")
        
        style.configure('.',
                        background=colors["bg"],
                        foreground=colors["fg"],
                        font=('Helvetica', 10),
                        padding=colors["padding"],
                        borderwidth=colors["border_width"])

        style.configure('TFrame', background=colors["bg"])

        # Use theme_colors for consistency. Assume "toggle" style values for custom buttons.
        dark_grey = colors.get("secondary", "#4e5254") 
        selected_orange = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggle"]["Button_Selected_Bg"]
        selected_fg = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggle"]["Button_Selected_Fg"] 
        
        hover_bg = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggle"]["Button_Hover_Bg"]
        hover_fg = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggle"]["Button_Hover_Fg"]

        style.configure('TButton', background=dark_grey, foreground=colors["text"], font=('Helvetica', 10, 'bold'), anchor='center') 
        style.map('TButton',
                  background=[('active', hover_bg), ('!active', dark_grey)],
                  foreground=[('active', hover_fg), ('!active', colors["text"])])

        style.configure('Custom.TButton', background=dark_grey, foreground=colors["text"], font=('Helvetica', 10, 'bold'), anchor='center') 
        style.map('Custom.TButton',
                  background=[('active', hover_bg), ('!active', dark_grey)],
                  foreground=[('active', hover_fg), ('!active', colors["text"])])

        # Configure Custom.TogglerUnselected.TButton
        toggler_unselected_bg = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggler_unselected"]["background"]
        toggler_unselected_fg = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggler_unselected"]["foreground"]
        toggler_hover_bg = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggler_unselected"]["Button_Hover_Bg"]
        toggler_hover_fg = THEMES[theme_name if theme_name in THEMES else DEFAULT_THEME]["button_style_toggler_unselected"]["Button_Hover_Fg"]

        style.configure('Custom.TogglerUnselected.TButton', background=toggler_unselected_bg, foreground=toggler_unselected_fg, font=('Helvetica', 10, 'bold'), anchor='center')
        style.map('Custom.TogglerUnselected.TButton',
                  background=[('active', toggler_hover_bg), ('!active', toggler_unselected_bg)],
                  foreground=[('active', toggler_hover_fg), ('!active', toggler_unselected_fg)])

        style.configure('Custom.Selected.TButton', background=selected_orange, foreground=selected_fg, relief="sunken", font=('Helvetica', 10, 'bold'), anchor='center')
        style.map('Custom.Selected.TButton',
                  background=[('active', hover_bg), ('!active', selected_orange)], 
                  foreground=[('active', hover_fg), ('!active', selected_fg)])

        style.configure('TNotebook',
                        background=colors["primary"],
                        borderwidth=0)
        
        style.configure('TNotebook.Tab',
                        padding=[colors["padding"] * 10, colors["padding"] * 5],
                        font=('Helvetica', 13), # Default to regular for unselected
                        borderwidth=0)
     
        style.map('TNotebook.Tab',
                  background=[('selected', colors["accent"]), ('!selected', colors["secondary"])],
                  foreground=[('selected', colors["accent_colors"][5]), ('!selected', colors["fg"])], # Darker blue
                  font=[('selected', ('Helvetica', 15, 'bold')), ('!selected', ('Helvetica', 13))]) # +2 points

     
        return colors

    def _get_layout_info(self, path: pathlib.Path):
        """
        ⚡ OPTIMIZATION HELPER: Checks cache before parsing directory.
        """
        path_str = str(path)
        # 1. Check RAM Cache
        if path_str in self._layout_cache:
            return self._layout_cache[path_str]

        # 2. Miss: Parse and Store
        layout_info = self.layout_parser.parse_directory(path)
        self._layout_cache[path_str] = layout_info
        return layout_info

    def _build_from_directory(self, path: pathlib.Path, parent_widget):
        """
        Recursively builds the GUI using Cached Layouts.
        """
        # ⚡ OPTIMIZATION: Guarded Log Call
        if app_constants.global_settings['debug_enabled']:
             debug_logger(
                 message=f"🏗️ _build_from_directory for path: '{path}'",
                 **_get_log_args()
             )

        # ⚡ OPTIMIZATION: Use Cached Layout Info
        layout_info = self._get_layout_info(path)
        layout_type = layout_info['type']
        layout_data = layout_info['data']

        if layout_type == 'error':
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"❌🔴 Layout parsing failed for {path}: {layout_data.get('error_message')}",
                    **_get_log_args()
                )
            return

        try:
            if layout_type == 'horizontal_split' or layout_type == 'vertical_split':
                orientation = layout_data['orientation']
                paned_window = ttk.PanedWindow(parent_widget, orient=orientation)
                paned_window.pack(fill=tk.BOTH, expand=True)

                def on_sash_drag(event):
                    self.update_idletasks()
                paned_window.bind("<B1-Motion>", on_sash_drag)

                percentages = layout_data.get('panel_percentages', [])
                for panel_info in layout_data['panels']:
                    sub_dir_path = panel_info['path']

                    # --- 🗺️ Objective 1: Temporal Crawler ---
                    if not self.layout_parser._scan_for_flux_capacitors(sub_dir_path):
                        if app_constants.global_settings['debug_enabled']:
                            debug_logger(
                                message=f"⏩ Pruning empty branch: Skipping panel '{sub_dir_path.name}' as it contains no GUI files.",
                                **_get_log_args()
                            )
                        continue 

                    weight = panel_info['weight']
                    
                    new_frame = ttk.Frame(paned_window, borderwidth=self.theme_colors["border_width"], relief=self.theme_colors["relief"])
                    paned_window.add(new_frame, weight=weight)
                    
                    self._build_from_directory(path=sub_dir_path, parent_widget=new_frame)

                def configure_sash(event):
                    total_percentage = sum(percentages)
                    if len(percentages) > 1 and total_percentage > 0:
                        sash_pos = int(event.width * (percentages[0] / total_percentage)) if orientation == tk.HORIZONTAL else int(event.height * (percentages[0] / total_percentage))
                        paned_window.tk.call(paned_window._w, 'sashpos', 0, sash_pos)
                        paned_window.unbind("<Configure>")

                paned_window.bind("<Configure>", configure_sash)

            elif layout_type == 'notebook':
                notebook = ttk.Notebook(parent_widget)
                notebook.pack(fill=tk.BOTH, expand=True)
                self._notebooks[path] = notebook
                
                notebook.bind('<Control-Button-1>', self.window_manager.tear_off_tab)
                notebook.bind('<<NotebookTabChanged>>', self._on_tab_change)
                notebook.bind('<<NotebookTabChanged>>', self._handle_tab_visibility, add='+')
                
                for tab_info in layout_data['tabs']:
                    tab_dir_path = tab_info['path']
                    display_name = tab_info['display_name']
                    
                    tab_frame = ttk.Frame(notebook)
                    tab_frame.grid_rowconfigure(0, weight=1)
                    tab_frame.grid_columnconfigure(0, weight=1)
                    tab_frame.grid(row=0, column=0, sticky="nsew") 
                    
                    self._frames_by_path[tab_dir_path] = tab_frame
                    
                    # === Lazy Loading Markers ===
                    tab_frame.is_populated = False
                    tab_frame.build_path = tab_dir_path
                    
                    notebook.add(tab_frame, text=display_name)

            elif layout_type == 'monitors':
                parent_widget.grid_rowconfigure(0, weight=1)
                parent_widget.grid_rowconfigure(1, weight=1)
                parent_widget.grid_rowconfigure(2, weight=1)
                parent_widget.grid_columnconfigure(0, weight=1)
                
                for i, gui_file_path in enumerate(layout_data['gui_files']):
                    frame_instance = self.module_loader.load_and_instantiate_gui(
                        path=gui_file_path, 
                        parent_widget=parent_widget
                    )
                    if frame_instance:
                        frame_instance.grid(row=i, column=0, sticky="nsew")

            elif layout_type == 'recursive_build':
                for child_dir_path in layout_data['child_containers']:
                    self.module_loader.load_and_instantiate_gui(
                        path=child_dir_path, 
                        parent_widget=parent_widget
                    )
                
                for gui_file_path in layout_data['gui_files']:
                    instance = self.module_loader.load_and_instantiate_gui(
                        path=gui_file_path, 
                        parent_widget=parent_widget
                    )
                    if instance:
                        instance.pack(fill=tk.BOTH, expand=True)
                        if app_constants.global_settings['debug_enabled']:
                            debug_logger(
                                message=f"✅ Successfully instantiated GUI from file: {gui_file_path}",
                                **_get_log_args()
                            ) 
                    else:
                        if app_constants.global_settings['debug_enabled']:
                            debug_logger(
                                message=f"❌ Failed to instantiate GUI from file: {gui_file_path}",
                                **_get_log_args()
                            ) 
            
            else: 
                # General Recursive Fallback
                sub_dirs = sorted([d for d in path.iterdir() if d.is_dir()])
                for sub_dir in sub_dirs:
                    dir_prefix = sub_dir.name.split('_')[0]
                    if not (dir_prefix in ['left', 'right', 'top', 'bottom'] or 
                            dir_prefix.isdigit() or 
                            sub_dir.name.startswith("child_")):
                        self._build_from_directory(path=sub_dir, parent_widget=parent_widget)

                py_files = sorted([f for f in path.iterdir() if f.is_file() and f.name.startswith("gui_") and f.suffix == '.py'])
                for py_file in py_files:
                    if app_constants.global_settings['debug_enabled']:
                        debug_logger(
                            message=f"🏗️ Attempting to instantiate GUI from file: {py_file}",
                            **_get_log_args()
                        ) 
                    instance = self.module_loader.load_and_instantiate_gui(path=py_file, parent_widget=parent_widget)
                    if instance:
                        instance.pack(fill=tk.BOTH, expand=True)
                        if app_constants.global_settings['debug_enabled']:
                            debug_logger(
                                message=f"✅ Successfully instantiated GUI from file: {py_file}",
                                **_get_log_args()
                            ) 
                    else:
                        if app_constants.global_settings['debug_enabled']:
                            debug_logger(
                                message=f"❌ Failed to instantiate GUI from file: {py_file}",
                                **_get_log_args()
                            ) 
            if self.root:
                self.root.update()

        except Exception as e:
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"❌🔴 Catastrophic structural failure in '_build_from_directory' for {path}: {e}",
                    **_get_log_args()
                )


    def print_to_console(self, message: str):
        """Placeholder method to print messages to a GUI console."""
        if app_constants.global_settings['debug_enabled']:
            debug_logger(
                message=f"🖥️💬 Observer's Log: {message}",
                **_get_log_args()
            )

    def _on_tab_change(self, event):
        """Logs a debug message, triggers lazy loading, and handles tab-specific actions."""
        # ⚡ OPTIMIZATION: Guarded Logging - Major Performance Gain
        if app_constants.global_settings['debug_enabled']:
             debug_logger(
                 message="▶️ _on_tab_change detected.",
                 **_get_log_args()
             )
        
        try:
            notebook = event.widget
            selected_tab_id = notebook.select()

            if not selected_tab_id:
                if app_constants.global_settings['debug_enabled']:
                    debug_logger(
                        message="No tab selected in notebook, skipping _on_tab_change logic.",
                        **_get_log_args()
                    )
                return
            
            selected_tab_frame = notebook.nametowidget(selected_tab_id)
            newly_selected_tab_name = notebook.tab(selected_tab_id, "text")

            # --- LAZY LOADING ---
            if not getattr(selected_tab_frame, "is_populated", False):
                build_path = getattr(selected_tab_frame, "build_path", None)
                if build_path:
                    if app_constants.global_settings['debug_enabled']:
                        debug_logger(
                            message=f"⚡ Lazy Loading engaged for tab: {newly_selected_tab_name}",
                            **_get_log_args()
                        )
                    
                    self._build_from_directory(path=build_path, parent_widget=selected_tab_frame)
                    
                    selected_tab_frame.is_populated = True
                    if app_constants.global_settings['debug_enabled']:
                        debug_logger(
                            message=f"✅ Lazy Loading complete for tab: {newly_selected_tab_name}",
                            **_get_log_args()
                        )

            # --- Standard Tab Change Logic ---
            self.last_selected_tab_name = newly_selected_tab_name
            
            if selected_tab_frame.winfo_children():
                content_widget = selected_tab_frame.winfo_children()[0]
                if hasattr(content_widget, '_on_tab_selected') and callable(getattr(content_widget, '_on_tab_selected')):
                    if app_constants.global_settings['debug_enabled']:
                        debug_logger(
                            message=f"Calling _on_tab_selected for {content_widget.__class__.__name__}.",
                            **_get_log_args()
                        )
                    content_widget._on_tab_selected(event)
            
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"⏹️_on_tab_change complete for '{newly_selected_tab_name}'.",
                    **_get_log_args()
                )

        except Exception as e:
            if app_constants.global_settings['debug_enabled']:
                debug_logger(
                    message=f"❌ Error in _on_tab_change: {e}",
                    **_get_log_args()
                )

    def _handle_tab_visibility(self, event):
        notebook = event.widget
        selected_tab_id = notebook.select()
        
        for tab_id in notebook.tabs():
            tab_frame = notebook.nametowidget(tab_id)
            if tab_frame.winfo_children():
                content_widget = tab_frame.winfo_children()[0]
                if tab_id == selected_tab_id:
                    if hasattr(content_widget, '_on_gui_visible'):
                        content_widget._on_gui_visible(event)
                else:
                    if hasattr(content_widget, '_on_gui_hidden'):
                        content_widget._on_gui_hidden(event)