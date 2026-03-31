# Core/json.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import orjson
from oaLogging.Methods.matrix_gate import matrix_log
import inspect
from pathlib import Path
from oaLogging.Core.logger import builder_logger

# --- Standard Debug Logging Setup ---

class JsonDataManager:
    """
    Manages the state and persistence of JSON data for the tree viewer.
    Handles loading from files/strings and path-based updates.
    """

    def __init__(self):
        self.raw_data = None
        self.source_path = None
        self.dynamic_columns = []

    def load(self, source):
        """Loads JSON from a file path, raw string, or object."""
        try:
            if isinstance(source, str):
                p = Path(source)
                if not p.is_absolute():
                    # Resolve relative to project root
                    project_root = Path(__file__).parents[4]
                    resolved_p = project_root / source
                else:
                    resolved_p = p
                
                if resolved_p.exists() and resolved_p.is_file():
                    self.source_path = resolved_p
                    with open(resolved_p, "rb") as f:
                        self.raw_data = orjson.loads(f.read())
                elif source.strip().startswith(("{", "[")):
                    self.raw_data = orjson.loads(source)
                else:
                    self.raw_data = {"Error": f"File not found: {source}"}
            elif isinstance(source, (dict, list)):
                self.raw_data = source
            
            return self.raw_data
        except Exception as e:
            if BUILDER_DEBUG: builder_logger.exception(f"❌ Error loading JSON: {e}")
            self.raw_data = {"Error": str(e)}
            return self.raw_data

    def save_as(self, filename):
        """Saves the current data to a JSON file."""
        if self.raw_data is None: return False
        try:
            with open(filename, "wb") as f:
                f.write(orjson.dumps(self.raw_data, option=orjson.OPT_INDENT_2))
            self.source_path = Path(filename)
            return True
        except Exception as e:
            if BUILDER_DEBUG: builder_logger.exception(f"❌ Error saving JSON: {e}")
            return False

    def update_at_path(self, key_path, new_value):
        """Updates the internal data object at a specific hierarchical path."""
        if not key_path:
            self.raw_data = new_value
            return

        d = self.raw_data
        try:
            for i in range(len(key_path) - 1):
                d = d[key_path[i]]
            d[key_path[-1]] = new_value
        except (KeyError, IndexError, TypeError) as e:
            if BUILDER_DEBUG: builder_logger.error(f"❌ Data update failed: {e}")

    def discover_columns(self, depth_limit=3):
        """Iteratively scans data to find common keys for table view columns."""
        keys_found = set()
        stack = [(self.raw_data, 0)]

        while stack:
            d, depth = stack.pop()
            if depth > depth_limit: continue

            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(v, dict):
                        for sub_k in v.keys():
                            if not isinstance(v[sub_k], (dict, list)): keys_found.add(sub_k)
                    stack.append((v, depth + 1))
            elif isinstance(d, list):
                for item in d:
                    if isinstance(item, dict):
                        for sub_k in item.keys():
                            if not isinstance(item[sub_k], (dict, list)): keys_found.add(sub_k)
                    stack.append((item, depth + 1))

        priority = ["name", "id", "Value", "Start_MHz", "Stop_MHz", "MHz", "channel"]
        cols = [k for k in priority if k in keys_found]
        cols += sorted([k for k in keys_found if k not in priority])
        self.dynamic_columns = cols
        return cols
