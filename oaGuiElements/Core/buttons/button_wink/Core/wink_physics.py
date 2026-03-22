# Core/wink_physics.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

def update_physics(canvas, state, config, draw_visuals_callback):
    """Smoothly interpolates current position to target position."""
    current = state["current_open"]
    target = state["target_open"]
    
    open_inc = config["open_inc"]
    close_inc = config["close_inc"]
    
    moved = False
    if current < target:
        state["current_open"] += open_inc
        if state["current_open"] > target:
            state["current_open"] = target
        moved = True
    elif current > target:
        state["current_open"] -= close_inc
        if state["current_open"] < target:
            state["current_open"] = target
        moved = True
    
    if moved:
        draw_visuals_callback()
    
    # ⚡ TERMINATION SAFETY: Use microscopic epsilon for floating point comparison.
    # Also check moved flag to ensure we don't loop if no delta was applied.
    is_at_target = abs(state["current_open"] - target) < 0.001
    
    if (moved or state["is_pressed"]) and not is_at_target:
        canvas.after(16, lambda: update_physics(canvas, state, config, 
                                                draw_visuals_callback))
    else:
        state["animating"] = False
        # Ensure terminal value is exact
        state["current_open"] = target
        # Final redraw to snap to perfect position
        draw_visuals_callback()

def blink_loop(canvas, state, config, value_var, draw_visuals_callback):
    """Toggles the shutter state periodically if blinking is active."""
    # ⚡ TERMINATION SAFETY: Stop loop if blink becomes disabled or value turns off.
    if not state.get("is_blinking_active", False) or not value_var.get():
        state["is_blinking_active"] = False
        return

    state["blink_open"] = not state["blink_open"]
    state["target_open"] = 1.0 if state["blink_open"] else 0.0
    
    if not state.get("animating", False):
        state["animating"] = True
        update_physics(canvas, state, config, draw_visuals_callback)

    # ⚡ OVERLAP PROTECTION: Cancel existing blink timer if present (handled by logic flow)
    # The canvas.after approach means only one chain lives per button.
    canvas.after(config["blink_interval"], lambda: blink_loop(canvas, state, 
                                                             config, value_var, 
                                                             draw_visuals_callback))
