# oaGui/FileReaders/folder_layout_interpreter.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1001.1
#
# Description: Interprets file paths and directory structures as physical UI layout intents.

import os
import pathlib
import tkinter as tk
import orjson

from oaConfigurationManager.FileReaders.config_reader import Config
from oaLogging.Methods.matrix_gate import matrix_log

from oaGui.FileReaders.layout_detectors.multi_window_detector import MultiWindowDetector
from oaGui.FileReaders.layout_detectors.split_pane_detector import SplitPaneDetector
from oaGui.FileReaders.layout_detectors.notebook_detector import NotebookDetector
from oaGui.FileReaders.layout_detectors.equal_split_detector import EqualSplitDetector

app_constants = Config.get_instance()


class FolderLayoutInterpreter:
    """
    Interprets directory structures to determine the GUI layout (e.g., PanedWindow, Notebook).
    """
    _scan_cache = {}

    def __init__(self, current_version):
        self.current_version = current_version
        self._initialize_detectors()

    def _initialize_detectors(self):
        """Registry of layout detectors for automated structure interpretation."""
        self._detectors = [
            MultiWindowDetector(self),
            SplitPaneDetector(self),
            NotebookDetector(self),
            EqualSplitDetector(self)
        ]

    def _scan_for_gui_files(self, path: pathlib.Path) -> bool:
        """Recursively checks if a folder contains a '.json' or '.py' file."""
        path_str = str(path)
        if path_str in self._scan_cache:
            return self._scan_cache[path_str]

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
                        if self._scan_for_gui_files(pathlib.Path(entry.path)):
                            result = True
                            break
        except (FileNotFoundError, PermissionError):
            pass

        self._scan_cache[path_str] = result
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
        """Centralized interpreting logic for layout configuration dictionaries."""
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

        matrix_log("gui", "gui_manager", "FolderLayoutInterpreter", f"Interpreted: '{source_path}' | Type: '{layout_type}'", "DEBUG")
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
        for detector in self._detectors:
            result = detector.detect(path, sub_dirs, gui_files)
            if result:
                matrix_log("gui", "gui_manager", "FolderLayoutInterpreter", f"Interpreted: '{path}' | Type: '{result['type']}'", "DEBUG")
                return result

        matrix_log("gui", "gui_manager", "FolderLayoutInterpreter", f"Listing: '{path}' | Sub-dirs: {len(sub_dirs)} | Files: {len(gui_files)}", "DEBUG")
        return {
            "type": "directory_listing",
            "data": {
                "sub_dirs": [{"path": d} for d in sub_dirs],
                "gui_files": gui_files,
            },
        }
