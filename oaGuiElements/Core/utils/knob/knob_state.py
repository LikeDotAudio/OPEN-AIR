# Core/knob_state.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

def create_knob_state(config):
    """Initializes the state for a Rotary Knob."""
    return {
        "start_y": None,
        "start_value": None,
        "dims": {"w": config["width"], "h": config["height"]},
        "_resize_timer": None,
        "secondary_current": config["secondary_color"]
    }
