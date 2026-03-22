# Methods/mqtt_topic_utils.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import re
import pathlib
from pathlib import Path

# --- Constants ---
TOPIC_DELIMITER = "/"

# ⚡ OPTIMIZATION: Cache for topic paths
_topic_path_cache = {}

def generate_topic_path_from_filepath(file_path: Path, project_root: Path) -> str:
    """
    Generates a hierarchical MQTT topic path from a given file path.
    Strips sorting numbers (e.g. 'left_50' -> 'left', '1_Router' -> 'Router').
    """
    cache_key = (str(file_path), str(project_root))
    if cache_key in _topic_path_cache:
        return _topic_path_cache[cache_key]

    try:
        relative_path = file_path.relative_to(project_root)
        path_parts = list(relative_path.parts)
        if file_path.is_file():
            path_parts = path_parts[:-1]

        filtered_parts = []
        for part in path_parts:
            # ⚡ FILTER 1: Skip known structural layout tokens
            if part.lower() in ["display", "gui", "left", "right", "top", "bottom"]:
                continue
            
            # ⚡ FILTER 2: Skip pure digits (standalone sorting numbers like '50', '100', '1')
            if part.isdigit():
                continue
            
            # ⚡ CLEAN: Strip numeric prefix/suffix from mixed names (e.g. '1_Router' -> 'Router')
            # Handle both [-_] and just the number at the start/end
            clean = re.sub(r"^(\d+)[_-]?", "", part)
            clean = re.sub(r"[_-]?(\d+)$", "", clean)
            
            # Clean up remaining underscores/spaces for topic uniformity
            clean = clean.replace(" ", "_")
            
            # ⚡ DOUBLE-CHECK: If stripping the number left us with a layout token or nothing, skip it
            if not clean or clean.lower() in ["left", "right", "top", "bottom"]:
                continue
            
            if clean:
                filtered_parts.append(clean)

        result = TOPIC_DELIMITER.join(filtered_parts)
        _topic_path_cache[cache_key] = result
        return result
    except:
        return ""

def get_topic(*args) -> str:
    """Joins non-empty arguments with '/'."""
    return TOPIC_DELIMITER.join(str(arg) for arg in args if arg)

def generate_base_topic(module_name: str) -> str:
    """Generates a standardized base topic string."""
    return f"OPEN-AIR/{module_name}"

def generate_widget_topic(base_topic: str, widget_id: str) -> str:
    """Generates a standardized widget topic string."""
    return f"{base_topic}/{widget_id}"
