# Interface/layout_engine/focus.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Interface.1
#
# Description: Handles path logic and event publishing for widget focus.

from oaLogging.Methods.matrix_gate import matrix_log
from oaComBroker.Core.event_bus import event_bus
from ...Core.state import state_manager

class FocusManager:
    """Handles path logic, array redirection, and event publishing for widget focus."""

    def __init__(self, workspace):
        self.workspace = workspace

    def handle_focus_request(self, path):
        """Processes a focus request for a specific widget path."""
        if path is None:
            self._clear_focus()
            return

        matrix_log("ui", "gui_builder", "handle_focus_request", f"🖱️🖱️🖱️ [ACTION] FocusManager: Resolving path: {path}", "DEBUG")

        normalized_path = self._normalize_path(path)
        redirected_path = self._apply_array_redirection(normalized_path)

        self._apply_focus(redirected_path)

    def _clear_focus(self):
        """Clears the currently focused path."""
        self.workspace.focused_path = None
        event_bus.publish("FOCUS_REQUESTED", path=None, source=self.workspace)
        self.workspace._force_overlay_refresh()

    def _normalize_path(self, path):
        """Standardizes the path string based on the current state's root keys."""
        full_state = state_manager.get_state()
        if not full_state:
            return path
            
        root_keys = list(full_state.keys())
        if state_manager.get_value_at_path(path) is None:
            if len(root_keys) == 1 and not path.startswith(root_keys[0]):
                candidate_path = f"{root_keys[0]}.{path}"
                if state_manager.get_value_at_path(candidate_path) is not None:
                    matrix_log("ui", "gui_builder", "handle_focus_request", f"🖱️🖱️🖱️ [ACTION] FocusManager: Prepended root key.", "DEBUG")
                    return candidate_path
        return path

    def _apply_array_redirection(self, path):
        """Redirects focus from array elements to their blueprint for consistent editing."""
        parts = str(path).split(".")
        for i in range(len(parts)):
            sub_path = ".".join(parts[:i+1])
            value = state_manager.get_value_at_path(sub_path)
            
            if isinstance(value, dict) and value.get("type") == "OcaArray":
                # Redirect if path is deep within array fields
                if len(parts) > i + 3 and parts[i+1] == "fields" and parts[i+3] == "fields":
                    return f"{sub_path}.blueprint.{'.'.join(parts[i+3:])}"
                # Redirect if path points to the direct field list
                elif len(parts) > i + 1 and parts[i+1] == "fields":
                    return f"{sub_path}.blueprint"
        return path

    def _apply_focus(self, path):
        """Finalizes the focus state and publishes the update to the system."""
        self.workspace.focused_path = path
        event_bus.publish("FOCUS_REQUESTED", path=path, source=self.workspace)
        self.workspace._force_overlay_refresh()
