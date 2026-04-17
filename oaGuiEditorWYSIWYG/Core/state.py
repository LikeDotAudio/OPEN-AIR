# Core/state.py
# Author: Gemini CLI
# Version: 1.0.0
#
# Description: The Central State Manager for the modular WYSIWYG editor.

import orjson
import copy
import inspect
from oaComBroker.Core.event_bus import event_bus
from oaLogging.Methods.matrix_gate import matrix_log

try:
    from oaRustCore.oa_editor_state_rs import EditorState as RustEditorState
    HAS_RUST = True
except ImportError:
    matrix_log(
        system='ui',
        element='state_manager',
        level='warning',
        message="🧠🔀🐌 [COMPUTE] oaeditorstate_rs not found. Falling back to slow Python state management.",
        func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
    )
    HAS_RUST = False
except Exception as e:
    matrix_log(
        system='ui',
        element='state_manager',
        level='error',
        message=f"🧠🔥👽 [COMPUTE] Failed to initialize Rust Editor State: {e}",
        func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
    )
    HAS_RUST = False

class SMLogger:
    def info(self, message):
        matrix_log(system='ui', element='state_manager', level='info', message=f"🧠⚙️⚙️ [COMPUTE] {message}", func_name=inspect.currentframe().f_code.co_name)
    def success(self, message):
        matrix_log(system='ui', element='state_manager', level='success', message=f"🧠🆗✅ [COMPUTE] {message}", func_name=inspect.currentframe().f_code.co_name)
    def warning(self, message):
        # MANDATE: Warnings are NOT gated. Standard logger for warnings.
        from oaLogging.Core.logger import WYSIWYG_LOGGER
        WYSIWYG_LOGGER.warning(f"⚠️🧠🤷‍♂️ [COMPUTE] StateManager: {message}")
    def error(self, message):
        # MANDATE: Errors are NOT gated.
        from oaLogging.Core.logger import WYSIWYG_LOGGER
        WYSIWYG_LOGGER.error(f"❌🧠🤦‍♂️ [COMPUTE] StateManager: {message}")
    def trace(self, message):
        matrix_log(system='ui', element='state_manager', level='trace', message=f"🧠🔬🔍 [COMPUTE] {message}", func_name=inspect.currentframe().f_code.co_name)

sm_logger = SMLogger()

class StateManager:
    """Manages the central JSON state of the GUI definition (RUST OPTIMIZED with Python fallback)."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            if HAS_RUST:
                try:
                    cls._instance._rust_state = RustEditorState()
                except Exception as e:
                    matrix_log(
                        system='ui',
                        element='state_manager',
                        level='error',
                        message=f"🧠🔥👻 [COMPUTE] Rust state instantiation failed: {e}",
                        func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
                    )
                    cls._instance._rust_state = None
            else:
                cls._instance._rust_state = None
            
            cls._instance._json_data = {} # Python fallback
            cls._instance._file_path = None
            cls._instance._original_state = {}
            # Subscribe to the event bus for component addition requests
            event_bus.subscribe("ADD_COMPONENT_REQUESTED", cls._instance._handle_add_component_request)
            matrix_log(
                system='ui',
                element='state_manager',
                level='trace',
                message=f"🧠✨🏗️ [COMPUTE] Singleton Instance Created ({'RUST' if HAS_RUST else 'PYTHON'}).",
                func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
            )
        return cls._instance

    def initialize(self, initial_data, file_path=None):
        """Initializes the state with starting JSON data."""
        matrix_log(
            system='ui',
            element='state_manager',
            level='info',
            message=f"🧠🛠️⚙️ [COMPUTE] Initialization started. Path: {file_path}",
            func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
        )
        self._original_state = copy.deepcopy(initial_data if initial_data is not None else {})
        self._json_data = copy.deepcopy(self._original_state)
        
        if self._rust_state:
            initial_str = orjson.dumps(self._original_state).decode()
            self._rust_state.initialize(initial_str)
        
        self._file_path = file_path
        
        # We need to broadcast the parsed data, so we fetch it back
        parsed_data = self.get_state()
        root_keys = list(parsed_data.keys())
        matrix_log(
            system='ui',
            element='state_manager',
            level='info',
            message=f"🧠⚖️📦 [COMPUTE] State loaded with {len(root_keys)} root elements.",
            func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
        )
        
        matrix_log(
            system='ui',
            element='state_manager',
            level='debug',
            message="🧠📡📤 [COMPUTE] Broadcasting initial STATE_UPDATED event...",
            func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
        )
        event_bus.publish("STATE_UPDATED", json_data=parsed_data)
        matrix_log(
            system='ui',
            element='state_manager',
            level='success',
            message="🧠🆗✅ [COMPUTE] StateManager: Initialization complete.",
            func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
        )

    def reset(self):
        """Resets the state manager to an empty state_manager."""
        matrix_log(
            system='ui',
            element='state_manager',
            level='info',
            message="🧠🔥🧹 [COMPUTE] Wiping internal state memory (Reset).",
            func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
        )
        if self._rust_state:
            self._rust_state.reset()
        self._json_data = {}
        self._file_path = None

    def get_state(self):
        """Returns the current master JSON data."""
        if self._rust_state:
            state_str = self._rust_state.get_state()
            return orjson.loads(state_str)
        # Treated as read-only reference to prevent O(N) deepcopy overhead
        return self._json_data

    def get_original_state(self):
        """Returns the original JSON data loaded during initialization."""
        return copy.deepcopy(self._original_state)

    def update_state(self, new_data, path=None, source=None):
        """
        Updates the master JSON state_manager.
        If path is provided (as a dot-notated string or list), updates a specific branch.
        """
        source_name = source.__class__.__name__ if source else "Unknown"
        matrix_log(
            system='ui',
            element='state_manager',
            level='info',
            message=f"🧠⚖️🔨 [COMPUTE] Update requested from {source_name}. Path: {path}",
            func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
        )
        
        path_list = []
        if path is not None and not (isinstance(path, (list, tuple)) and len(path) == 0):
            if isinstance(path, str):
                path_list = path.split(".")
            else:
                path_list = list(path)

        # Update Python fallback
        if not path_list:
            self._json_data = copy.deepcopy(new_data)
        else:
            current = self._json_data
            for part in path_list[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
            current[path_list[-1]] = copy.deepcopy(new_data)
                
        if self._rust_state:
            try:
                new_data_str = orjson.dumps(new_data).decode()
                self._rust_state.update_state(path_list, new_data_str)
            except Exception as e:
                # MANDATE: Exceptions are NOT gated.
                from oaLogging.Core.logger import WYSIWYG_LOGGER
                WYSIWYG_LOGGER.exception(f"❌🧠🔥 [COMPUTE] StateManager: Failed to update path {path} in Rust: {e}")
            
        matrix_log(
            system='ui',
            element='state_manager',
            level='trace',
            message="🧠📡📤 [COMPUTE] Broadcasting STATE_UPDATED event to subscribers.",
            func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
        )
        event_bus.publish("STATE_UPDATED", json_data=self.get_state(), source=source)

    def batch_update(self, updates, source=None):
        """
        Performs multiple updates and broadcasts a single STATE_UPDATED event.
        'updates' should be a list of (new_data, path) tuples.
        """
        source_name = source.__class__.__name__ if source else "Unknown"
        matrix_log(
            system='ui',
            element='state_manager',
            level='info',
            message=f"🧠🧮🔨 [COMPUTE] Batch update started from {source_name} ({len(updates)} changes).",
            func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
        )
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
                # MANDATE: Errors are NOT gated.
                from oaLogging.Core.logger import WYSIWYG_LOGGER
                WYSIWYG_LOGGER.error(f"❌🧠🔥 [COMPUTE] StateManager: Batch Error: Failed to update path {path}: {e}")
        
        matrix_log(
            system='ui',
            element='state_manager',
            level='info',
            message=f"🧠🆗✅ [COMPUTE] Batch update complete.",
            func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
        )
        event_bus.publish("STATE_UPDATED", json_data=self.get_state(), source=source)

    def reorder_element(self, path, direction, source=None):
        """Moves an element up or down within its sibling list."""
        matrix_log(
            system='ui',
            element='state_manager',
            level='info',
            message=f"🧠⚖️🔀 [COMPUTE] Reorder requested for '{path}' direction: {direction}",
            func_name=inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown"
        )
        if isinstance(path, str): path = path.split(".")
        if len(path) < 1: return
        
        key_to_move = path[-1]
        parent_path = path[:-1]
        
        parent = self._json_data
        for part in parent_path:
            parent = parent.get(part, {})
            
        if not isinstance(parent, dict): 
            # MANDATE: Warnings are NOT gated.
            from oaLogging.Core.logger import WYSIWYG_LOGGER
            WYSIWYG_LOGGER.warning(f"⚠️ StateManager: Cannot reorder. Parent at '{'.'.join(parent_path)}' is not a dict.")
            return
        
        keys = list(parent.keys())
        try:
            idx = keys.index(key_to_move)
        except ValueError:
            sm_logger.error(f"Cannot reorder. Key '{key_to_move}' not found in parent.")
            return
        
        sm_logger.trace(f"Element current index: {idx}. Neighbor count: {len(keys)}")
        
        if direction == "up" and idx > 0:
            keys[idx], keys[idx-1] = keys[idx-1], keys[idx]
        elif direction == "down" and idx < len(keys) - 1:
            keys[idx], keys[idx+1] = keys[idx+1], keys[idx]
        else:
            sm_logger.trace(f"Reorder '{key_to_move}' {direction} not possible (at boundary).")
            return # No move possible
            
        # Rebuild parent dict with new order
        sm_logger.trace(f"Rebuilding parent structure for order change...")
        new_parent = {k: parent[k] for k in keys}
        
        # Update state at parent level
        self.update_state(new_parent, path=parent_path, source=source)
        sm_logger.success(f"Successfully reordered '{key_to_move}' {direction}.")

    def move_element(self, path, target_parent_path, source=None):
        """Moves an element from its current location to a new parent."""
        sm_logger.info(f"MOVE OPERATION: {path} -> {target_parent_path}")
        value = self.get_value_at_path(path)
        if value is None: 
            sm_logger.error(f"Move failed. Source value at '{path}' not found.")
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
        
        target_parent[key] = value
        sm_logger.trace(f"  ↳ Inserted '{key}' into target parent '{'.'.join(target_parent_path)}'")
        
        sm_logger.trace("Move sequence complete. Broadcasting updated state_manager.")
        event_bus.publish("STATE_UPDATED", json_data=self._json_data, source=source)
        sm_logger.success(f"Successfully moved '{key}' to '{'.'.join(target_parent_path)}'.")

    def delete_element(self, path, source=None):
        """Removes an element from the state_manager."""
        sm_logger.info(f"DELETE OPERATION: {path}")
        if isinstance(path, str): path = path.split(".")
        if len(path) < 1: return
        
        key_to_delete = path[-1]
        parent_path = path[:-1]
        
        parent = self._json_data
        for part in parent_path:
            parent = parent.get(part, {})
            
        if isinstance(parent, dict) and key_to_delete in parent:
            del parent[key_to_delete]
            sm_logger.success(f"Successfully deleted '{key_to_delete}'.")
            event_bus.publish("STATE_UPDATED", json_data=self._json_data, source=source)
        else:
            sm_logger.warning(f"Delete failed. '{key_to_delete}' not found in parent.")

    def get_value_at_path(self, path):
        """Returns the value at a specific dot-notated path."""
        if isinstance(path, str):
            path = path.split(".")
        
        current = self.get_state()
        try:
            for part in path:
                current = current[part]
            return copy.deepcopy(current)
        except (KeyError, TypeError):
            return None

    def set_file_path(self, path):
        """Sets the file path for the current JSON state_manager."""
        sm_logger.info(f"Active File Path updated to: {path}")
        self._file_path = path

    def get_file_path(self):
        """Returns the current file path."""
        return self._file_path

    def _handle_add_component_request(self, component_name, component_schema, target_path, source=None):
        """
        Handles the ADD_COMPONENT_REQUESTED event by updating the state manager
        with the new component schema at the specified target path.
        """
        source_name = source.__class__.__name__ if source else "Unknown"
        sm_logger.info(f"Handling ADD_COMPONENT_REQUESTED for '{component_name}' from {source_name} at path '{target_path}'.")
        
        # Use the existing update_state method to add the component.
        # The update_state method already handles broadcasting STATE_UPDATED.
        self.update_state(new_data=component_schema, path=target_path, source=source)
        sm_logger.success(f"Component '{component_name}' successfully added to state at '{target_path}'.")

# Global instance
state_manager = StateManager()
