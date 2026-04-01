# Core/state.py
# Author: Gemini CLI
# Version: 1.0.0
#
# Description: The Central State Manager for the modular WYSIWYG editor.

import orjson
import copy
from .event_bus import event_bus
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

from .oaEditorState_rs.compiler_hook import ensure_compiled
ensure_compiled()
from .oaEditorState_rs.oaeditorstate_rs import EditorState as RustEditorState

# Specialized logger for StateManager to allow categorized filtering
sm_logger = logger.bind(category="STATE_MANAGER")

class StateManager:
    """Manages the central JSON state of the GUI definition (RUST OPTIMIZED)."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance._rust_state = RustEditorState()
            cls._instance._file_path = None
            sm_logger.trace("🧠 StateManager: Singleton Instance Created (RUST).")
        return cls._instance

    def initialize(self, initial_data, file_path=None):
        """Initializes the state with starting JSON data."""
        sm_logger.info(f"🧠 StateManager: Initialization started. Path: {file_path}")
        initial_str = orjson.dumps(initial_data if initial_data is not None else {}).decode()
        self._rust_state.initialize(initial_str)
        self._file_path = file_path
        
        # We need to broadcast the parsed data, so we fetch it back
        parsed_data = self.get_state()
        root_keys = list(parsed_data.keys())
        sm_logger.info(f"🧠 StateManager: State loaded with {len(root_keys)} root elements.")
        
        sm_logger.trace("🧠 StateManager: Broadcasting initial STATE_UPDATED event...")
        event_bus.publish("STATE_UPDATED", json_data=parsed_data)
        sm_logger.success("✅ StateManager: Initialization complete.")

    def reset(self):
        """Resets the state manager to an empty state_manager."""
        sm_logger.info("🧠 StateManager: Wiping internal state memory (Reset).")
        self._rust_state.reset()
        self._file_path = None

    def get_state(self):
        """Returns the current master JSON data."""
        state_str = self._rust_state.get_state()
        return orjson.loads(state_str)

    def update_state(self, new_data, path=None, source=None):
        """
        Updates the master JSON state_manager.
        If path is provided (as a dot-notated string or list), updates a specific branch.
        """
        source_name = source.__class__.__name__ if source else "Unknown"
        sm_logger.info(f"🔄 StateManager: Update requested from {source_name}. Path: {path}")
        
        new_data_str = orjson.dumps(new_data).decode()
        path_list = []
        if path is not None and not (isinstance(path, (list, tuple)) and len(path) == 0):
            if isinstance(path, str):
                path_list = path.split(".")
            else:
                path_list = list(path)
                
        try:
            self._rust_state.update_state(path_list, new_data_str)
        except Exception as e:
            sm_logger.exception(f"❌ StateManager Error: Failed to update path {path}: {e}")
            
        sm_logger.trace("🧠 StateManager: Broadcasting STATE_UPDATED event to subscribers.")
        event_bus.publish("STATE_UPDATED", json_data=self.get_state(), source=source)

    def batch_update(self, updates, source=None):
        """
        Performs multiple updates and broadcasts a single STATE_UPDATED event.
        'updates' should be a list of (new_data, path) tuples.
        """
        source_name = source.__class__.__name__ if source else "Unknown"
        sm_logger.info(f"🔄 StateManager: Batch update started from {source_name} ({len(updates)} changes).")
        for i, (new_data, path) in enumerate(updates):
            new_data_str = orjson.dumps(new_data).decode()
            path_list = []
            if path is not None and not (isinstance(path, (list, tuple)) and len(path) == 0):
                if isinstance(path, str):
                    path_list = path.split(".")
                else:
                    path_list = list(path)
            try:
                self._rust_state.update_state(path_list, new_data_str)
            except Exception as e:
                sm_logger.error(f"❌ StateManager Batch Error: Failed to update path {path}: {e}")
        
        sm_logger.info(f"✅ StateManager: Batch update complete.")
        event_bus.publish("STATE_UPDATED", json_data=self.get_state(), source=source)

    def reorder_element(self, path, direction, source=None):
        """Moves an element up or down within its sibling list."""
        sm_logger.info(f"↕️ StateManager: Reorder requested for '{path}' direction: {direction}")
        if isinstance(path, str): path = path.split(".")
        if len(path) < 1: return
        
        key_to_move = path[-1]
        parent_path = path[:-1]
        
        parent = self._json_data
        for part in parent_path:
            parent = parent.get(part, {})
            
        if not isinstance(parent, dict): 
            sm_logger.warning(f"❌ StateManager: Cannot reorder. Parent at '{'.'.join(parent_path)}' is not a dict.")
            return
        
        keys = list(parent.keys())
        try:
            idx = keys.index(key_to_move)
        except ValueError:
            sm_logger.error(f"❌ StateManager: Cannot reorder. Key '{key_to_move}' not found in parent.")
            return
        
        sm_logger.trace(f"↕️ StateManager: Element current index: {idx}. Neighbor count: {len(keys)}")
        
        if direction == "up" and idx > 0:
            keys[idx], keys[idx-1] = keys[idx-1], keys[idx]
        elif direction == "down" and idx < len(keys) - 1:
            keys[idx], keys[idx+1] = keys[idx+1], keys[idx]
        else:
            sm_logger.trace(f"↕️ StateManager: Reorder '{key_to_move}' {direction} not possible (at boundary).")
            return # No move possible
            
        # Rebuild parent dict with new order
        new_parent = {k: parent[k] for k in keys}
        
        # Update state at parent level
        sm_logger.trace(f"↕️ StateManager: Rebuilding parent structure for order change...")
        self.update_state(new_parent, path=parent_path, source=source)
        sm_logger.success(f"↕️ StateManager: Successfully reordered '{key_to_move}' {direction}.")

    def move_element(self, path, target_parent_path, source=None):
        """Moves an element from its current location to a new parent."""
        sm_logger.info(f"📦 StateManager: MOVE OPERATION: {path} -> {target_parent_path}")
        val = self.get_value_at_path(path)
        if val is None: 
            sm_logger.error(f"❌ StateManager: Move failed. Source value at '{path}' not found.")
            return
        
        # 1. Remove from old location
        if isinstance(path, str): path = path.split(".")
        key = path[-1]
        old_parent_path = path[:-1]
        old_parent = self._json_data
        for part in old_parent_path: old_parent = old_parent.get(part, {})
        if key in old_parent: 
            del old_parent[key]
            sm_logger.trace(f"  ↳ Removed '{key}' from source parent '{'.'.join(old_parent_path)}'")
        
        # 2. Add to new location
        if isinstance(target_parent_path, str): target_parent_path = target_parent_path.split(".")
        target_parent = self._json_data
        for part in target_parent_path:
            if part not in target_parent: target_parent[part] = {}
            target_parent = target_parent[part]
        
        target_parent[key] = val
        sm_logger.trace(f"  ↳ Inserted '{key}' into target parent '{'.'.join(target_parent_path)}'")
        
        sm_logger.trace("📦 StateManager: Move sequence complete. Broadcasting updated state_manager.")
        event_bus.publish("STATE_UPDATED", json_data=self._json_data, source=source)
        sm_logger.success(f"📦 StateManager: Successfully moved '{key}' to '{'.'.join(target_parent_path)}'.")

    def delete_element(self, path, source=None):
        """Removes an element from the state_manager."""
        sm_logger.info(f"🗑️ StateManager: DELETE OPERATION: {path}")
        if isinstance(path, str): path = path.split(".")
        if len(path) < 1: return
        
        key_to_delete = path[-1]
        parent_path = path[:-1]
        
        parent = self._json_data
        for part in parent_path:
            parent = parent.get(part, {})
            
        if isinstance(parent, dict) and key_to_delete in parent:
            del parent[key_to_delete]
            sm_logger.success(f"🗑️ StateManager: Successfully deleted '{key_to_delete}'.")
            event_bus.publish("STATE_UPDATED", json_data=self._json_data, source=source)
        else:
            sm_logger.warning(f"⚠️ StateManager: Delete failed. '{key_to_delete}' not found in parent.")

    def get_value_at_path(self, path):
        """Returns the value at a specific dot-notated path."""
        if isinstance(path, str):
            path = path.split(".")
        
        current = self._json_data
        try:
            for part in path:
                current = current[part]
            return copy.deepcopy(current)
        except (KeyError, TypeError):
            return None

    def set_file_path(self, path):
        """Sets the file path for the current JSON state_manager."""
        sm_logger.info(f"📂 StateManager: Active File Path updated to: {path}")
        self._file_path = path

    def get_file_path(self):
        """Returns the current file path."""
        return self._file_path

# Global instance
state_manager = StateManager()
