# FileReaders/layout_parser.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: oaGui/Assets/layout_parser.py

import inspect
import os
import pathlib
import tkinter as tk

import orjson

from oaConfigurationManager.FileReaders.config_reader import Config
from oaGui.Constants.schema_defaults import DEFAULT_PANEL_PERCENTAGE

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import LAYOUT_LOGGER
from oaLogging.Methods.matrix_gate import matrix_log

app_constants = Config.get_instance()  # Get the singleton instance


class LayoutParser:
    """
    Parses directory structures to determine the GUI layout (e.g., PanedWindow, Notebook).
    This is a stateless utility class.
    """
    _scan_cache = {}

    def __init__(self, current_version):
        self.current_version = current_version

    @staticmethod
    def _scan_for_gui_files(path: pathlib.Path) -> bool:
        """Recursively checks if a folder contains a '.json' or '.py' file."""
        path_str = str(path)
        if path_str in LayoutParser._scan_cache:
            return LayoutParser._scan_cache[path_str]

        result = False
        try:
            with os.scandir(path_str) as it:
                for entry in it:
                    if entry.is_file():
                        name = entry.name
                        if (name.endswith(".json") or name.endswith(".py")) and \
                           name != "layout.json" and not name.startswith("__"):
                            result = True
                            break
                    elif entry.is_dir() and not entry.name.startswith("__"):
                        if LayoutParser._scan_for_gui_files(pathlib.Path(entry.path)):
                            result = True
                            break
        except (FileNotFoundError, PermissionError):
            pass

        LayoutParser._scan_cache[path_str] = result
        return result

    def parse_directory(self, path: pathlib.Path) -> dict:
        """Determines layout type and gathers relevant data for a given path."""
        if not path.exists():
            return {"type": "error", "data": {"error_message": f"Path not found: {path}"}}

        if path.is_file():
            return self._parse_file_as_layout(path)

        layout_file = path / "layout.json"
        if layout_file.is_file():
            return self._parse_layout_json(layout_file, path)
        
        return self._parse_directory_listing(path)

    def _parse_file_as_layout(self, path: pathlib.Path) -> dict:
        if path.suffix in [".json", ".py"]:
            return {"type": "directory_listing", "data": {"sub_dirs": [], "gui_files": [path]}}
        return {"type": "error", "data": {"error_message": f"Not a valid GUI file: {path}"}}

    def _parse_layout_json(self, layout_file: pathlib.Path, source_path: pathlib.Path) -> dict:
        try:
            if layout_file.stat().st_size == 0:
                return {"type": "error", "data": {"error_message": "Empty layout.json"}}
            with open(layout_file, "rb") as f:
                layout_data = orjson.loads(f.read())
            return self.parse_layout_data(layout_data, source_path)
        except orjson.JSONDecodeError as e:
            return {"type": "error", "data": {"error_message": f"Invalid JSON: {e}"}}

    def parse_layout_data(self, layout_data: dict, source_path: pathlib.Path) -> dict:
        """Centralized parsing logic for layout configuration dictionaries."""
        layout_type = layout_data.get("type", "unknown")
        behavior = layout_data.get("behavior", {})
        
        parsed_data = {
            "overflow_ew": behavior.get("overflow_ew", "none"),
            "overflow_ns": behavior.get("overflow_ns", "none"),
            "fluid_ew": behavior.get("fluid_ew", False),
            "fluid_ns": behavior.get("fluid_ns", False)
        }

        if layout_type in ["horizontal_split", "vertical_split"]:
            self._gather_split_data(layout_data, layout_type, source_path, parsed_data)
        elif layout_type == "notebook":
            self._gather_notebook_data(layout_data, source_path, parsed_data)
        elif layout_type in ["monitors", "recursive_build"]:
            self._gather_recursive_data(layout_data, source_path, parsed_data)
        else:
            return self._parse_directory_listing(source_path)

        matrix_log("UI", "GUI_MANAGER", "_parse_layout_data", f"Parsed: '{source_path}' | Type: '{layout_type}'", "DEBUG")
        return {"type": layout_type, "data": parsed_data}

    def _gather_split_data(self, layout_data, layout_type, source_path, parsed_data):
        parsed_data["orientation"] = tk.HORIZONTAL if layout_type == "horizontal_split" else tk.VERTICAL
        raw_panels = layout_data.get("panels", [])
        percentages = layout_data.get("percentages", [])
        resolved = []
        for i, item in enumerate(raw_panels):
            path_str = item if isinstance(item, str) else item.get("path")
            if not path_str: continue
            weight = percentages[i] if i < len(percentages) else (item.get("weight", 1) if isinstance(item, dict) else 1)
            resolved.append({"path": source_path / path_str, "weight": weight})
        parsed_data["panels"] = resolved
        parsed_data["panel_percentages"] = [p["weight"] for p in resolved]

    def _gather_notebook_data(self, layout_data, source_path, parsed_data):
        tabs = layout_data.get("tabs", [])
        resolved = []
        for t in tabs:
            if isinstance(t, dict) and "path" in t and "display_name" in t:
                resolved.append({"path": source_path / t["path"], "display_name": t["display_name"]})
        parsed_data["tabs"] = resolved

    def _gather_recursive_data(self, layout_data, source_path, parsed_data):
        parsed_data["gui_files"] = [source_path / f for f in layout_data.get("gui_files", [])]
        children = []
        for item in layout_data.get("child_containers", []):
            children.append(source_path / item if isinstance(item, str) else item)
        parsed_data["child_containers"] = children

    def _parse_directory_listing(self, path: pathlib.Path) -> dict:
        """Infers layout type from directory contents using a rule-based sequence."""
        if path.is_file(): return self._parse_file_as_layout(path)
        if not path.is_dir(): return {"type": "error", "data": {"error_message": f"Invalid path: {path}"}}

        try:
            sub_dirs = sorted([d for d in path.iterdir() if d.is_dir() and not d.name.startswith('.') and not d.name.startswith('__')])
            gui_files = sorted([f for f in path.iterdir() if f.is_file() and f.suffix in [".json", ".py"] and f.name != "layout.json" and not f.name.startswith("__")])
        except FileNotFoundError:
            return {"type": "error", "data": {"error_message": "Directory not found."}}

        # Rule Sequence
        for detector in [self._detect_multi_window, self._detect_split_pane, self._detect_notebook, self._detect_equal_split]:
            result = detector(path, sub_dirs, gui_files)
            if result: return result

        return {
            "type": "directory_listing",
            "data": {
                "sub_dirs": [{"path": d} for d in sub_dirs],
                "gui_files": gui_files,
            },
        }

    def _detect_multi_window(self, path, sub_dirs, gui_files):
        window_dirs = [d for d in sub_dirs if d.name.lower().startswith("window_")]
        if window_dirs:
            return {"type": "multi_window", "data": {"windows": [{"path": d, "title": d.name.replace("_", " ")} for d in sorted(window_dirs)]}}
        return None

    def _detect_split_pane(self, path, sub_dirs, gui_files):
        layout_dirs = [d for d in sub_dirs if d.name.split("_")[0] in ["left", "right", "top", "bottom"]]
        if not layout_dirs: return None
        
        is_h = any(d.name.startswith(("left_", "right_")) for d in layout_dirs)
        is_v = any(d.name.startswith(("top_", "bottom_")) for d in layout_dirs)
        if is_h and is_v: return {"type": "error", "data": {"error_message": "Mixed orientation split."}}

        sort_order = ["left", "right"] if is_h else ["top", "bottom"]
        sorted_dirs = sorted(layout_dirs, key=lambda d: sort_order.index(d.name.split("_")[0]))
        
        panels = []
        for d in sorted_dirs:
            try: weight = int(d.name.split("_")[1])
            except (IndexError, ValueError): weight = DEFAULT_PANEL_PERCENTAGE
            panels.append({"path": d, "weight": weight})
        
        return {
            "type": "horizontal_split" if is_h else "vertical_split",
            "data": {"panels": panels, "panel_percentages": [p["weight"] for p in panels], "orientation": tk.HORIZONTAL if is_h else tk.VERTICAL}
        }

    def _detect_notebook(self, path, sub_dirs, gui_files):
        potential_tabs = [d for d in sub_dirs if d.name and d.name[0].isdigit()]
        valid_tabs = [d for d in potential_tabs if self._scan_for_gui_files(d)]
        if not valid_tabs: return None
        
        sorted_tabs = sorted(valid_tabs, key=lambda d: int(d.name.split("_")[0]))
        tabs = []
        for d in sorted_tabs:
            parts = d.name.split("_")
            name = " ".join(parts[1:]).title() if len(parts) > 1 else d.name
            tabs.append({"path": d, "display_name": name})
        return {"type": "notebook", "data": {"tabs": tabs}}

    def _detect_equal_split(self, path, sub_dirs, gui_files):
        numerical_files = [f for f in gui_files if f.name and f.name[0].isdigit()]
        if len(numerical_files) <= 1: return None
        
        weight = 100 // len(numerical_files)
        panels = [{"path": f, "weight": weight} for f in numerical_files]
        return {
            "type": "vertical_split",
            "data": {"panels": panels, "panel_percentages": [weight] * len(panels), "orientation": tk.VERTICAL}
        }

