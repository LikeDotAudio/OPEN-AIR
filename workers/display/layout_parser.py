# workers/display/layout_parser.py
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# This file is part of the OPEN-AIR project.
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.

import os
import inspect
import pathlib
import tkinter as tk
from tkinter import ttk
from workers.logger.log_utils import _get_log_args
from workers.logger.logger import debug_logger
from managers.configini.config_reader import Config

app_constants = Config.get_instance()  # Get the singleton instance


class LayoutParser:
    """
    Parses directory structures to determine the GUI layout (e.g., PanedWindow, Notebook).
    This is a stateless utility class.
    """

    def __init__(self, current_version, debug_log_func):
        self.current_version = current_version
        self.debug_log = (
            debug_log_func if debug_log_func else (lambda message, **kwargs: None)
        )

    @staticmethod
    def _scan_for_flux_capacitors(path: pathlib.Path) -> bool:
        """
        Recursively checks if a folder or any of its sub-folders contain a 'gui_*.py' file.
        This is the "Temporal Crawler" to avoid building empty containers.
        """
        try:
            for item in path.iterdir():
                if (
                    item.is_file()
                    and item.name.startswith("gui_")
                    and item.name.endswith(".py")
                ):
                    return True
                if item.is_dir() and not item.name.startswith("__"):
                    if LayoutParser._scan_for_flux_capacitors(item):
                        return True
        except (FileNotFoundError, PermissionError):
            return False
        return False

    def parse_directory(self, path: pathlib.Path) -> dict:
        """
        Analyzes a directory path to determine its intended GUI layout structure.
        Returns a dictionary describing the layout and relevant parsed data.
        """
        current_function_name = inspect.currentframe().f_code.co_name
        debug_logger(message=f"📂 Parsing directory: '{path}'", **_get_log_args())

        try:
            sub_dirs = sorted([d for d in path.iterdir() if d.is_dir()])
        except FileNotFoundError:
            debug_logger(
                message=f"❌ Error: Directory not found for parsing: {path}",
                **_get_log_args(),
            )
            return {"type": "error", "data": {"error_message": "Directory not found."}}

        layout_dirs = [
            d
            for d in sub_dirs
            if d.name.split("_")[0] in ["left", "right", "top", "bottom"]
        ]
        potential_tab_dirs = [d for d in sub_dirs if d.name and d.name[0].isdigit()]

        layout_type = "unknown"
        layout_data = {}

        if layout_dirs:
            is_horizontal = any(
                d.name.startswith("left_") or d.name.startswith("right_")
                for d in layout_dirs
            )
            is_vertical = any(
                d.name.startswith("top_") or d.name.startswith("bottom_")
                for d in layout_dirs
            )

            if is_horizontal and is_vertical:
                debug_logger(
                    message=f"❌ Layout Error: Cannot mix horizontal and vertical layouts in '{path}'.",
                    **_get_log_args(),
                )
                layout_type = "error"
                layout_data["error_message"] = "Mixed horizontal and vertical layouts."
            elif is_horizontal:
                layout_type = "horizontal_split"
                sort_order = ["left", "right"]
                sorted_layout_dirs = sorted(
                    layout_dirs, key=lambda d: sort_order.index(d.name.split("_")[0])
                )

                layout_data["orientation"] = tk.HORIZONTAL
                layout_data["panels"] = []
                percentages = []
                for sub_dir in sorted_layout_dirs:
                    if sub_dir.name.split("_")[0] not in ["left", "right"]:
                        continue
                    try:
                        percentage = int(sub_dir.name.split("_")[1])
                    except (IndexError, ValueError):
                        percentage = app_constants.UI_LAYOUT_SPLIT_EQUAL
                        debug_logger(
                            message=f"⚠️ Warning: Could not parse percentage from '{sub_dir.name}'. Defaulting to {percentage}.",
                            **_get_log_args(),
                        )
                    percentages.append(percentage)
                    layout_data["panels"].append(
                        {"name": sub_dir.name, "path": sub_dir, "weight": percentage}
                    )
                layout_data["panel_percentages"] = percentages
            elif is_vertical:
                layout_type = "vertical_split"
                sort_order = ["top", "bottom"]
                sorted_layout_dirs = sorted(
                    layout_dirs, key=lambda d: sort_order.index(d.name.split("_")[0])
                )

                layout_data["orientation"] = tk.VERTICAL
                layout_data["panels"] = []
                percentages = []
                for sub_dir in sorted_layout_dirs:
                    if sub_dir.name.split("_")[0] not in ["top", "bottom"]:
                        continue
                    try:
                        percentage = int(sub_dir.name.split("_")[1])
                    except (IndexError, ValueError):
                        percentage = app_constants.UI_LAYOUT_SPLIT_EQUAL
                        debug_logger(
                            message=f"⚠️ Warning: Could not parse percentage from '{sub_dir.name}'. Defaulting to {percentage}.",
                            **_get_log_args(),
                        )
                    percentages.append(percentage)
                    layout_data["panels"].append(
                        {"name": sub_dir.name, "path": sub_dir, "weight": percentage}
                    )
                layout_data["panel_percentages"] = percentages
            else:
                debug_logger(
                    message=f"⚠️ Found layout_dirs but no clear orientation detected in '{path}'.",
                    **_get_log_args(),
                )

        elif potential_tab_dirs:
            layout_type = "notebook"

            valid_tab_dirs = [
                d
                for d in potential_tab_dirs
                if LayoutParser._scan_for_flux_capacitors(d)
            ]

            tab_dirs = sorted(valid_tab_dirs, key=lambda d: int(d.name.split("_")[0]))

            layout_data["tabs"] = []
            for tab_dir in tab_dirs:
                parts = tab_dir.name.split("_")
                digit_part_index = -1
                for i, part in enumerate(parts):
                    if part.isdigit():
                        digit_part_index = i
                        break

                display_name = (
                    " ".join(parts[digit_part_index + 1 :]).title()
                    if digit_part_index != -1
                    else tab_dir.name
                )
                layout_data["tabs"].append(
                    {
                        "name": tab_dir.name,
                        "path": tab_dir,
                        "display_name": display_name,
                    }
                )

        elif "2_monitors" in str(path):
            layout_type = "monitors"
            layout_data["gui_files"] = sorted(
                [
                    f
                    for f in path.iterdir()
                    if f.is_file() and f.name.startswith("gui_") and f.suffix == ".py"
                ]
            )

        else:
            layout_type = "recursive_build"
            layout_data["child_containers"] = [
                d for d in sub_dirs if d.name.startswith("child_")
            ]
            layout_data["gui_files"] = sorted(
                [
                    f
                    for f in path.iterdir()
                    if f.is_file() and f.name.startswith("gui_") and f.suffix == ".py"
                ]
            )

        debug_logger(
            message=f"🗺️ Parsed layout for '{path}': Type='{layout_type}', Data={layout_data}",
            **_get_log_args(),
        )
        return {"type": layout_type, "data": layout_data}
