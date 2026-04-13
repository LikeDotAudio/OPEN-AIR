# oaComProtocols.oaComREST/Tests/test_rest.py
# Author: Anthony Peter Kuzub
# Version: 20260410.1000.1
#
# Description: Unit tests for RESTManager ensuring Hub-and-Spoke integrity, 
# anti-feedback, and standardized standalone behavior.

import pytest
import unittest
from unittest.mock import MagicMock, patch

# Note: These tests require 'fastapi' and 'httpx' to be installed.
try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from oaComProtocols.oaComREST.Interface.routes import create_router
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

@pytest.fixture
def api_client():
    """BUILD: Initialize mock environment and FastAPI client."""
    mock_state_cache = MagicMock()
    mock_router = MagicMock()
    
    app = FastAPI()
    app.include_router(create_router(mock_state_cache, mock_router))
    client = TestClient(app)
    
    return client, mock_state_cache, mock_router

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="FastAPI or HTTPX not installed")
class TestRESTProtocol:
    """
    Architectural Integrity Tests for REST Protocol Spoke.
    Follows BUILD -> OPERATE -> CHECK pattern.
    """

    def test_hub_ingest_via_post(self, api_client):
        """OPERATE: Simulate incoming REST data (Spoke -> Hub)."""
        client, mock_state, mock_router = api_client
        test_topic = "Audio/Fader/1"
        test_val = 0.5
        
        # OPERATE
        response = client.post(f"/{test_topic}", json={"value": test_val})
        
        # CHECK: Data normalized and sent to Hub (ProtocolRouter)
        assert response.status_code == 200
        mock_router.ingest.assert_called_with(
            transport_source="REST",
            topic=test_topic,
            value=test_val
        )

    def test_spoke_read_via_get(self, api_client):
        """OPERATE: Simulate Spoke reading from Hub."""
        client, mock_state, mock_router = api_client
        test_topic = "Audio/Mute"
        mock_state.get_cached_value.return_value = True
        
        # OPERATE
        response = client.get(f"/{test_topic}")
        
        # CHECK: Correct value returned from Hub state
        assert response.status_code == 200
        assert response.json()["value"] is True

    def test_dynamic_system_status(self, api_client):
        """CHECK: Verify the dynamic system status endpoint works without hardcoded lists."""
        client, mock_state, mock_router = api_client
        
        # Mock ProtocolRouter to return a specific list
        with patch("oaComBroker.Core.protocol_router.manager.ProtocolRouter.get_instance") as mock_get:
            mock_inst = MagicMock()
            mock_inst.protocols = ["MQTT", "REST", "CUSTOM"]
            mock_get.return_value = mock_inst
            
            # OPERATE
            response = client.get("/api/v1/system/status")
            
            # CHECK
            assert response.status_code == 200
            data = response.json()
            assert "CUSTOM" in data["active_protocols"]
            assert data["status"] == "operational"

if __name__ == "__main__":
    pytest.main([__file__])
