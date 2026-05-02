# oaGui/FileReaders/loader/resource_resolver.py
# Author: Anthony Peter Kuzub
# Version: 20260502.1000.1
#
# Description: Service for resolving GUI resources (JSON/Python) from a given path.

import os
import pathlib
from loguru import logger

def resolve_gui_resource(path: pathlib.Path):
    """
    Identifies if a path points to a valid GUI resource (Python class or JSON blueprint).
    Returns (python_path, json_path) or (None, None).
    """
    python_path = None
    json_path = None

    if path.is_dir():
        try:
            found_json = []
            found_py = []
            with os.scandir(str(path)) as it:
                for entry in it:
                    if entry.is_file() and not entry.name.startswith("__") and entry.name != "layout.json":
                        if entry.name.endswith(".json"):
                            found_json.append(pathlib.Path(entry.path))
                        elif entry.name.endswith(".py"):
                            found_py.append(pathlib.Path(entry.path))

            if found_json: json_path = sorted(found_json)[0]
            elif found_py: python_path = sorted(found_py)[0]
        except (FileNotFoundError, PermissionError) as error:
            logger.warning(f"ResourceResolver: Cannot access directory {path}: {error}")

    elif path.is_file():
        if path.suffix == ".json" and path.name != "layout.json":
            json_path = path
        elif path.suffix == ".py" and not path.name.startswith("__"):
            python_path = path
            
    return python_path, json_path
