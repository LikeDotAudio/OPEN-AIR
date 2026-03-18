# workers/logic/manifest/builder.py
#
# Robust Builder for the Splinker "Shipping Manifest" (JSON Payload).
# Ensures strict type enforcement and immutable core attributes.

import time
import uuid
from typing import Any, Dict
from oaConfiguration.config_reader import Config

app_constants = Config.get_instance()

def create_manifest(
    value: Any, 
    topic: str, 
    source: str = "EXTERNAL", 
    metadata: Dict = None
) -> Dict:
    """
    Constructs a standardized Splinker JSON manifest.
    
    Inputs:
        value (Any): The control value (floated internally).
        topic (str): The target_parameter/topic.
        source (str): The logical origin (e.g., GUI, MIDI).
        metadata (Dict, optional): Extra flags (LOCKED, SETTLED).
        
    Outputs:
        Dict: The formatted manifest.
    """
    now = time.time()
    
    # ⚡ MODULAR LOGIC: Resolve origin_source based on system state
    if source == "GUI":
        origin = app_constants.FULL_INSTANCE_ID
    else:
        origin = source

    payload = {
        # ⚡ THE IMMUTABLE MANIFEST
        "origin_source": origin,
        "msg_guid": str(uuid.uuid4()),
        "timestamp": now,
        "target_parameter": topic,
        "value": float(value) if isinstance(value, (int, float)) else value,
        "is_locked": metadata.get("LOCKED", False) if metadata else False,
        "is_settled": metadata.get("SETTLED", True) if metadata else True,
        
        # Backward Compatibility Layer
        "val": value, 
        "source": source, 
        "ts": now, 
        "GUID": app_constants.INSTANCE_GUID,
        "partition": app_constants.PARTITION_ID,
        "full_id": app_constants.FULL_INSTANCE_ID
    }
    
    if metadata:
        payload.update(metadata)
        
    return payload
