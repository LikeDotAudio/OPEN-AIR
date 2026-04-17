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
        matrix_log("ui", "gui_builder", "drop", f"🎯 [DROP] Component '{name}' dropped at ({x}, {y})", "INFO")
        
        target = self.find_drop_target_at(x, y)
        if not target: return
        
        tw, tp, tmode, tcoords = target
        
        if tp is not None:
            matrix_log("ui", "gui_builder", "drop", f"🎯 [DROP] resolved target path: '{tp}'", "DEBUG")
            
            # Final target resolution (append .fields if Block)
            final_target_parent = tp
            t_val = state_manager.get_value_at_path(tp)
            if isinstance(t_val, dict) and "Block" in t_val.get("type", ""):
                if "fields" not in tp: final_target_parent = f"{tp}.fields"
            
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
            if hasattr(curr, '_oca_path'):
                path = curr._oca_path
                break
            curr = curr.master
            
        if not path:
            # Check if dropped on empty workspace area
            is_child = False; temp = target_widget
            while temp:
                if temp == self.workspace: is_child = True; break
                temp = temp.master
            if is_child:
                full_state = state_manager.get_state()
                path = list(full_state.keys())[0] if full_state else ""
            else:
                return None

        # 2. Resolve target characteristics
        val = state_manager.get_value_at_path(path)
        if not isinstance(val, dict):
            # Leaf -> Move to parent container
            path = ".".join(path.split(".")[:-1])
            val = state_manager.get_value_at_path(path)
            temp = curr
            while temp:
                if getattr(temp, '_oca_path', None) == path:
                    curr = temp; break
                temp = temp.master

        if not isinstance(val, dict): return None

        # 3. Calculate visuals
        ox = self.workspace.render_area.winfo_rootx()
        oy = self.workspace.render_area.winfo_rooty()

        w_type = val.get("type", "")
        if w_type in ["OcaBlock", "OcaBin", "OcaArray"]:
            # Container -> Append visual
            wx1 = curr.winfo_rootx(); wy1 = curr.winfo_rooty()
            ww = curr.winfo_width(); wh = curr.winfo_height()
            return (curr, path, "append", (wx1-ox, wy1+wh-5-oy, wx1+ww-ox, wy1+wh-5-oy))
        else:
            # Widget -> Sibling insertion visual
            container_path = ".".join(path.split(".")[:-1])
            container_val = state_manager.get_value_at_path(container_path)
            if isinstance(container_val, dict) and container_val.get("type") in ["OcaBlock", "OcaBin", "OcaArray"]:
                cx1 = curr.winfo_rootx(); cy1 = curr.winfo_rooty()
                cw = curr.winfo_width(); ch = curr.winfo_height()
                if y < cy1 + (ch // 2):
                    return (curr.master, container_path, "before", (cx1-ox, cy1-oy, cx1+cw-ox, cy1-oy))
                else:
                    return (curr.master, container_path, "after", (cx1-ox, cy1+ch-oy, cx1+cw-ox, cy1+ch-oy))
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
