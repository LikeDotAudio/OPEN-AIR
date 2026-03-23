# parser/layout_parser.py
# Author: Anthony Peter Kuzub
# Version: 20250821.200641.1
#
# Description: oaGuiDefinitions/layout_parser.py

import orjson
import os
import inspect
import pathlib
import tkinter as tk
from tkinter import ttk

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import LAYOUT_LOGGER
from loguru import logger

from oaConfiguration.FileReaders.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance


class LayoutParser:
    """
    Parses directory structures to determine the GUI layout (e.g., PanedWindow, Notebook).
    This is a stateless utility class.
    """
    # ⚡ OPTIMIZATION: Cache for _scan_for_gui_files to avoid redundant deep crawls
    _scan_cache = {}

    # Initializes the LayoutParser.
    # This constructor sets up the parser with the current application version.
    # Inputs:
    #     current_version (str): The current version string of the application.
    # Outputs:
    #     None.
    def __init__(self, current_version):
        self.current_version = current_version

    # Recursively scans a directory for the presence of GUI Python files.
    # This static method acts as a "Temporal Crawler" to determine if a directory
    # or any of its subdirectories contain files named `gui_*.py`, indicating
    # that it should be considered for GUI construction.
    # Inputs:
    #     path (pathlib.Path): The path to the directory to scan.
    # Outputs:
    #     bool: True if a `gui_*.py` file is found, False otherwise.
    @staticmethod
    def _scan_for_gui_files(path: pathlib.Path) -> bool:
        """
        Recursively checks if a folder or any of its sub-folders contain a '.json' or '.py' file.
        Uses os.scandir for speed and caches results.
        """
        path_str = str(path)
        if path_str in LayoutParser._scan_cache:
            return LayoutParser._scan_cache[path_str]

        result = False
        try:
            # ⚡ OPTIMIZATION: Use os.scandir instead of pathlib.iterdir for significant speed gains
            with os.scandir(path_str) as it:
                for entry in it:
                    if entry.is_file():
                        name = entry.name
                        # Acceptance criteria: any .json or .py file (excluding __init__ and layout.json)
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

    # Analyzes a directory structure to determine its intended GUI layout.
    # This method examines subdirectories and file naming conventions within the
    # given path to identify layout types such as horizontal/vertical splits, notebooks,
    # or recursive builds, returning a structured dictionary describing the layout.
    # Inputs:
    #     path (pathlib.Path): The path to the directory to analyze.
    # Outputs:
    #     dict: A dictionary describing the layout structure and relevant data.
    def parse_directory(self, path: pathlib.Path) -> dict:
        """
        Parses a directory to determine its layout type and gather relevant data.
        If a layout.json exists, it is used. Otherwise, defaults to directory listing.
        """
        layout_file = path / "layout.json"
        if layout_file.is_file():
            try:
                with open(layout_file, "r") as f:
                    layout_data = orjson.loads(f.read())
                # Centralize parsing logic by calling the new method
                return self.parse_layout_data(layout_data, path)
            except orjson.JSONDecodeError as e:
                return {"type": "error", "data": {"error_message": f"Invalid JSON: {e}"}}
        else:
            # Fallback to parsing based on directory naming conventions
            return self._parse_directory_listing(path)

    def parse_layout_data(self, layout_data: dict, source_path: pathlib.Path) -> dict:
        """
        Parses a pre-loaded layout dictionary to determine its layout type and gather data.
        This is the central parsing logic for layout dictionaries.
        """
        layout_type = layout_data.get("type", "unknown")
        parsed_data = {}

        if layout_type in ["horizontal_split", "vertical_split"]:
            orientation = tk.HORIZONTAL if layout_type == "horizontal_split" else tk.VERTICAL
            parsed_data["orientation"] = orientation
            raw_panels = layout_data.get("panels", [])
            percentages = layout_data.get("percentages", [])
            
            # Resolve relative paths and ensure weights are present
            resolved_panels = []
            for i, panel_item in enumerate(raw_panels):
                panel_path_str = panel_item if isinstance(panel_item, str) else panel_item.get("path")
                if not panel_path_str: continue

                resolved_path = source_path / panel_path_str
                weight = 1
                if i < len(percentages):
                    weight = percentages[i]
                elif isinstance(panel_item, dict) and "weight" in panel_item:
                    weight = panel_item["weight"]
                
                resolved_panels.append({"path": resolved_path, "weight": weight})

            parsed_data["panels"] = resolved_panels
            parsed_data["panel_percentages"] = [p.get("weight", 1) for p in resolved_panels]

        elif layout_type == "notebook":
            tabs = layout_data.get("tabs", [])
            resolved_tabs = []
            for tab_info in tabs:
                if isinstance(tab_info, dict) and "path" in tab_info and "display_name" in tab_info:
                    resolved_path = source_path / tab_info["path"]
                    resolved_tabs.append({"path": resolved_path, "display_name": tab_info["display_name"]})
            parsed_data["tabs"] = resolved_tabs

        elif layout_type == "monitors" or layout_type == "recursive_build":
            gui_files = [source_path / f for f in layout_data.get("gui_files", [])]
            # child_containers can be strings (paths) or dicts (nested layouts)
            child_containers = []
            for item in layout_data.get("child_containers", []):
                if isinstance(item, str):
                    child_containers.append(source_path / item)
                elif isinstance(item, dict):
                    child_containers.append(item) # Keep nested dicts as-is
            
            parsed_data["gui_files"] = gui_files
            parsed_data["child_containers"] = child_containers
        
        else: # Default or unknown, parse as a directory listing
             return self._parse_directory_listing(source_path)


        if LOCAL_DEBUG: LAYOUT_LOGGER.debug(f"Parsed layout data for '{source_path}': Type='{layout_type}', Data={orjson.dumps(parsed_data, default=str).decode()}")
        return {"type": layout_type, "data": parsed_data}

    def _parse_directory_listing(self, path: pathlib.Path) -> dict:
        """
        Fallback parser that inspects directory contents based on file/folder naming conventions.
        This handles the case where no layout.json is present.
        It uses a chain of responsibility: checks for splits, then notebooks, then defaults.
        """
        if LOCAL_DEBUG: LAYOUT_LOGGER.debug(f"Parsing directory listing via naming convention for: '{path}'")
        try:
            sub_dirs = sorted([d for d in path.iterdir() if d.is_dir() and not d.name.startswith('.') and not d.name.startswith('__')])
        except FileNotFoundError:
            LAYOUT_LOGGER.error(f"Error: Directory not found for parsing: {path}")
            return {"type": "error", "data": {"error_message": "Directory not found."}}

        # 1. Check for Split-Pane Layout
        layout_dirs = [d for d in sub_dirs if d.name.split("_")[0] in ["left", "right", "top", "bottom"]]
        if layout_dirs:
            is_horizontal = any(d.name.startswith("left_") or d.name.startswith("right_") for d in layout_dirs)
            is_vertical = any(d.name.startswith("top_") or d.name.startswith("bottom_") for d in layout_dirs)

            if is_horizontal and is_vertical:
                return {"type": "error", "data": {"error_message": "Mixed horizontal and vertical layouts."}}

            layout_type = "horizontal_split" if is_horizontal else "vertical_split"
            parsed_data = {
                "panels": [], 
                "panel_percentages": [],
                "orientation": tk.HORIZONTAL if is_horizontal else tk.VERTICAL
            }
            
            # Sort panels correctly
            sort_order = ["left", "right"] if is_horizontal else ["top", "bottom"]
            
            # We only sort the directories that match the convention
            # Other directories will be ignored by the split layout logic 
            # (they should ideally be inside the split panels)
            sorted_layout_dirs = sorted(layout_dirs, key=lambda d: sort_order.index(d.name.split("_")[0]))

            for sub_dir in sorted_layout_dirs:
                try:
                    percentage = int(sub_dir.name.split("_")[1])
                except (IndexError, ValueError):
                    percentage = 50
                parsed_data["panels"].append({"path": sub_dir, "weight": percentage})
                parsed_data["panel_percentages"].append(percentage)
            
            if LOCAL_DEBUG: LAYOUT_LOGGER.debug(f"Parsed '{layout_type}' from dir names '{path}'")
            return {"type": layout_type, "data": parsed_data}

        # 2. Check for Notebook Layout (Numerical Prefix)
        potential_tab_dirs = [d for d in sub_dirs if d.name and d.name[0].isdigit()]
        if potential_tab_dirs:
            # Only consider it a notebook if at least one numerical dir contains GUI files
            valid_tab_dirs = [d for d in potential_tab_dirs if self._scan_for_gui_files(d)]
            if valid_tab_dirs:
                layout_type = "notebook"
                parsed_data = {"tabs": []}
                
                # Sort numerically
                sorted_tabs = sorted(valid_tab_dirs, key=lambda d: int(d.name.split("_")[0]))
                
                for tab_dir in sorted_tabs:
                    parts = tab_dir.name.split("_")
                    display_name = " ".join(parts[1:]).title() if len(parts) > 1 else tab_dir.name
                    parsed_data["tabs"].append({"path": tab_dir, "display_name": display_name})

                if LOCAL_DEBUG: LAYOUT_LOGGER.debug(f"Parsed 'notebook' layout from dir names '{path}'")
                return {"type": layout_type, "data": parsed_data}

        # 3. Fallback to simple directory listing
        gui_files = sorted(
            [f for f in path.iterdir() if f.is_file() and (f.suffix == ".json" or f.suffix == ".py") and f.name != "layout.json" and not f.name.startswith("__")]
        )
        content_dirs = [d for d in sub_dirs if d not in layout_dirs and d not in potential_tab_dirs]

        if LOCAL_DEBUG: LAYOUT_LOGGER.debug(f"Parsed 'directory_listing' as fallback for '{path}'")
        return {
            "type": "directory_listing",
            "data": {
                "sub_dirs": [{"path": d} for d in content_dirs],
                "gui_files": gui_files,
            },
        }

