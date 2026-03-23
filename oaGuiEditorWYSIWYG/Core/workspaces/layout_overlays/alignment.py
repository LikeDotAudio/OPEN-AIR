# layout_overlays/alignment.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from ...state import state_manager

def apply(layout, widget, path, is_focused, design_elements):
    """Handles LRCTB alignment indicators."""
    
    alignment_handles = {}
    for d in ["L", "R", "C", "T", "B"]:
        lbl = tk.Label(widget.master, text=d, bg="#666666", fg="white", font=("Arial", 5, "bold"), cursor="hand2")
        lbl._is_design_overlay = True
        alignment_handles[d] = lbl
        design_elements.append(lbl)

        # Functional mapping to 'sticky'
        def _toggle(event, mode=d):
            full_path = f"{path}.layout.sticky"
            current = str(state_manager.get_value_at_path(full_path) or "").lower()
            
            new_sticky = current
            if mode == "L": 
                if "w" in new_sticky: new_sticky = new_sticky.replace("w", "")
                else: new_sticky += "w"
            elif mode == "R":
                if "e" in new_sticky: new_sticky = new_sticky.replace("e", "")
                else: new_sticky += "e"
            elif mode == "T":
                if "n" in new_sticky: new_sticky = new_sticky.replace("n", "")
                else: new_sticky += "n"
            elif mode == "B":
                if "s" in new_sticky: new_sticky = new_sticky.replace("s", "")
                else: new_sticky += "s"
            elif mode == "C":
                new_sticky = ""
            
            new_sticky = "".join(sorted(list(set(new_sticky))))
            state_manager.update_state(new_sticky.upper(), path=full_path, source=layout)

        lbl.bind("<Button-1>", _toggle)

    def sync(x, y, w, h):
        if layout.show_alignment.get():
            val = (state_manager.get_value_at_path(f"{path}.layout.sticky") or "").lower()
            
            # Update colors based on state
            alignment_handles["L"].config(bg="#33A1FD" if "w" in val else "#666666")
            alignment_handles["R"].config(bg="#33A1FD" if "e" in val else "#666666")
            alignment_handles["T"].config(bg="#33A1FD" if "n" in val else "#666666")
            alignment_handles["B"].config(bg="#33A1FD" if "s" in val else "#666666")
            alignment_handles["C"].config(bg="#33A1FD" if not val else "#666666")

            alignment_handles["L"].place(x=x, y=y + h//2 - 5, width=10, height=10)
            alignment_handles["R"].place(x=x + w - 10, y=y + h//2 - 5, width=10, height=10)
            alignment_handles["C"].place(x=x + w//2 - 5, y=y + h//2 - 5, width=10, height=10)
            alignment_handles["T"].place(x=x + w//2 - 5, y=y, width=10, height=10)
            alignment_handles["B"].place(x=x + w//2 - 5, y=y + h - 10, width=10, height=10)
        else:
            for hdl in alignment_handles.values(): hdl.place_forget()

    return sync
