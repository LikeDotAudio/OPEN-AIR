import pathlib

# FileReaders/directory_loader.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose
import tkinter as tk
from tkinter import ttk

from loguru import logger

from oaLogging.Methods.matrix_gate import matrix_log

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = False

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
                return cached_entry

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
            parent.grid_columnconfigure(0, weight=1)
            parent.grid_rowconfigure(index, weight=1)
            instance.grid(row=index, column=0, sticky="nsew")
        elif manager == "pack":
            instance.pack(fill=tk.BOTH, expand=True)
        else:
            parent.grid_columnconfigure(0, weight=1)
            parent.grid_rowconfigure(index, weight=1)
            instance.grid(row=index, column=0, sticky="nsew")

    def _build_from_directory(self, path: pathlib.Path, parent_widget, on_complete=None, layout_override=None):
        """Recursively builds the GUI via a modular dispatcher."""
        matrix_log("gui", "gui_builder", "_build_from_directory", f"🏗️ [BUILDER] Starting build for: {path}", "DEBUG")
        if isinstance(path, str): path = pathlib.Path(path)

        layout_info = layout_override and self.layout_parser.parse_layout_data(layout_override, source_path=path) or self._get_layout_info(path)
        
        layout_type = layout_info["type"]
        layout_data = layout_info["data"]

        if layout_type == "error":
            logger.error(f"❌🔴 Layout parsing failed for {path}: {layout_data.get('error_message')}")
            if on_complete: on_complete()
            return

        # Modular Dispatcher Table
        builders = {
            "multi_window": self._build_multi_window_layout,
            "horizontal_split": self._build_split_layout,
            "vertical_split": self._build_split_layout,
            "notebook": self._build_notebook_layout,
            "monitors": self._build_recursive_layout,
            "recursive_build": self._build_recursive_layout
        }

        builder_fn = builders.get(layout_type, self._build_default_layout)
        
        try:
            builder_fn(path, parent_widget, layout_data, on_complete)
        except Exception:
            if LOCAL_DEBUG: logger.exception(f"❌🔴 Build failure for {path} ({layout_type})")
            if on_complete: on_complete()

    def _build_multi_window_layout(self, path, parent_widget, layout_data, on_complete):
        """Orchestrates multi-window instantiation."""
        windows = layout_data.get("windows", [])
        
        def _process_windows(win_idx=0):
            if win_idx >= len(windows):
                if on_complete: on_complete()
                return
                
            win_data = windows[win_idx]
            path_to_build = win_data["path"]
            title = win_data["title"]
            
            if win_idx == 0:
                target_widget = parent_widget
                root = getattr(self, "root", None)
                if root and isinstance(root, tk.Tk):
                    root.title(f"OPEN-AIR: {title}")
            else:
                root = getattr(self, "root", None)
                target_window = tk.Toplevel(root) if root and isinstance(root, tk.Tk) else tk.Toplevel()
                target_window.title(f"OPEN-AIR: {title}")
                target_window.geometry("1024x768")
                target_window.configure(bg=self.theme_colors["bg"])
                target_widget = tk.Frame(target_window, bg=self.theme_colors["bg"])
                target_widget.pack(fill=tk.BOTH, expand=True)

            self._build_from_directory(
                path=path_to_build, 
                parent_widget=target_widget, 
                on_complete=lambda: self.after(1, lambda: _process_windows(win_idx + 1))
            )

        self.after(1, lambda: _process_windows(0))

    def _build_split_layout(self, path, parent_widget, layout_data, on_complete):
        """Constructs split-pane (horizontal/vertical) layouts."""
        orientation = layout_data.get("orientation", tk.HORIZONTAL)
        paned_window = ttk.PanedWindow(parent_widget, orient=orientation)

        try:
            paned_window.pack(fill=tk.BOTH, expand=True)
        except tk.TclError as e:
            matrix_log("gui", "gui_builder", "_build_from_directory", f"⚠️ PanedWindow pack skipped: {e}", "TRACE")

        panels = layout_data.get("panels", [])
        overflow_ew = layout_data.get("overflow_ew", "none")
        overflow_ns = layout_data.get("overflow_ns", "none")

        containers = []
        for i, panel_data in enumerate(panels):
            base_frame = tk.Frame(paned_window, borderwidth=0, relief="flat", bg=self.theme_colors["bg"], width=1, height=1)
            base_frame.grid_rowconfigure(0, weight=1); base_frame.grid_columnconfigure(0, weight=1)
            
            target = base_frame
            if overflow_ew == "auto" or overflow_ns == "auto":
                from oaGui.Workers.builder import AutoScrollbar
                canvas = tk.Canvas(base_frame, borderwidth=0, highlightthickness=0, relief="flat", bg=self.theme_colors["bg"])
                if overflow_ew == "auto":
                    h_scroll = AutoScrollbar(base_frame, orient=tk.HORIZONTAL, command=canvas.xview)
                    canvas.configure(xscrollcommand=h_scroll.set)
                    h_scroll.grid(row=1, column=0, sticky="ew")
                if overflow_ns == "auto":
                    v_scroll = AutoScrollbar(base_frame, orient=tk.VERTICAL, command=canvas.yview)
                    canvas.configure(yscrollcommand=v_scroll.set)
                    v_scroll.grid(row=0, column=1, sticky="ns")
                canvas.grid(row=0, column=0, sticky="nsew")
                target = canvas

            containers.append(target)
            paned_window.add(base_frame)
            paned_window.pane(base_frame, weight=int(panel_data.get("weight", 1)), sticky="nsew")

        def _process_panels(idx=0):
            if idx >= len(panels):
                if on_complete: on_complete()
                return
            
            override = {"behavior": {"overflow_ew": overflow_ew, "overflow_ns": overflow_ns}}
            self._build_from_directory(path=panels[idx]["path"], parent_widget=containers[idx],
                                       on_complete=lambda: _process_panels(idx + 1),
                                       layout_override=override)

        self.after(1, lambda: _process_panels(0))
        self._bind_sash_configuration(paned_window, panels, orientation)

    def _bind_sash_configuration(self, paned_window, panels, orientation):
        """Handles responsive sash positioning for PanedWindows."""
        paned_window.sash_config_in_progress = False

        def configure_sash(event=None):
            if not paned_window.winfo_exists() or getattr(paned_window, "sash_config_in_progress", False): return
            paned_window.sash_config_in_progress = True
            try:
                w, h = paned_window.winfo_width(), paned_window.winfo_height()
                if w <= 20 or h <= 20: return
                total_weight = sum(max(1, p.get("weight", 1)) for p in panels)
                if total_weight == 0: return
                size, cumulative = (w, 0) if orientation == tk.HORIZONTAL else (h, 0)
                last_pos = 0
                for i in range(len(panels) - 1):
                    cumulative += (size * max(1, panels[i].get("weight", 1))) / total_weight
                    pos = max(last_pos + 1, min(int(size) - (len(panels) - i), int(cumulative)))
                    paned_window.sashpos(i, max(1, int(pos)))
                    last_pos = pos
            except tk.TclError: pass
            finally: paned_window.sash_config_in_progress = False

        paned_window.bind("<Configure>", configure_sash, add="+")
        self.after(50, configure_sash)

    def _build_notebook_layout(self, path, parent_widget, layout_data, on_complete):
        """Constructs tabbed notebook layouts."""
        notebook = ttk.Notebook(parent_widget)
        notebook.pack(fill=tk.BOTH, expand=True)
        if hasattr(self, '_notebooks'): self._notebooks[path] = notebook
        if hasattr(self, 'window_manager'): notebook.bind("<Control-Button-1>", self.window_manager.tear_off_tab)

        notebook.bind("<Button-3>", self._on_notebook_right_click)
        notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
        notebook.bind("<<NotebookTabChanged>>", self._handle_tab_visibility, add="+")

        for tab_info in layout_data.get("tabs", []):
            tab_path = tab_info["path"]
            tab_frame = tk.Frame(notebook, bg=self.theme_colors["bg"])
            if hasattr(self, '_frames_by_path'): self._frames_by_path[tab_path] = tab_frame
            tab_frame.is_populated = False
            tab_frame.build_path = tab_path
            notebook.add(tab_frame, text=tab_info["display_name"])

        if on_complete: on_complete()

    def _build_recursive_layout(self, path, parent_widget, layout_data, on_complete):
        """Constructs recursive/nested container layouts."""
        container = tk.Frame(parent_widget, bg=self.theme_colors["bg"])
        container.pack(fill=tk.BOTH, expand=True)
        all_items = layout_data.get("gui_files", []) + layout_data.get("child_containers", [])

        if not all_items:
            if on_complete: on_complete()
            return

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

            item = all_items[idx]
            slot = slots[idx]
            if isinstance(item, dict):
                self._build_from_directory(path=path, parent_widget=slot, 
                                           on_complete=lambda: self.after(1, lambda: _process_recursive(idx + 1)), 
                                           layout_override=item)
            elif isinstance(item, (str, pathlib.Path)):
                instance = self.module_loader.load_and_instantiate_gui(path=item, parent_widget=slot)
                self._add_instance_to_parent(slot, instance, 0)
                self.after(1, lambda: _process_recursive(idx + 1))
            else:
                self.after(1, lambda: _process_recursive(idx + 1))

        _process_recursive(0)

    def _build_default_layout(self, path, parent_widget, layout_data, on_complete):
        """Fallback builder for standard directory listings."""
        sub_dirs = layout_data.get("sub_dirs", [])
        gui_files = layout_data.get("gui_files", [])

        def _process_items(dir_idx=0, file_idx=0):
            if dir_idx < len(sub_dirs):
                self._build_from_directory(path=sub_dirs[dir_idx]["path"], parent_widget=parent_widget, 
                                           on_complete=lambda: _process_items(dir_idx + 1, file_idx))
                return
            if file_idx < len(gui_files):
                instance = self.module_loader.load_and_instantiate_gui(path=gui_files[file_idx], parent_widget=parent_widget)
                self._add_instance_to_parent(parent_widget, instance, file_idx)
                self.after(1, lambda: _process_items(dir_idx, file_idx + 1))
                return
            if on_complete: on_complete()

        _process_items()
