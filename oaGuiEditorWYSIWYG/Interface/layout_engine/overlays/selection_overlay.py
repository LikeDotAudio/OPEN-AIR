# oaGuiEditorWYSIWYG/Interface/layout_engine/overlays/selection_overlay.py
# Author: Anthony Peter Kuzub
# Version: 20260416.01.0
#
# Description: Modular Selection Highlight and Move Handle.

import tkinter as tk
from .base_overlay import BaseOverlay
from ....Core.state import state_manager

class SelectionOverlay(BaseOverlay):
    """Handles selection markers and the primary move/focus handle."""

    def __init__(self, workspace, widget, path, is_focused):
        super().__init__(workspace, widget, path, is_focused)
        self._dragging = False
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._drop_target = None # (container_widget, container_path, index)
        self._build_ui()

    def _build_ui(self):
        # 1. 4-Frame Construction for yellow selection highlight
        self.highlight_frames = []
        if self.is_focused:
            for _ in range(4):
                f = self.create_element(tk.Frame, bg="yellow", bd=0, highlightthickness=0)
                self.highlight_frames.append(f)

        # 2. RESIZE HANDLES (Bottom-Right) - Visual only
        self.resize_marker = None
        if self.is_focused:
            self.resize_marker = self.create_element(tk.Frame, bg="#00FF00", width=10, height=10, cursor="bottom_right_corner")

        # 3. SELECTION HANDLE (🎯)
        master_bg = "#2b2b2b"
        try: master_bg = self.widget.master.cget("bg")
        except: pass

        bg_color = "#33A1FD" if self.is_focused else master_bg
        self.move_handle = self.create_element(tk.Label, text="🎯", bg=bg_color, fg="white", font=("Arial", 8), cursor="fleur")
        
        # 4. EVENT BINDINGS
        self.move_handle.bind("<Button-1>", self._on_click_start)
        self.move_handle.bind("<B1-Motion>", self._on_drag_motion)
        self.move_handle.bind("<ButtonRelease-1>", self._on_drag_stop)

        self.widget.bind("<Button-1>", self._on_click_start, add="+")
        
        self.move_handle.bind("<Enter>", lambda e: self.move_handle.config(bg="#FF00FF"))
        self.move_handle.bind("<Leave>", lambda e: self.move_handle.config(bg="#33A1FD" if self.is_focused else master_bg))

    def _on_click_start(self, event):
        self._dragging = False
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        
        if self.is_focused:
            new_path = None
        else:
            # ⚡ ROBUST PATH RESOLUTION:
            # If the path doesn't exist in the state (e.g. sub-component of a composite),
            # walk up until we find a valid selectable element.
            new_path = self.path
            while new_path and state_manager.get_value_at_path(new_path) is None:
                if '.' not in new_path: 
                    new_path = None; break
                new_path = ".".join(new_path.split(".")[:-1])

        self.workspace._on_widget_focused(new_path)
        return "break"

    def _on_drag_motion(self, event):
        if not self._dragging:
            if abs(event.x_root - self._drag_start_x) > 5 or abs(event.y_root - self._drag_start_y) > 5:
                self._dragging = True
                self.workspace.ghost_overlay.place(x=0, y=0, relwidth=1, relheight=1)
        
        if self._dragging:
            # 1. Update Ghost Rect
            ox = self.workspace.render_area.winfo_rootx()
            oy = self.workspace.render_area.winfo_rooty()
            x = event.x_root - ox
            y = event.y_root - oy
            w = self.widget.winfo_width()
            h = self.widget.winfo_height()
            self.workspace.ghost_overlay.draw_ghost(x - 10, y - 10, w, h)

            # 2. Find Drop Target
            target = self._find_drop_target(event.x_root, event.y_root)
            if target:
                self._drop_target = target
                # Draw green insertion line
                tw, tp, tmode, tcoords = target
                self.workspace.ghost_overlay.draw_insertion_line(*tcoords)
            else:
                self._drop_target = None
                self.workspace.ghost_overlay.clear_insertion()

        return "break"

    def _on_drag_stop(self, event):
        if self._dragging:
            self.workspace.ghost_overlay.clear()
            self.workspace.ghost_overlay.place_forget()
            
            if self._drop_target:
                tw, tp, tmode, tcoords = self._drop_target
                # ⚡ MOVE LOGIC
                if not tp.startswith(self.path):
                    # Resolve target container path (append .fields if Block)
                    final_target_parent = tp
                    t_val = state_manager.get_value_at_path(tp)
                    if isinstance(t_val, dict) and "Block" in t_val.get("type", ""):
                        if "fields" not in tp: final_target_parent = f"{tp}.fields"
                    
                    state_manager.move_element(self.path, final_target_parent, source=self.workspace)
            
        self._dragging = False
        self._drop_target = None
        return "break"

    def _find_drop_target(self, root_x, root_y):
        """Recursively finds the best drop container and insertion coordinate."""
        top = self.widget.winfo_toplevel()
        target_widget = top.winfo_containing(root_x, root_y)
        if not target_widget: return None

        # Resolve the widget under the mouse to its _oca_path
        curr = target_widget
        path = None
        while curr:
            if hasattr(curr, '_oca_path'):
                path = curr._oca_path
                break
            curr = curr.master
        
        if not path: return None
        
        val = state_manager.get_value_at_path(path)
        if not isinstance(val, dict):
             # Leaf -> Move to parent container
             path = ".".join(path.split(".")[:-1])
             val = state_manager.get_value_at_path(path)
             # Update curr to represent the container
             temp = curr
             while temp:
                 if getattr(temp, '_oca_path', None) == path:
                     curr = temp; break
                 temp = temp.master

        if not isinstance(val, dict): return None

        # Check if we are over a container (Block/Bin)
        w_type = val.get("type", "")
        if w_type in ["OcaBlock", "OcaBin", "OcaArray"]:
            # Container -> Find which child we are near for insertion, or append
            # For now, simple "append to container" visual
            ox = self.workspace.render_area.winfo_rootx()
            oy = self.workspace.render_area.winfo_rooty()
            wx1 = curr.winfo_rootx(); wy1 = curr.winfo_rooty()
            ww = curr.winfo_width(); wh = curr.winfo_height()
            
            # Draw line near the bottom to indicate "append"
            return (curr, path, "append", (wx1-ox, wy1+wh-5-oy, wx1+ww-ox, wy1+wh-5-oy))
        else:
            # Over a non-container widget -> Find its container and insert relative
            container_path = ".".join(path.split(".")[:-1])
            container_val = state_manager.get_value_at_path(container_path)
            
            if isinstance(container_val, dict) and container_val.get("type") in ["OcaBlock", "OcaBin", "OcaArray"]:
                cx1 = curr.winfo_rootx(); cy1 = curr.winfo_rooty()
                cw = curr.winfo_width(); ch = curr.winfo_height()
                ox = self.workspace.render_area.winfo_rootx(); oy = self.workspace.render_area.winfo_rooty()

                if root_y < cy1 + (ch // 2):
                    return (curr.master, container_path, "before", (cx1-ox, cy1-oy, cx1+cw-ox, cy1-oy))
                else:
                    return (curr.master, container_path, "after", (cx1-ox, cy1+ch-oy, cx1+cw-ox, cy1+ch-oy))

        return None


    def sync(self, x, y, w, h):
        if self.highlight_frames:
            th = 2 
            self.highlight_frames[0].place(x=x-th, y=y-th, width=w+(th*2), height=th)
            self.highlight_frames[1].place(x=x-th, y=y+h, width=w+(th*2), height=th)
            self.highlight_frames[2].place(x=x-th, y=y, width=th, height=h)
            self.highlight_frames[3].place(x=x+w, y=y, width=th, height=h)
            
        self.move_handle.place(x=x, y=y, width=20, height=20)
        if self.resize_marker:
            self.resize_marker.place(x=x+w-5, y=y+h-5, width=10, height=10)

