import pathlib

import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Core/directory.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk
from loguru import logger

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True

class DirectoryBuilderMixin:
    """
    Handles recursively building the GUI structure from a directory structure.
    """

    def _get_layout_info(self, path: pathlib.Path):
        """
        Retrieves layout information for a given path, using a cache to avoid redundant parsing.
        """
        path_str = str(path)
        
        # ⚡ OPTIMIZATION: Check directory timestamp for invalidation
        try:
            current_mtime = path.stat().st_mtime
        except OSError:
            current_mtime = 0

        if path_str in self._layout_cache:
            cached_entry = self._layout_cache[path_str]
            if cached_entry.get("mtime") == current_mtime:
                # ⚡ CACHE HIT: Return already normalized layout info directly.
                # Redundant re-normalization via parse_layout_data was causing failures 
                # because the parser expects 'raw' input, not already-normalized results.
                return cached_entry

        # Re-parse if not in cache or if mtime changed
        layout_info = self.layout_parser.parse_directory(path)
        layout_info["mtime"] = current_mtime
        self._layout_cache[path_str] = layout_info
        return layout_info

    def _add_instance_to_parent(self, parent, instance, index=0):
        """Safely adds a widget instance to a parent using the parent's current geometry manager."""
        if not instance: return
        manager = None
        if parent.winfo_children():
            manager = parent.winfo_children()[0].winfo_manager()
        
        if manager == "grid":
            instance.grid(row=index, column=0, sticky="nsew")
        elif manager == "pack":
            instance.pack(fill=tk.BOTH, expand=True)
        else:
            instance.pack(fill=tk.BOTH, expand=True)

    def _build_from_directory(self, path: pathlib.Path, parent_widget, on_complete=None, layout_override=None):
        """Recursively builds the GUI."""
        matrix_log("gui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🏗️ [BUILDER] Starting build for: {path}", "DEBUG")
        if isinstance(path, str): path = pathlib.Path(path)
        if hasattr(self, 'root') and self.root: self.root.update_idletasks()

        layout_info = None
        if layout_override:
            layout_info = self.layout_parser.parse_layout_data(layout_override, source_path=path)
        else:
            layout_info = self._get_layout_info(path)
        
        layout_type = layout_info["type"]
        layout_data = layout_info["data"]
        
        matrix_log("gui", "gui_builder", "_build_from_directory", f"🏗️ [BUILDER] Path: {path} | Type: {layout_type}", "INFO")

        if layout_type == "error":
            logger.error(f"❌🔴 Layout parsing failed for {path}: {layout_data.get('error_message')}")
            if on_complete: on_complete()
            return

        try:
            if layout_type in ["horizontal_split", "vertical_split"]:
                orientation = layout_data.get("orientation", tk.HORIZONTAL if layout_type == "horizontal_split" else tk.VERTICAL)
                matrix_log("gui", "gui_builder", "_build_from_directory", f"🏗️ [BUILDER] Creating SplitPane (Orient: {orientation})", "DEBUG")
                paned_window = ttk.PanedWindow(parent_widget, orient=orientation)
                
                try:
                    paned_window.pack(fill=tk.BOTH, expand=True)
                except tk.TclError as e:
                    matrix_log("gui", "gui_builder", "_build_from_directory", f"⚠️ PanedWindow pack skipped: {e}", "TRACE")

                panels = layout_data.get("panels", [])
                
                # Retrieve overflow settings for the current split pane
                # These are now parsed by LayoutParser and available in layout_data
                panel_overflow_ew = layout_data.get("overflow_ew", "auto")
                panel_overflow_ns = layout_data.get("overflow_ns", "auto")

                panel_widget_containers = [] # To store the widget that will contain the panel's content
                panel_frames = [] # Keep track of the base frames for each panel
                
                for i, panel_data in enumerate(panels):
                    # Create a base frame for the panel within the PanedWindow
                    base_frame = tk.Frame(paned_window, borderwidth=0, relief="flat", bg=self.theme_colors["bg"], width=10, height=10)
                    panel_frames.append(base_frame) # Keep track of the base frame
                    weight = int(panel_data.get("weight", 1))
                    matrix_log("gui", "gui_builder", "_build_from_directory", f"  ├─ Adding Panel {i}: Path={panel_data['path']}, Weight={weight}", "TRACE")
                    
                    widget_to_build_into = base_frame # Default: build directly into the frame
                    
                    # If overflow is 'auto' horizontally or vertically, create a scrollable canvas
                    if panel_overflow_ew == "auto" or panel_overflow_ns == "auto":
                        from oaGuiBuilder.Workers.builder import AutoScrollbar
                        # Create a canvas that will hold the scrollable content
                        canvas = tk.Canvas(base_frame, borderwidth=0, highlightthickness=0, relief="flat", bg=self.theme_colors["bg"])
                        
                        base_frame.grid_rowconfigure(0, weight=1)
                        base_frame.grid_columnconfigure(0, weight=1)
                        
                        h_scrollbar = None
                        if panel_overflow_ew == "auto":
                            h_scrollbar = AutoScrollbar(base_frame, orient=tk.HORIZONTAL, command=canvas.xview)
                            canvas.configure(xscrollcommand=h_scrollbar.set)
                        
                        v_scrollbar = None
                        if panel_overflow_ns == "auto":
                            v_scrollbar = AutoScrollbar(base_frame, orient=tk.VERTICAL, command=canvas.yview)
                            canvas.configure(yscrollcommand=v_scrollbar.set)

                        canvas.grid(row=0, column=0, sticky="nsew")
                        if h_scrollbar: h_scrollbar.grid(row=1, column=0, sticky="ew")
                        if v_scrollbar: v_scrollbar.grid(row=0, column=1, sticky="ns")

                        widget_to_build_into = canvas # Content will be built into the canvas
                    
                    panel_widget_containers.append(widget_to_build_into) # Store the widget to build into for this panel

                    try:
                        paned_window.add(base_frame) # Add the base frame to the PanedWindow
                        paned_window.pane(base_frame, weight=weight)
                    except tk.TclError as e:
                        matrix_log("gui", "gui_builder", "_build_from_directory", f"⚠️ Panel addition skipped: {e}", "TRACE")

                # Define _process_panels to recursively build content into the appropriate widget
                def _process_panels(panel_index=0):
                    if panel_index >= len(panels):
                        if on_complete: on_complete()
                        return
                    
                    if hasattr(self, 'root') and self.root: self.root.update_idletasks()
                    
                    panel_data = panels[panel_index]
                    panel_path = panel_data["path"]
                    
                    # Use the correct widget to build into (frame or canvas)
                    widget_to_build_into = panel_widget_containers[panel_index]
                    
                    # Pass down the overflow behavior settings for potential use by child widgets
                    behavior_override_for_panel = {
                        "behavior": {
                            "overflow_ew": panel_overflow_ew,
                            "overflow_ns": panel_overflow_ns
                        }
                    }
                    
                    self._build_from_directory(path=panel_path, parent_widget=widget_to_build_into, 
                                               on_complete=lambda: _process_panels(panel_index + 1), 
                                               layout_override=behavior_override_for_panel) # Pass override

                # Initial call to start processing panels
                self.after(1, lambda: _process_panels(0))

                paned_window.sash_config_in_progress = False

                def configure_sash(event=None):
                    if not paned_window.winfo_exists(): return
                    if getattr(paned_window, "sash_config_in_progress", False): return
                    
                    paned_window.sash_config_in_progress = True
                    try:
                        w, h = paned_window.winfo_width(), paned_window.winfo_height()
                        if w <= 20 or h <= 20: return
                        total_weight = sum(max(1, p.get("weight", 1)) for p in panels)
                        if total_weight == 0: return
                        cumulative_size = 0
                        last_pos = 0
                        
                        try:
                            for i in range(len(panels) - 1):
                                weight = max(1, panels[i].get("weight", 1))
                                if orientation == tk.HORIZONTAL:
                                    cumulative_size += (w * weight) / total_weight
                                    pos = max(last_pos + 1, min(int(w) - (len(panels) - i), int(cumulative_size)))
                                    # ⚡ HARDENING: Ensure pos is at least 1 and within bounds before calling sashpos
                                    pos = max(1, int(pos))
                                    paned_window.sashpos(i, pos)
                                else:
                                    cumulative_size += (h * weight) / total_weight
                                    pos = max(last_pos + 1, min(int(h) - (len(panels) - i), int(cumulative_size)))
                                    # ⚡ HARDENING: Ensure pos is at least 1 and within bounds before calling sashpos
                                    pos = max(1, int(pos))
                                    paned_window.sashpos(i, pos)
                                last_pos = pos
                        except tk.TclError as e:
                            # 🛡️ RECURSION GUARD: Catch TclErrors to prevent X11 BadValue (0x0) crashes 
                            # during rapid layout changes or initial settling.
                            matrix_log("gui", "gui_builder", "configure_sash", f"⚠️ Sash positioning skipped: {e}", "TRACE")
                    finally:
                        paned_window.sash_config_in_progress = False
                
                paned_window.bind("<Configure>", configure_sash, add="+")
                self.after(50, configure_sash)

            elif layout_type == "notebook":
                notebook = ttk.Notebook(parent_widget)
                notebook.pack(fill=tk.BOTH, expand=True)
                if hasattr(self, '_notebooks'): self._notebooks[path] = notebook

                if hasattr(self, 'window_manager'):
                    notebook.bind("<Control-Button-1>", self.window_manager.tear_off_tab)
                
                notebook.bind("<Button-3>", self._on_notebook_right_click)
                notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
                notebook.bind("<<NotebookTabChanged>>", self._handle_tab_visibility, add="+")

                for tab_info in layout_data.get("tabs", []):
                    tab_path = tab_info["path"]
                    display_name = tab_info["display_name"]
                    tab_frame = tk.Frame(notebook, bg=self.theme_colors["bg"])
                    if hasattr(self, '_frames_by_path'): self._frames_by_path[tab_path] = tab_frame
                    tab_frame.is_populated = False
                    tab_frame.build_path = tab_path
                    notebook.add(tab_frame, text=display_name)
                
                if on_complete: on_complete()

            elif layout_type in ["monitors", "recursive_build"]:
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
                        if hasattr(self, 'root') and self.root: self.root.update_idletasks()
                        item = all_items[idx]
                        slot = slots[idx]
                        if isinstance(item, dict):
                            self._build_from_directory(path=path, parent_widget=slot, on_complete=lambda: self.after(1, lambda: _process_recursive(idx + 1)), layout_override=item)
                        elif isinstance(item, (str, pathlib.Path)):
                            instance = self.module_loader.load_and_instantiate_gui(path=item, parent_widget=slot)
                            if instance: instance.pack(fill=tk.BOTH, expand=True)
                            self.after(1, lambda: _process_recursive(idx + 1))
                        else:
                            self.after(1, lambda: _process_recursive(idx + 1))
                    
                    _process_recursive(0)
                elif on_complete: on_complete()
            
            else:
                self._process_default_directory_items(path, parent_widget, on_complete)

        except Exception as e:
            if LOCAL_DEBUG: logger.exception(f"❌🔴 Build failure for {path}")
            if on_complete: on_complete()

    def _process_default_directory_items(self, path, parent_widget, on_complete):
        """Processes files and subdirectories."""
        layout_info = self._get_layout_info(path)
        sub_dirs = layout_info["data"].get("sub_dirs", [])
        gui_files = layout_info["data"].get("gui_files", [])

        def _process_items(dir_idx=0, file_idx=0):
            if hasattr(self, 'root') and self.root: self.root.update_idletasks()
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