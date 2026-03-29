# oaComREST/Tests/test_rest.py
# Author: Anthony Peter Kuzub
# Version: 20260326.1200.1
#
# Description: Unit tests for the REST API module.

import pytest
from unittest.mock import MagicMock

# Note: These tests require 'fastapi' and 'httpx' to be installed.
try:
    from fastapi.testclient import TestClient
    from oaComREST.Interface.routes import create_router
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

@pytest.fixture
def mock_managers():
    state_cache = MagicMock()
    protocol_router = MagicMock()
    return state_cache, protocol_router

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="FastAPI or HTTPX not installed")
def test_get_state_success(mock_managers):
    state_cache, protocol_router = mock_managers
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(create_router(state_cache, protocol_router))
    test_client = TestClient(app)
    
    state_cache.get_cached_value.return_value = 42
    
    response = test_client.get("/api/v1/state/test/topic")
    
    assert response.status_code == 200
    assert response.json() == {"topic": "OPEN-AIR/test/topic", "val": 42}
    state_cache.get_cached_value.assert_called_with("OPEN-AIR/test/topic")

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="FastAPI or HTTPX not installed")
def test_post_state_success(mock_managers):
    state_cache, protocol_router = mock_managers
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(create_router(state_cache, protocol_router))
    test_client = TestClient(app)
    
    payload = {"val": 100, "meta": {"unit": "pct"}}
    response = test_client.post("/api/v1/state/test/topic", json=payload)
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    protocol_router.ingest.assert_called_with(
        transport_source="REST",
        topic="OPEN-AIR/test/topic",
        value=100,
        metadata={"unit": "pct"}
    )
