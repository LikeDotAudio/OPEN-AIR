# layout_overlays/sizing.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk

from ...Core.state import state_manager


def apply_design_overlay(layout, widget, path, is_focused, design_elements):
    """Handles sizing handles and resize tooltips."""

    res_diag = tk.Label(widget.master, text="⤡", bg="#FF9900", fg="black", font=("Arial", 8), cursor="sizing")
    res_horiz = tk.Label(widget.master, text="↔", bg="#FF9900", fg="black", font=("Arial", 8), cursor="sb_h_double_arrow")
    res_vert = tk.Label(widget.master, text="↕", bg="#FF9900", fg="black", font=("Arial", 8), cursor="sb_v_double_arrow")
    pad_x_handle = tk.Label(widget.master, text="PX", bg="#33A1FD", fg="white", font=("Arial", 6, "bold"), cursor="sb_h_double_arrow")
    pad_y_handle = tk.Label(widget.master, text="PY", bg="#33A1FD", fg="white", font=("Arial", 6, "bold"), cursor="sb_v_double_arrow")
    breath_handle = tk.Label(widget.master, text="BR", bg="#33A1FD", fg="white", font=("Arial", 6, "bold"), cursor="fleur")

    handles = [res_diag, res_horiz, res_vert, pad_x_handle, pad_y_handle, breath_handle]
    for h in handles:
        h._is_design_overlay = True
        design_elements.append(h)

    def _show_resize_tooltip(event, x_root, y_root, val1, val2, label1="W", label2="H"):
        toplevel = layout.winfo_toplevel()
        if not hasattr(layout, 'resize_tooltip') or not layout.resize_tooltip or not layout.resize_tooltip.winfo_exists():
            layout.resize_tooltip = tk.Label(toplevel, bg="#FF9900", fg="black",
                                          font=("Arial", 8, "bold"), padx=5, pady=2, relief="solid", bd=1)
            layout.resize_tooltip._is_design_overlay = True

        layout.resize_tooltip.config(text=f"{label1}: {int(val1)} {label2}: {int(val2)}" if label2 else f"{label1}: {int(val1)}")
        root_x, root_y = toplevel.winfo_rootx(), toplevel.winfo_rooty()
        layout.resize_tooltip.place(x=x_root - root_x + 25, y=y_root - root_y + 25)

    def _show_ghost_box(w, h):
        if not hasattr(layout, 'ghost_box') or not layout.ghost_box or not layout.ghost_box.winfo_exists():
            # Use master background for ghost box to avoid color errors
            master_bg = "#2b2b2b"
            try: master_bg = widget.master.cget("bg")
            except: pass

            layout.ghost_box = tk.Frame(widget.master, bg=master_bg, highlightbackground="#FF9900", highlightthickness=2)
            layout.ghost_box._is_design_overlay = True

        layout.ghost_box.place(x=widget.winfo_x(), y=widget.winfo_y(), width=w, height=h)
        layout.ghost_box.lift()

    def _on_drag(event, mode):
        if not widget.winfo_exists(): return
        dx, dy = event.x_root - widget.winfo_rootx(), event.y_root - widget.winfo_rooty()
        if mode == "padx":
            pv = max(0, int(dx // 5))
            _show_resize_tooltip(event, event.x_root, event.y_root, pv, None, label1="PAD-X", label2=None)
            # Visualize the padding being added to the right
            current_w, current_h = widget.winfo_width(), widget.winfo_height()
            _show_ghost_box(current_w + pv, current_h) # Show widget + padding width
        elif mode == "pady":
            pv = max(0, int(dy // 5))
            _show_resize_tooltip(event, event.x_root, event.y_root, pv, None, label1="PAD-Y", label2=None)
            # Visualize the padding being added below
            current_w, current_h = widget.winfo_width(), widget.winfo_height()
            _show_ghost_box(current_w, current_h + pv) # Show widget + padding height
        elif mode == "breath":
            bpv = max(0, int(dx // 5)) # Breath Padding Value
            _show_resize_tooltip(event, event.x_root, event.y_root, bpv, None, label1="BREATH", label2=None)
            current_w, current_h = widget.winfo_width(), widget.winfo_height()
            _show_ghost_box(current_w + bpv * 2, current_h + bpv * 2) # Visualize breath padding around the widget
        else:
            nw, nh = max(20, dx), max(20, dy)
            if mode == "horiz": nh = widget.winfo_height()
            if mode == "vert": nw = widget.winfo_width()
            _show_resize_tooltip(event, event.x_root, event.y_root, nw, nh)
            _show_ghost_box(nw, nh)

    def _on_release(event, mode):
        try:
            if hasattr(layout, 'resize_tooltip') and layout.resize_tooltip and layout.resize_tooltip.winfo_exists():
                layout.resize_tooltip.place_forget()
            if hasattr(layout, 'ghost_box') and layout.ghost_box and layout.ghost_box.winfo_exists():
                layout.ghost_box.place_forget()
        except tk.TclError: pass

        if not widget.winfo_exists(): return
        dx, dy = event.x_root - widget.winfo_rootx(), event.y_root - widget.winfo_rooty()

        if mode == "padx":
            state_manager.update_state(max(0, int(dx // 5)), path=f"{path}.layout.padx", source=layout)
        elif mode == "pady":
            state_manager.update_state(max(0, int(dy // 5)), path=f"{path}.layout.pady", source=layout)
        elif mode == "breath":
            state_manager.update_state(max(0, int(dx // 5)), path=f"{path}.layout.breath_padding", source=layout)
        else:
            nw, nh = max(20, dx), max(20, dy)
            updates = []
            if "_config" in path:
                if mode in ["diag", "horiz"]: updates.append((int(nw), f"{path}.width"))
                if mode in ["diag", "vert"]: updates.append((int(nh), f"{path}.height"))
            else:
                if mode in ["diag", "horiz"]: updates.append((int(nw), f"{path}.geometry.width"))
                if mode in ["diag", "vert"]: updates.append((int(nh), f"{path}.geometry.height"))
            state_manager.batch_update(updates, source=layout)

    # Bind Events
    for m, h in [("diag", res_diag), ("horiz", res_horiz), ("vert", res_vert), ("padx", pad_x_handle), ("pady", pad_y_handle), ("breath", breath_handle)]:
        h.bind("<Button-1>", lambda e, mode=m: _on_drag(e, mode))
        h.bind("<B1-Motion>", lambda e, mode=m: _on_drag(e, mode))
        h.bind("<ButtonRelease-1>", lambda e, mode=m: _on_release(e, mode))

    def sync(x, y, w, h):
        if layout.show_sizing.get() and w >= 40 and h >= 40:
            res_diag.place(x=x + w - 20, y=y + h - 20, width=20, height=20)
            res_horiz.place(x=x + w - 20, y=y + (h//2) - 10, width=20, height=20)
            res_vert.place(x=x + (w//2) - 10, y=y + h - 20, width=20, height=20)
            pad_x_handle.place(x=x + w - 40, y=y, width=18, height=12)
            pad_y_handle.place(x=x + w - 20, y=y, width=18, height=12)
            breath_handle.place(x=x + w - 60, y=y, width=18, height=12) # Place breath handle
        else:
            for hdl in handles: hdl.place_forget()

    return sync
