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
                paned_window.pack(fill=tk.BOTH, expand=True)

                panels = layout_data.get("panels", [])
                panel_frames = [tk.Frame(paned_window, borderwidth=0, relief="flat", bg=self.theme_colors["bg"], width=1, height=1) for _ in panels]
                for i, frame in enumerate(panel_frames):
                    weight = int(panels[i].get("weight", 1))
                    matrix_log("gui", "gui_builder", "_build_from_directory", f"  ├─ Adding Panel {i}: Path={panels[i]['path']}, Weight={weight}", "TRACE")
                    paned_window.add(frame)
                    paned_window.pane(frame, weight=weight)

                def _process_panels(idx=0):
                    if idx >= len(panels):
                        if on_complete: on_complete()
                        return
                    if hasattr(self, 'root') and self.root: self.root.update_idletasks()
                    panel_path = panels[idx]["path"]
                    frame = panel_frames[idx]
                    matrix_log("gui", "gui_builder", "_build_from_directory", f"  └─ Building Panel Content: {panel_path}", "DEBUG")
                    self._build_from_directory(path=panel_path, parent_widget=frame, on_complete=lambda: _process_panels(idx + 1))

                self.after(1, lambda: _process_panels(0))

                def configure_sash(event=None):
                    if not paned_window.winfo_exists(): return
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