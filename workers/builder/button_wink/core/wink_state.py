import tkinter as tk

def create_wink_state(config, initial_value):
    """Initializes the state for a Wink Button."""
    return {
        "target_open": 1.0 if initial_value else 0.0,
        "current_open": 1.0 if initial_value else 0.0,
        "is_pressed": False,
        "is_latched": initial_value,
        "is_locked": config.get("is_locked_init", False),
        "is_hovering": False,
        "shutter_ids": [],
        "animating": False,
        "blink_open": True, 
        "is_blinking_active": False,
        "last_click_was_alt": False,
        "dims": {"w": config.get("width"), "h": config.get("height")},
        "_resize_timer": None
    }
