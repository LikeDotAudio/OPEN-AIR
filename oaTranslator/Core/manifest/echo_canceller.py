# manifest/echo_canceller.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Logic to prevent infinite feedback loops via Echo Cancellation.

from typing import Dict
from oaConfigurationManager.FileReaders.config_reader import Config

app_constants = Config.get_instance()

def is_echo(payload: Dict) -> bool:
    """
    Identifies if a payload is an echo of a local action.
    
    Checks:
        1. origin_source matches local FULL_INSTANCE_ID.
        2. full_id (legacy) matches local FULL_INSTANCE_ID.
    """
    if not isinstance(payload, dict):
        return False
        
    local_id = app_constants.FULL_INSTANCE_ID
    
    # ⚡ SHIELD CHECK: Is this the Ghost of our own Fader?
    if payload.get("origin_source") == local_id:
        return True
    
    if payload.get("full_id") == local_id:
        return True
        
    return False
