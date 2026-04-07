# manifest/ghost_lock.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Manages the "Ghost Touch Lock" logic for interaction priority.

from typing import Dict, Any

def is_ghost_touch_locked(payload: Dict, widget_instance: Any = None) -> bool:
    """
    Checks if a network update should be blocked due to human interaction.
    
    Checks:
        1. If the widget_instance.is_locked == True, the human is in control.
        2. If is_settled == False (the sender is in motion), it yields.
    """
    if not isinstance(payload, dict):
        return False
        
    # ⚡ HUMAN PRIORITY: If a human is touching the widget, the Ghost is locked out.
    if widget_instance and getattr(widget_instance, "is_locked", False):
        # ⚡ SETTLE CHECK: Only yield if the sender hasn't settled their movement.
        if not payload.get("is_settled", True):
            return True
            
    return False
