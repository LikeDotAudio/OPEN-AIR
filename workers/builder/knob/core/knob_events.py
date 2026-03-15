import tkinter as tk
import sys

def bind_knob_events(canvas, frame, state, config, knob_value_var, draw_visuals_callback, broadcast_callback):
    """Binds all input events to the Rotary Knob."""
    
    def on_knob_press(event):
        state["start_y"] = event.y
        state["start_value"] = knob_value_var.get()
        # ⚡ INTERACTION LOCK
        if hasattr(frame, "is_locked"):
            frame.is_locked = True

    def on_knob_drag(event):
        if state["start_y"] is None: return
        dy = state["start_y"] - event.y
        
        min_val, max_val = config["min"], config["max"]
        base_sensitivity = (max_val - min_val) / 200.0
        if config["fine_pitch"]:
            base_sensitivity /= 10.0
        
        if (event.state & 0x000C) == 0x000C: 
            base_sensitivity /= 2.0

        delta = dy * base_sensitivity
        raw_new_val = state["start_value"] + delta

        if config["infinity"]:
             range_span = max_val - min_val
             new_val = min_val + ((raw_new_val - min_val) % range_span)
        else:
            new_val = max(min_val, min(max_val, raw_new_val))

        if knob_value_var.get() != new_val:
            knob_value_var.set(new_val)
            broadcast_callback()

    def on_knob_release(event):
        # ⚡ RELEASE SEQUENCE: Fire final broadcast before unlocking
        broadcast_callback()
        
        state["start_y"] = None
        state["start_value"] = None
        # ⚡ INTERACTION LOCK: Release
        if hasattr(frame, "is_locked"):
            frame.is_locked = False

    def on_mousewheel(event):
        current_val = knob_value_var.get()
        val_range = config["max"] - config["min"]
        step = val_range * 0.05
        delta = 0
        if sys.platform == "linux":
            delta = 1 if event.num == 4 else -1
        else:
            delta = 1 if event.delta > 0 else -1
        new_val = max(config["min"], min(config["max"], current_val + (delta * step)))
        knob_value_var.set(new_val)
        broadcast_callback()

    def on_enter(event):
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        canvas.bind_all("<Button-4>", on_mousewheel)
        canvas.bind_all("<Button-5>", on_mousewheel)
        state["secondary_current"] = "#999999"
        draw_visuals_callback()

    def on_leave(event):
        canvas.unbind_all("<MouseWheel>")
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")
        state["secondary_current"] = config["secondary_color"]
        draw_visuals_callback()

    def on_resize(event):
        if state["_resize_timer"]:
            canvas.after_cancel(state["_resize_timer"])
        w, h = canvas.winfo_width(), canvas.winfo_height()
        state["_resize_timer"] = canvas.after(100, lambda: perform_resize(w, h))

    def perform_resize(w, h):
        state["_resize_timer"] = None
        if w > 1 and h > 1:
            if w != state["dims"]["w"] or h != state["dims"]["h"]:
                state["dims"]["w"], state["dims"]["h"] = w, h
                draw_visuals_callback()

    canvas.bind("<Configure>", on_resize)
    canvas.bind("<Enter>", on_enter)
    canvas.bind("<Leave>", on_leave)
    canvas.bind("<Button-1>", on_knob_press)
    canvas.bind("<B1-Motion>", on_knob_drag)
    canvas.bind("<ButtonRelease-1>", on_knob_release)
    canvas.bind("<Button-2>", frame._jump_to_reff_point)
    canvas.bind("<Control-Button-1>", frame._jump_to_reff_point)
    canvas.bind("<Alt-Button-1>", frame._open_manual_entry)
