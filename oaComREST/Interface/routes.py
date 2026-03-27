# oaComREST/Interface/routes.py
# Author: Anthony Peter Kuzub
# Version: 20260326.1200.1
#
# Description: API endpoint definitions for FastAPI.

try:
    from fastapi import APIRouter, HTTPException, Path, Body
except ImportError:
    pass

from typing import Any, Dict
from ..Constants.rest_constants import LOCAL_DEBUG
from loguru import logger

def create_router(state_cache_manager, protocol_router):
    """
    Creates and configures the FastAPI router with system dependencies.
    """
    router = APIRouter(prefix="/api/v1")

    @router.get("/state/{topic_path:path}")
    async def get_state(topic_path: str = Path(..., description="The MQTT-style topic path")):
        """Fetches the current state for a given topic from the cache."""
        # Normalize the topic to ensure it starts with the system root.
        full_topic = topic_path
        if not full_topic.startswith("OPEN-AIR"):
            full_topic = f"OPEN-AIR/{topic_path}"
            
        value = state_cache_manager.get_cached_value(full_topic)
        if value is None:
            raise HTTPException(status_code=404, detail=f"Topic '{full_topic}' not found in cache.")
        
        return {"topic": full_topic, "val": value}

    @router.post("/state/{topic_path:path}")
    async def set_state(
        topic_path: str = Path(..., description="The MQTT-style topic path"),
        payload: Dict[str, Any] = Body(..., description="The new state value and optional metadata")
    ):
        """Injects a new state value into the protocol router."""
        full_topic = topic_path
        if not full_topic.startswith("OPEN-AIR"):
            full_topic = f"OPEN-AIR/{topic_path}"
            
        val = payload.get("val")
        if val is None and "val" not in payload:
             # If the payload is just a single value (not a dict with 'val'), treat the whole thing as 'val'
             val = payload
             
        # Log the REST command.
        if LOCAL_DEBUG:
            logger.debug(f"📡📥📥 [REST] POST to {full_topic}: {val}")
            
        # Pushes to ProtocolRouter for propagation.
        protocol_router.ingest(
            transport_source="REST",
            topic=full_topic,
            value=val,
            metadata=payload.get("meta")
        )
        
        return {"status": "success", "topic": full_topic, "val": val}

    @router.get("/system/status")
    async def get_system_status():
        """Returns high-level system health metrics."""
        return {
            "status": "operational",
            "partition": "CORE",
            "active_protocols": ["MQTT", "REST"] # Simplified for now
        }

    return router
