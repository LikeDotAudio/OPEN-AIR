# managers/Display/builder/gui_display.py
#
# This file defines the main Application class, which orchestrates the GUI build process.
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

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory
from loguru import logger

from managers.configini.config_reader import Config

app_constants = Config.get_instance()

# 📚 Python's standard library modules are our trusty sidekicks!
import os
import inspect
import tkinter as tk
from tkinter import ttk
import pathlib
import traceback
import orjson
import time

# --- Module Imports ---
from managers.Display.builder.window_manager import WindowManager
from managers.Display.loader.module_loader import ModuleLoader
from managers.Display.parser.layout_parser import LayoutParser

from workers.styling.style import THEMES, DEFAULT_THEME

# --- New MQTT and Logic Layer Imports ---
from workers.Command_Router.mqtt.mqtt_connection_manager import MqttConnectionManager
from workers.Command_Router.mqtt.mqtt_subscriber_router import MqttSubscriberRouter
from workers.logic.state_mirror_engine import StateMirrorEngine
from workers.initialization.worker_project_paths import LAYOUT_CACHE_PATH
from managers.Display.factory.widget_registry import WidgetRegistry


class Application(ttk.Frame):
    """
    The main application class that orchestrates the GUI build process.
    OPTIMIZED: Implements Persistent Layout Caching and Guarded Logging.
    """

    # Initializes the main Application class, setting up the core components of the GUI.
    # This constructor establishes the MQTT connection, state management, and utility classes
    # required for the application to function. It then initiates the GUI build process.
    # Inputs:
    #     parent (tk.Widget): The parent tkinter widget.
    #     root (tk.Tk, optional): The root tkinter window.
    #     mqtt_connection_manager (MqttConnectionManager): Manages the MQTT connection.
    #     subscriber_router (MqttSubscriberRouter): Routes incoming MQTT messages.
    #     state_mirror_engine (StateMirrorEngine): Manages the application's state.
    #     visa_proxy (VisaProxy): A proxy for VISA instrument communication.
    # Outputs:
    #     None.
    def __init__(
        self,
        parent,
        root=None,
        mqtt_connection_manager=None,
        subscriber_router=None,
        state_mirror_engine=None,
        state_cache_manager=None,
        osc_manager=None,
        aes70_manager=None,
        snmp_manager=None,
        midi_manager=None,
        visa_proxy=None,
        on_complete=None,
    ):
        """
        Initializes the main Application.

        Args:
            parent (tk.Widget): The parent widget.
            root (tk.Tk, optional): The root Tkinter window. Defaults to None.
            mqtt_connection_manager (MqttConnectionManager, optional): The MQTT connection manager. Defaults to None.
            subscriber_router (MqttSubscriberRouter, optional): The MQTT subscriber router. Defaults to None.
            state_mirror_engine (StateMirrorEngine, optional): The state mirror engine. Defaults to None.
            state_cache_manager (StateCacheManager, optional): The state cache manager. Defaults to None.
            visa_proxy (VisaProxy, optional): The VISA proxy object. Defaults to None.
            on_complete (callable, optional): Callback triggered when initial build pass is done.
        
        Returns:
            None
        """
        super().__init__(parent)
        self.root = root
        self.app_constants = app_constants
        self.on_complete_callback = on_complete

        # ⚡ AUTO-DISCOVERY: Scan for widgets at startup
        WidgetRegistry.scan_widgets()

        # ⚡ OPTIMIZATION: Persistent Layout Cache
        self._cache_file = LAYOUT_CACHE_PATH
        self._layout_cache = self._load_layout_cache()

        if LOCAL_DEBUG: logger.debug("🖥️🚦 The grand orchestrator is waking up! Let's get this GUI built!")

        # --- Initialize MQTT and Logic Layers (injected) ---
        self.mqtt_connection_manager = mqtt_connection_manager
        self.subscriber_router = subscriber_router
        self.state_mirror_engine = state_mirror_engine
        self.state_cache_manager = state_cache_manager
        self.osc_manager = osc_manager
        self.aes70_manager = aes70_manager
        self.snmp_manager = snmp_manager
        self.midi_manager = midi_manager
        self.visa_proxy = visa_proxy  # Store visa_proxy

        # ⚡ PROTOCOL ROUTER: Start the centralized hub
        from workers.Command_Router.protocol_router import ProtocolRouter
        ProtocolRouter.get_instance().start()

        # Initialize utility classes
        self.theme_colors = self._apply_styles(theme_name=DEFAULT_THEME)
        self.window_manager = WindowManager(self)

        # Initialize LayoutParser
        self.layout_parser = LayoutParser(
            current_version=app_constants.CURRENT_VERSION
        )

        # Pass the state engine and subscriber router to the module loader
        self.module_loader = ModuleLoader(
            self.theme_colors,
            state_mirror_engine=self.state_mirror_engine,
            subscriber_router=self.subscriber_router,
            app_instance=self,
        )

        # Initialize storage
        self._notebooks = {}
        self._frames_by_path = {}
        self.last_selected_tab_name = None
        
        # --- Resize Debouncing ---
        self.global_resizing = False
        self._resize_timer = None
        if self.root:
            self.root.bind("<Configure>", self._on_global_configure)

        try:
            if LOCAL_DEBUG:
                logger.debug(f"🖥️🏗️🎨 [DISPLAY] Applied theme: "
                             f"{DEFAULT_THEME}. Aesthetic enchantments done!")

            # ⚡ OPTIMIZATION: Use static project root from cache
            from workers.initialization.path_initializer import GLOBAL_PROJECT_ROOT
            root_dir = GLOBAL_PROJECT_ROOT / "display"
            
            def _start_build():
                self._build_from_directory(path=root_dir, parent_widget=self, 
                                           on_complete=self._on_initial_build_complete)

            self.after(10, _start_build)

        except Exception as e:
            # Gravity of Errors: Non-gated failure reporting.
            logger.exception(f"🖥️🏗️🎨 [DISPLAY] CRITICAL: App initialization "
                             f"failed. Forensic Report: {e}")

    def _on_initial_build_complete(self):
        """Callback for when the first pass of the GUI build finishes."""
        if LOCAL_DEBUG:
            logger.debug("🖥️🏗️🎨 [DISPLAY] Architectural marvel complete! "
                         "Finished building GUI structure.")

        # ⚡ OPTIMIZATION: 500ms delay to allow geometry to settle before heavy tab logic
        self.after(500, self._trigger_initial_tab_selection)
        
        # ⚡ OPTIMIZATION: Trigger State Restoration after UI is built
        if self.state_cache_manager:
            if LOCAL_DEBUG:
                logger.debug("🖥️🏗️🎨 [DISPLAY] UI Ready. Triggering state "
                             "restoration...")
            self.after(1000, self.state_cache_manager.initialize_state)

        # ⚡ OPTIMIZATION: Save cache after initial build
        self.after(2000, self._save_layout_cache)

        # ⚡ OPTIMIZATION: Start background tab pre-loading (DISABLED by User Request)
        # self.after(3000, self._start_background_tab_population)

        # ⚡ Trigger external completion callback
        if self.on_complete_callback:
            self.on_complete_callback()

    def _start_background_tab_population(self):
        """Starts the background population of unvisited tabs to prevent lag later."""
        # Find all unpopulated tabs
        unpopulated_tabs = []
        for path, frame in self._frames_by_path.items():
            if not getattr(frame, "is_populated", False) and not getattr(frame, "is_populating", False):
                unpopulated_tabs.append(frame)
        
        if not unpopulated_tabs:
            return

        # Pop one and schedule it
        target = unpopulated_tabs[0]
        # logger.debug(f"🏗️ Background Builder: Pre-loading tab {target.build_path.name}...")
        
        target.is_populating = True
        
        def _build_step():
            try:
                if not getattr(target, "is_populated", False): # Double check
                    self._build_from_directory(path=target.build_path, parent_widget=target)
                    target.is_populated = True
            except Exception as e:
                if LOCAL_DEBUG:
                    logger.error(f"Background build failed for {target.build_path}: {e}")
            finally:
                target.is_populating = False
                # Schedule next
                self.after(2000, self._start_background_tab_population)

        self.after(100, _build_step)

    def _load_layout_cache(self):
        """Loads the layout cache from disk."""
        if self._cache_file.exists():
            try:
                with open(self._cache_file, "rb") as f:
                    data = orjson.loads(f.read())
                return self._restore_cache_paths(data)
            except Exception as e:
                if LOCAL_DEBUG:
                    logger.exception("⚠️ Failed to load layout cache")
        return {}

    def _save_layout_cache(self):
        """Saves the layout cache to disk."""
        try:
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            serializable_cache = self._make_cache_serializable(self._layout_cache)
            with open(self._cache_file, "wb") as f:
                f.write(orjson.dumps(serializable_cache))
        except Exception as e:
             if LOCAL_DEBUG:
                 logger.exception("⚠️ Failed to save layout cache")

    def _make_cache_serializable(self, data):
        """Recursively converts Path objects to strings for JSON serialization."""
        if isinstance(data, dict):
            return {k: self._make_cache_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._make_cache_serializable(v) for v in data]
        elif isinstance(data, pathlib.Path):
            return str(data)
        return data

    def _restore_cache_paths(self, data):
        """Recursively restores Path objects from strings."""
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                if k in ["path", "build_path"] and isinstance(v, str):
                    new_dict[k] = pathlib.Path(v)
                elif k in ["gui_files", "child_containers"] and isinstance(v, list):
                    new_dict[k] = [pathlib.Path(item) if isinstance(item, str) else item for item in v]
                elif k in ["panels", "tabs"] and isinstance(v, list):
                    # These are lists of dictionaries that have 'path' keys
                    new_dict[k] = [self._restore_cache_paths(item) for item in v]
                else:
                    new_dict[k] = self._restore_cache_paths(v)
            return new_dict
        elif isinstance(data, list):
            return [self._restore_cache_paths(v) for v in data]
        return data

    def _get_layout_info(self, path: pathlib.Path):
        """
        Retrieves layout information for a given path, using a cache to avoid redundant parsing.
        Invalidates cache if the directory mtime has changed.
        """
        path_str = str(path)
        
        # ⚡ OPTIMIZATION: Check directory timestamp for invalidation
        try:
            current_mtime = path.stat().st_mtime
        except OSError:
            current_mtime = 0

        if path_str in self._layout_cache:
            cached_info = self._layout_cache[path_str]
            # If mtime matches, we can trust the cache
            if cached_info.get("mtime") == current_mtime:
                return cached_info

        # Re-parse if not in cache or if mtime changed
        layout_info = self.layout_parser.parse_directory(path)
        layout_info["mtime"] = current_mtime
        
        self._layout_cache[path_str] = layout_info
        return layout_info

    def _add_instance_to_parent(self, parent, instance, index=0):
        """Safely adds a widget instance to a parent using the parent's current geometry manager."""
        if not instance: return
        
        # Check if the parent already has slaves and which manager it uses
        manager = None
        if parent.winfo_children():
            # Check first child's manager
            manager = parent.winfo_children()[0].winfo_manager()
        
        if manager == "grid":
            instance.grid(row=index, column=0, sticky="nsew")
        elif manager == "pack":
            instance.pack(fill=tk.BOTH, expand=True)
        else:
            # Fallback: Prefer pack for simple containers, grid for multi-child ones
            instance.pack(fill=tk.BOTH, expand=True)

    def _build_from_directory(self, path: pathlib.Path, parent_widget, on_complete=None, layout_override=None):
        """
        Recursively builds the GUI from a directory structure or a provided layout dictionary.
        """
        if isinstance(path, str): path = pathlib.Path(path)
        if self.root: self.root.update()

        layout_info = None
        if layout_override:
            # If a layout dictionary is passed directly, use it
            layout_info = self.layout_parser.parse_layout_data(layout_override, source_path=path)
        else:
            # Otherwise, get it from the directory (which uses caching)
            layout_info = self._get_layout_info(path)
        
        layout_type = layout_info["type"]
        layout_data = layout_info["data"]

        if layout_type == "error":
            logger.error(f"❌🔴 Layout parsing failed for {path}: {layout_data.get('error_message')}")
            if on_complete: on_complete()
            return

        try:
            # --- LAYOUT-DRIVEN BUILD ---
            if layout_type == "horizontal_split" or layout_type == "vertical_split":
                orientation = layout_data["orientation"]
                paned_window = ttk.PanedWindow(parent_widget, orient=orientation)
                paned_window.pack(fill=tk.BOTH, expand=True)

                panels = layout_data.get("panels", [])
                
                panel_frames = [tk.Frame(paned_window, borderwidth=0, relief="flat", bg=self.theme_colors["bg"]) for _ in panels]
                for i, frame in enumerate(panel_frames):
                    weight = panels[i].get("weight", 1)
                    paned_window.add(frame, weight=weight)

                def _process_panels(idx=0):
                    if idx >= len(panels):
                        if on_complete: on_complete()
                        return
                    if self.root: self.root.update()

                    panel_path = panels[idx]["path"]
                    frame = panel_frames[idx]
                    
                    self._build_from_directory(path=panel_path, parent_widget=frame, on_complete=lambda: _process_panels(idx + 1))

                self.after(1, lambda: _process_panels(0))

                def configure_sash(event=None):
                    if not paned_window.winfo_exists(): return
                    w, h = paned_window.winfo_width(), paned_window.winfo_height()
                    if w <= 1 or h <= 1: return

                    total_weight = sum(p["weight"] for p in panels)
                    if total_weight == 0: return

                    cumulative_size = 0
                    for i in range(len(panels) - 1):
                        weight = panels[i]["weight"]
                        if orientation == tk.HORIZONTAL:
                            cumulative_size += (w * weight) / total_weight
                            paned_window.sashpos(i, int(cumulative_size))
                        else:
                            cumulative_size += (h * weight) / total_weight
                            paned_window.sashpos(i, int(cumulative_size))
                
                paned_window.bind("<Configure>", configure_sash, add="+")
                self.after(50, configure_sash)

            elif layout_type == "notebook":
                notebook = ttk.Notebook(parent_widget)
                notebook.pack(fill=tk.BOTH, expand=True)
                self._notebooks[path] = notebook

                notebook.bind("<Control-Button-1>", self.window_manager.tear_off_tab)
                notebook.bind("<Button-3>", self._on_notebook_right_click)
                notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
                notebook.bind("<<NotebookTabChanged>>", self._handle_tab_visibility, add="+")

                for tab_info in layout_data.get("tabs", []):
                    tab_path = tab_info["path"]
                    display_name = tab_info["display_name"]
                    tab_frame = tk.Frame(notebook, bg=self.theme_colors["bg"])
                    self._frames_by_path[tab_path] = tab_frame
                    tab_frame.is_populated = False
                    tab_frame.build_path = tab_path
                    notebook.add(tab_frame, text=display_name)
                
                if on_complete: on_complete()

            elif layout_type == "monitors" or layout_type == "recursive_build":
                container = tk.Frame(parent_widget, bg=self.theme_colors["bg"])
                container.pack(fill=tk.BOTH, expand=True)
                
                all_items = layout_data.get("gui_files", []) + layout_data.get("child_containers", [])
                
                if all_items:
                    container.grid_columnconfigure(0, weight=1)
                    slots = []
                    for i in range(len(all_items)):
                        container.grid_rowconfigure(i, weight=1, uniform="group")
                        slot = tk.Frame(container, bg=self.theme_colors["bg"])
                        slot.grid(row=i, column=0, sticky="nsew")
                        slots.append(slot)

                    def _process_recursive(idx=0):
                        if idx >= len(all_items):
                            if on_complete: on_complete()
                            return
                        if self.root: self.root.update()

                        item = all_items[idx]
                        slot = slots[idx]

                        if isinstance(item, dict):
                            self._build_from_directory(path=path, parent_widget=slot, on_complete=lambda: self.after(1, lambda: _process_recursive(idx + 1)), layout_override=item)
                        elif isinstance(item, (str, pathlib.Path)):
                            instance = self.module_loader.load_and_instantiate_gui(path=item, parent_widget=slot)
                            if instance:
                                instance.pack(fill=tk.BOTH, expand=True)
                            self.after(1, lambda: _process_recursive(idx + 1))
                        else:
                            logger.warning(f"🤷‍♂️ [BUILDER] Skipping unknown item type: {type(item)}")
                            self.after(1, lambda: _process_recursive(idx + 1))
                    
                    _process_recursive(0)
                elif on_complete:
                    on_complete()
            
            else: # 'directory_listing' or any other type
                self._process_default_directory_items(path, parent_widget, on_complete)

        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception(f"❌🔴 Catastrophic structural failure in '_build_from_directory' for {path}")
            if on_complete:
                on_complete()

    def _process_default_directory_items(self, path, parent_widget, on_complete):
        """Processes files and subdirectories in a default, iterative manner."""
        layout_info = self._get_layout_info(path)
        sub_dirs = layout_info["data"].get("sub_dirs", [])
        gui_files = layout_info["data"].get("gui_files", [])

        def _process_items(dir_idx=0, file_idx=0):
            if self.root: self.root.update()

            if dir_idx < len(sub_dirs):
                sub_dir_path = sub_dirs[dir_idx]["path"]
                self._build_from_directory(path=sub_dir_path, parent_widget=parent_widget, on_complete=lambda: _process_items(dir_idx + 1, file_idx))
                return
            
            if file_idx < len(gui_files):
                py_file = gui_files[file_idx]
                instance = self.module_loader.load_and_instantiate_gui(path=py_file, parent_widget=parent_widget)
                self._add_instance_to_parent(parent_widget, instance, file_idx)
                self.after(1, lambda: _process_items(dir_idx, file_idx + 1))
                return
            
            if on_complete: on_complete()

        _process_items()

    def print_to_console(self, message: str):
        if LOCAL_DEBUG: logger.debug(f"🖥️💬 Observer's Log: {message}")

    def _on_notebook_right_click(self, event):
        """Handles right-click on notebook tabs to open definition."""
        try:
            notebook = event.widget
            index = notebook.index(f"@{event.x},{event.y}")
            tab_id = notebook.tabs()[index]
            tab_frame = notebook.nametowidget(tab_id)
            self._trigger_wysiwyg_editor(tab_frame)
        except Exception as e:
            # Click likely outside a tab area
            pass

    def _trigger_wysiwyg_editor(self, widget):
        """Traverses widget hierarchy to find and invoke definition viewer."""
        queue = [widget]
        while queue:
            curr = queue.pop(0)
            
            # Check for direct method
            if hasattr(curr, "_show_wysiwyg_editor"):
                curr._show_wysiwyg_editor()
                return
            
            # Check for wrapper with dynamic_gui
            if hasattr(curr, "dynamic_gui"):
                if hasattr(curr.dynamic_gui, "_show_wysiwyg_editor"):
                    curr.dynamic_gui._show_wysiwyg_editor()
                    return
            
            # Continue search (breadth-first, shallow limit implied by use case)
            for child in curr.winfo_children():
                queue.append(child)

    def _trigger_initial_tab_selection(self):
        """Triggers _on_tab_change for initially selected tabs."""
        if LOCAL_DEBUG: logger.debug("🔍🔵 Triggering initial tab selection for all notebooks.")

        for notebook_path, notebook_widget in list(self._notebooks.items()):
            try:
                dummy_event = type("Event", (object,), {"widget": notebook_widget})()
                self._on_tab_change(dummy_event)
            except Exception:
                logger.exception(f"❌🔴 Critical error during initial tab selection for {notebook_path}")

    def _on_tab_change(self, event):
        if LOCAL_DEBUG:
            logger.debug("▶️ _on_tab_change detected.")
        try:
            notebook = event.widget
            selected_tab_id = notebook.select()
            if not selected_tab_id: return
            selected_tab_frame = notebook.nametowidget(selected_tab_id)
            newly_selected_tab_name = notebook.tab(selected_tab_id, "text")

            if not getattr(selected_tab_frame, "is_populated", False) and not getattr(selected_tab_frame, "is_populating", False):
                selected_tab_frame.is_populating = True
                build_path = getattr(selected_tab_frame, "build_path", None)
                if build_path:
                    if isinstance(build_path, str): build_path = pathlib.Path(build_path)
                    
                    # Use a loader callback to ensure the tab is visually responsive while loading
                    def _populate():
                        try:
                            self._build_from_directory(path=build_path, parent_widget=selected_tab_frame)
                            selected_tab_frame.is_populated = True
                        finally:
                            selected_tab_frame.is_populating = False
                    
                    self.after(10, _populate)

            self.last_selected_tab_name = newly_selected_tab_name
            if selected_tab_frame.winfo_children():
                content_widget = selected_tab_frame.winfo_children()[0]
                if hasattr(content_widget, "_on_tab_selected") and callable(getattr(content_widget, "_on_tab_selected")):
                    content_widget._on_tab_selected(event)
        except Exception as e:
            if LOCAL_DEBUG:
                logger.exception("❌ Error in _on_tab_change")

    def _handle_tab_visibility(self, event):
        notebook = event.widget
        selected_tab_id = notebook.select()
        for tab_id in notebook.tabs():
            tab_frame = notebook.nametowidget(tab_id)
            if tab_frame.winfo_children():
                content_widget = tab_frame.winfo_children()[0]
                if tab_id == selected_tab_id:
                    if hasattr(content_widget, "_on_gui_visible"):
                        content_widget._on_gui_visible(event)
                else:
                    if hasattr(content_widget, "_on_gui_hidden"):
                        content_widget._on_gui_hidden(event)

    def _on_global_configure(self, event):
        if event.widget == self.root:
            self.global_resizing = True
            if self._resize_timer:
                self.after_cancel(self._resize_timer)
            self._resize_timer = self.after(200, self._on_resize_finished)

    def _on_resize_finished(self):
        self._resize_timer = None
        self.global_resizing = False
        try:
            self.event_generate("<<GlobalResizeDone>>")
        except: pass

    def shutdown(self):
        if LOCAL_DEBUG: logger.debug("Initiating application shutdown...")
        self.mqtt_connection_manager.disconnect()
        if self.visa_proxy:
            self.visa_proxy.shutdown()

    def show_splinker_tab(self, src_topic=None, dest_topic=None):
        """
        Navigates to the Splinker tab and optionally populates it with topics.
        """
        target_path = pathlib.Path(self.app_constants.GLOBAL_PROJECT_ROOT) / "display/right_50/bottom_90/4_Splinker"
        target_frame = self._frames_by_path.get(target_path)
        
        if not target_frame:
            # Try relative path if absolute fails
            target_frame = self._frames_by_path.get(pathlib.Path("display/right_50/bottom_90/4_Splinker"))
            
        if target_frame:
            # Find the notebook that owns this tab
            notebook = target_frame.master
            if isinstance(notebook, ttk.Notebook):
                notebook.select(target_frame)
                
                # If topics provided, we need to find the SplinkerDashboard instance
                if src_topic or dest_topic:
                    def _update_dashboard():
                        # The dashboard might not be built yet if tab was never visited
                        if not getattr(target_frame, "is_populated", False):
                            self.after(100, _update_dashboard)
                            return
                            
                        # Search children for a widget that can handle pending topics
                        for child in target_frame.winfo_children():
                            # It might be nested in a few frames
                            queue = [child]
                            while queue:
                                curr = queue.pop(0)
                                # Look for our dashboard via duck-typing (no hard-coded invalid imports)
                                if hasattr(curr, 'set_pending_topics') and callable(getattr(curr, 'set_pending_topics')):
                                    curr.set_pending_topics(src_topic, dest_topic)
                                    return
                                for sub in curr.winfo_children():
                                    queue.append(sub)
                    
                    self.after(50, _update_dashboard)

    def _apply_styles(self, theme_name: str):
        if LOCAL_DEBUG: logger.debug(f"🔍🔵 Applying styles for theme: {theme_name}.")
        from workers.styling.theme_applier import apply_theme
        return apply_theme(self, theme_name)