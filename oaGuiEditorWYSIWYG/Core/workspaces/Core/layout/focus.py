# layout/focus.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import GUI_LOGGER as logger

from oaComBroker.Core.event_bus import event_bus
from ....state import state_manager

class FocusManager:
    """Handles path logic, array redirection, and event publishing for widget focus."""

    def __init__(self, workspace):
        self.workspace = workspace

    def handle_focus_request(self, path):
        if path is None:
            self.workspace.focused_path = None
            event_bus.publish("FOCUS_REQUESTED", path=None, source=self.workspace)
            self.workspace._force_overlay_refresh()
            return

        # ⚡ FORENSIC LOGGING: Track selection resolution
        matrix_log("ui", "gui_builder", "handle_focus_request", f"🖱️🖱️🖱️ [ACTION] FocusManager: Resolving path: {path}", "DEBUG")

        # Normalize path: The state_manager state might be { "root_key": { ... } }
        # If the path starts with the root key of the state, we keep it.
        # Otherwise, we might need to prepend or adjust.
        
        full_state = state_manager.get_state()
        root_keys = list(full_state.keys())
        
        # If the path doesn't start with a root key, and there is only one root key,
        # we might need to prepend it if state_manager.get_value_at_path(path) fails.
        if state_manager.get_value_at_path(path) is None:
            if len(root_keys) == 1 and not path.startswith(root_keys[0]):
                candidate_path = f"{root_keys[0]}.{path}"
                if state_manager.get_value_at_path(candidate_path) is not None:
                    path = candidate_path
                    matrix_log("ui", "gui_builder", "handle_focus_request", f"🖱️🖱️🖱️ [ACTION] FocusManager: Prepended root key. New path: {path}", "DEBUG")

        parts = str(path).split(".")
        for i in range(len(parts)):
            sub_path = ".".join(parts[:i+1])
            value = state_manager.get_value_at_path(sub_path)
            
            if isinstance(value, dict) and value.get("type") == "OcaArray":
                if len(parts) > i + 3 and parts[i+1] == "fields" and parts[i+3] == "fields":
                    path = f"{sub_path}.blueprint.{'.'.join(parts[i+3:])}"
                    break
                elif len(parts) > i + 1 and parts[i+1] == "fields":
                    path = f"{sub_path}.blueprint"
                    break

        self.workspace.focused_path = path
        event_bus.publish("FOCUS_REQUESTED", path=path, source=self.workspace)
        self.workspace._force_overlay_refresh()
