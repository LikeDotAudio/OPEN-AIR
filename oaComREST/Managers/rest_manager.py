# oaComREST/Managers/rest_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260326.1200.1
#
# Description: Orchestrator for the REST API service.

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from loguru import logger

from ..Constants.rest_constants import LOCAL_DEBUG, REST_HOST, REST_PORT, REST_CORS_ORIGINS
from ..Workers.uvicorn_worker import UvicornWorker
from ..Interface.routes import create_router

class RESTManager:
    """
    Manages the lifecycle of the FastAPI REST service.
    """
    def __init__(self, state_cache_manager, protocol_router):
        """
        Initializes the REST manager.
        
        Inputs:
            state_cache_manager (StateRegistry): Dependency for state retrieval.
            protocol_router (ProtocolRouter): Dependency for state injection.
        """
        self.state_cache = state_cache_manager
        self.router = protocol_router
        self.app = None
        self.worker = None

        if not FASTAPI_AVAILABLE:
            logger.warning("⚠️ [REST] FastAPI or dependencies not found. REST API will be disabled.")
            return
        
        # 1. Initialize FastAPI
        self.app = FastAPI(
            title="OPEN-AIR REST API",
            description="High-performance interface for system state and control.",
            version="1.0.0"
        )
        
        # 2. Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=REST_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 3. Inject Routes
        api_router = create_router(self.state_cache, self.router)
        self.app.include_router(api_router)
        
        # 4. Initialize Worker
        self.worker = UvicornWorker(self.app, host=REST_HOST, port=REST_PORT)

    def start(self):
        """Launches the REST API background thread."""
        if self.worker and not self.worker.is_alive():
            if LOCAL_DEBUG:
                logger.info(f"🌐 [REST] Launching API Service on {REST_HOST}:{REST_PORT}...")
            self.worker.start()
            return True
        return False

    def stop(self):
        """Shuts down the REST API service."""
        if self.worker and self.worker.is_alive():
            if LOCAL_DEBUG:
                logger.info("🌐 [REST] Shutting down API Service...")
            self.worker.stop()
            self.worker.join(timeout=2.0)
            return True
        return False
