# workers/wysiwyg_editor/workspaces/layout_overlays/sticky.py
import tkinter as tk
from ...core.state_manager import state_manager

def apply(layout, widget, path, is_focused, design_elements):
    """Handles NSEW sticky toggles."""
    
    sticky_handles = {}
    for d in ["n", "s", "e", "w"]:
        lbl = tk.Label(widget.master, text=d.upper(), bg="#444444", fg="white", font=("Arial", 6, "bold"), cursor="hand2")
        lbl._is_design_overlay = True
        sticky_handles[d] = lbl
        design_elements.append(lbl)
        
        # Closure for click
        def _toggle(event, direction=d):
            full_path = f"{path}.layout.sticky"
            current = (state_manager.get_value_at_path(full_path) or "").lower()
            new_sticky = current.replace(direction, "") if direction in current else "".join(sorted(current + direction))
            # ⚡ OPTIMIZATION: source=layout ensures we don't trigger a rebuild counter
            state_manager.update_state(new_sticky.upper(), path=full_path, source=layout)
            
        lbl.bind("<Button-1>", _toggle)

    def sync(x, y, w, h):
        if layout.show_sticky.get():
            val = (state_manager.get_value_at_path(f"{path}.layout.sticky") or "").lower()
            for d, handle in sticky_handles.items():
                handle.config(bg="#00ff00" if d in val else "#444444")
            
            sticky_handles["n"].place(x=x + (w//2) - 50, y=y, width=16, height=12)
            sticky_handles["s"].place(x=x + (w//2) - 50, y=y + h - 12, width=16, height=12)
            sticky_handles["w"].place(x=x, y=y + (h//2) - 50, width=12, height=16)
            sticky_handles["e"].place(x=x + w - 12, y=y + (h//2) - 50, width=12, height=16)
        else:
            for hdl in sticky_handles.values(): hdl.place_forget()

    return sync
