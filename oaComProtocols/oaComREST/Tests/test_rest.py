# oaComProtocols.oaComREST/Tests/test_rest.py
# Author: Anthony Peter Kuzub
# Version: 20260414.1000.1
#
# Description: Unit tests for RESTManager ensuring Hub-and-Spoke integrity, 
# anti-feedback, and standardized standalone behavior.

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

class TestRESTProtocol(unittest.TestCase):
    """
    Architectural Integrity Tests for REST Protocol Spoke.
    Follows BUILD -> OPERATE -> CHECK pattern.
    """

    def setUp(self):
        """BUILD: Initialize mock environment and FastAPI client."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("FastAPI or TestClient not installed")
            
        self.mock_state_cache = MagicMock()
        self.mock_router = MagicMock()
        
        # Setup FastAPI app with our router
        self.app = FastAPI()
        self.app.include_router(create_router(self.mock_state_cache, self.mock_router))
        self.client = TestClient(self.app)

    def test_hub_ingest_via_post(self):
        """OPERATE: Simulate incoming REST data (Spoke -> Hub)."""
        test_topic = "Audio/Fader/1"
        test_val = 0.5
        
        # OPERATE
        response = self.client.post(f"/{test_topic}", json={"value": test_val})
        
        # CHECK: Data normalized and sent to Hub (ProtocolRouter)
        self.assertEqual(response.status_code, 200)
        self.mock_router.ingest.assert_called_with(
            transport_source="REST",
            topic=test_topic,
            value=test_val
        )

    def test_spoke_read_via_get(self):
        """OPERATE: Simulate Spoke reading from Hub."""
        test_topic = "Audio/Mute"
        self.mock_state_cache.get_cached_value.return_value = True
        
        # OPERATE
        response = self.client.get(f"/{test_topic}")
        
        # CHECK: Correct value returned from Hub state
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["value"], True)

    def test_dynamic_system_status(self):
        """CHECK: Verify the dynamic system status endpoint works without hardcoded lists."""
        # Mock ProtocolRouter to return a specific list
        with patch("oaComBroker.Core.protocol_router.manager.ProtocolRouter.get_instance") as mock_get:
            mock_inst = MagicMock()
            mock_inst.protocols = ["MQTT", "REST", "CUSTOM"]
            mock_inst.GUID = "TEST-GUID"
            mock_get.return_value = mock_inst
            
            # OPERATE
            response = self.client.get("/api/v1/system/status")
            
            # CHECK
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("CUSTOM", data["active_protocols"])
            self.assertEqual(data["status"], "operational")

if __name__ == "__main__":
    unittest.main()
