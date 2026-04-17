# Interface/layout_engine/focus.py
# Author: Anthony Peter Kuzub
# Version: 20260416.Interface.1
#
# Description: Handles path logic and event publishing for widget focus.

from oaLogging.Methods.matrix_gate import matrix_log
from oaComBroker.Core.event_bus import event_bus
from ...Core.state import state_manager
import tkinter as tk

class FocusManager:
    """Handles path logic, array redirection, and event publishing for widget focus."""

    def __init__(self, workspace):
        self.workspace = workspace
        event_bus.subscribe("COMPONENT_DROPPED", self._on_component_dropped)

    def _on_component_dropped(self, x, y, name, schema):
        """Finds the widget under the drop point and adds the new component."""
        matrix_log("ui", "gui_builder", "drop", f"🎯🖱️🔨 [ACTION] FocusManager: Dropping component '{name}' at ({x}, {y})", "INFO")
        
        target = self.find_drop_target_at(x, y)
        if not target: 
            matrix_log("ui", "gui_builder", "drop", "🎯 [DROP] No valid target found at coordinates.", "WARNING")
            return
        
        tw, tp, tmode, tcoords = target
        
        if tp is not None:
            matrix_log("ui", "gui_builder", "drop", f"🎯 [DROP] target path: '{tp}' mode: {tmode}", "DEBUG")
            
            # Final target resolution
            final_target_parent = tp
            t_val = state_manager.get_value_at_path(tp)
            
            if isinstance(t_val, dict):
                w_type = t_val.get("type", "")
                if ("Block" in w_type or "Container" in w_type) and "fields" not in tp:
                    final_target_parent = f"{tp}.fields"
                elif "Table" in w_type and "rows" not in tp:
                    final_target_parent = f"{tp}.rows.0"
            
            # Generate a unique key
            base_key = name.lower().replace(" ", "_")
            key = base_key
            counter = 1
            search_path = f"{final_target_parent}.{key}" if final_target_parent else key
            while state_manager.get_value_at_path(search_path) is not None:
                key = f"{base_key}_{counter}"
                search_path = f"{final_target_parent}.{key}" if final_target_parent else key
                counter += 1
                
            final_path = f"{final_target_parent}.{key}" if final_target_parent else key
            matrix_log("ui", "gui_builder", "drop", f"🎯 [DROP] Final insertion path: '{final_path}'", "SUCCESS")
            state_manager.update_state(schema, path=final_path, source=self.workspace)
            self.workspace._manual_rebuild()

    def find_drop_target_at(self, x, y):
        """Resolves screen coordinates to a (widget, path, mode, coords) tuple for ghosting/dropping."""
        root = self.workspace.winfo_toplevel()
        target_widget = root.winfo_containing(x, y)
        if not target_widget: return None
        
        # 1. Walk up to find a path
        curr = target_widget
        path = None
        while curr:
            path = getattr(curr, '_oca_path', getattr(curr, 'oa_path', None))
            if path: break
            # 🛡️ SAFETY: If we hit the InteractiveLayout or RENDER_AREA, stop and handle as empty space
            if curr == self.workspace or curr == getattr(self.workspace, 'render_area', None):
                break
            curr = curr.master
            
        if not path:
            # Check if dropped on empty workspace area
            is_child = False; temp = target_widget
            render_area = getattr(self.workspace, 'render_area', None)
            while temp:
                if temp == render_area or temp == self.workspace: 
                    is_child = True; break
                temp = temp.master
            
            if is_child and render_area:
                full_state = state_manager.get_state()
                if not full_state: return None
                path = list(full_state.keys())[0]
                curr = render_area
            else:
                return None

        # 2. Resolve target characteristics
        val = state_manager.get_value_at_path(path)
        if not isinstance(val, dict):
            # Leaf -> Move to parent container
            path = ".".join(path.split(".")[:-1])
            val = state_manager.get_value_at_path(path)
            # Find the actual parent widget for this container path
            temp = target_widget
            found = False
            while temp:
                tp = getattr(temp, '_oca_path', getattr(temp, 'oa_path', None))
                if tp == path:
                    curr = temp; found = True; break
                temp = temp.master
            if not found: curr = render_area # Fallback to canvas

        if not isinstance(val, dict): return None

        # 3. Calculate visuals (RELATIVE TO GHOST OVERLAY which matches RENDER_AREA)
        # 🛡️ SAFETY: Ensure render_area exists, is mapped, and has valid geometry
        if not render_area or not render_area.winfo_exists():
            return None

        try:
            render_area.update_idletasks()
            ox = render_area.winfo_rootx()
            oy = render_area.winfo_rooty()
        except (tk.TclError, AttributeError):
            return None

        # Ensure target widget still exists
        if not curr or not curr.winfo_exists():
            curr = render_area # Absolute fallback

        w_type = val.get("type", "")
        try:
            curr.update_idletasks()
            wx1 = curr.winfo_rootx(); wy1 = curr.winfo_rooty()
            ww = curr.winfo_width(); wh = curr.winfo_height()
            
            if w_type in ["OcaBlock", "OcaBin", "OcaArray", "OcaContainer"]:
                # Container -> Append visual (bottom of container)
                return (curr, path, "append", (wx1-ox, wy1+wh-5-oy, wx1+ww-ox, wy1+wh-5-oy))
            else:
                # Widget -> Sibling insertion visual (top or bottom of widget)
                p_path = ".".join(path.split(".")[:-1])
                if y < wy1 + (wh // 2):
                    return (curr, p_path, "before", (wx1-ox, wy1-oy, wx1+ww-ox, wy1-oy))
                else:
                    return (curr, p_path, "after", (wx1-ox, wy1+wh-oy, wx1+ww-ox, wy1+wh-oy))
        except (tk.TclError, AttributeError):
            return None
        return None

    def _find_path_at_widget(self, widget):
        """Recursively searches up the widget tree for a path identifier."""
        curr = widget
        while curr:
            # Check for path tags or attributes assigned by various builders
            if hasattr(curr, 'oa_path'): return curr.oa_path
            if hasattr(curr, '_oca_path'): return curr._oca_path
            
            # Fallback: check master
            if hasattr(curr, 'master'):
                curr = curr.master
            else:
                break
        return None

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
        if path is None: return None
        
        full_state = state_manager.get_state()
        if not full_state:
            return path
            
        # If path is already valid, return as is
        if state_manager.get_value_at_path(path) is not None:
            return path

        root_keys = list(full_state.keys())
        # If it's a relative path, try to find which root it belongs to
        for root in root_keys:
            candidate = f"{root}.{path}"
            if state_manager.get_value_at_path(candidate) is not None:
                matrix_log("ui", "gui_builder", "handle_focus_request", f"🖱️🖱️🖱️ [ACTION] FocusManager: Resolved relative path '{path}' to '{candidate}'", "DEBUG")
                return candidate
        
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
