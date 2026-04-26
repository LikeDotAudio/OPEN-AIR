# Core/wink_events.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose




def bind_wink_events(canvas, state, config, value_var, draw_visuals_callback, broadcast_callback):
    """Binds all input events to the Wink Button."""

    def on_press(event):
        alt_pressed = (event.state & 0x0008) != 0
        state["last_click_was_alt"] = alt_pressed

        # ⚡ INTERACTION LOCK
        frame = canvas.master
        if hasattr(frame, "is_locked"):
            frame.is_locked = True

        if alt_pressed:
            state["is_locked"] = not state["is_locked"]
            if state["is_locked"]:
                state["is_latched"] = value_var.get()
            broadcast_callback(state["is_locked"])
            draw_visuals_callback()
            return

        if state["is_locked"]:
            return

        state["is_pressed"] = True
        value_var.set(True)

    def on_release(event):
        if state.get("last_click_was_alt"):
            state["last_click_was_alt"] = False
            # ⚡ INTERACTION LOCK: Release
            frame = canvas.master
            if hasattr(frame, "is_locked"): frame.is_locked = False
            return

        if state["is_locked"]:
            # ⚡ INTERACTION LOCK: Release
            frame = canvas.master
            if hasattr(frame, "is_locked"): frame.is_locked = False
            return

        state["is_pressed"] = False

        if config["is_latching"]:
            state["is_latched"] = not state["is_latched"]
            value_var.set(state["is_latched"])
        else:
            value_var.set(False)

        # ⚡ INTERACTION LOCK: Release
        frame = canvas.master
        if hasattr(frame, "is_locked"):
            frame.is_locked = False

    def on_enter(event):
        state["is_hovering"] = True
        draw_visuals_callback()

    def on_leave(event):
        state["is_hovering"] = False
        draw_visuals_callback()

    def on_resize(event):
        if state["_resize_timer"]:
            canvas.after_cancel(state["_resize_timer"])

        w = canvas.winfo_width()
        h = canvas.winfo_height()
        state["_resize_timer"] = canvas.after(100, lambda: perform_resize(w, h))

    def perform_resize(w, h):
        state["_resize_timer"] = None
        if w > 1 and h > 1:
            if w != state["dims"]["w"] or h != state["dims"]["h"]:
                state["dims"]["w"] = w
                state["dims"]["h"] = h
                draw_visuals_callback()

    canvas.bind("<Button-1>", on_press)
    canvas.bind("<ButtonRelease-1>", on_release)
    canvas.bind("<Enter>", on_enter)
    canvas.bind("<Leave>", on_leave)
    canvas.bind("<Configure>", on_resize)
