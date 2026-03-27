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
        self.monitor_callbacks = []

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
        
        # 3. Add Activity Middleware
        @self.app.middleware("http")
        async def activity_log_middleware(request, call_next):
            response = await call_next(request)
            self.notify_activity(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code
            )
            return response

        # 4. Inject Routes
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

    def is_running(self):
        """Checks if the REST API service is currently active."""
        return self.worker is not None and self.worker.is_alive()

    def get_status(self):
        """Returns a comprehensive status report for the REST service."""
        status = {
            "running": self.is_running(),
            "host": REST_HOST,
            "port": REST_PORT,
            "url": f"http://{REST_HOST}:{REST_PORT}",
            "docs_url": f"http://{REST_HOST}:{REST_PORT}/docs",
            "routes": []
        }
        
        if self.app:
            for route in self.app.routes:
                if hasattr(route, "path"):
                    status["routes"].append({
                        "path": route.path,
                        "methods": list(route.methods) if hasattr(route, "methods") else []
                    })
        
        return status

    def add_monitor_callback(self, callback):
        """Registers a callback for real-time API activity monitoring."""
        if callback not in self.monitor_callbacks:
            self.monitor_callbacks.append(callback)

    def remove_monitor_callback(self, callback):
        """Removes a previously registered monitor callback."""
        if callback in self.monitor_callbacks:
            self.monitor_callbacks.remove(callback)

    def notify_activity(self, method, path, status_code, payload=None):
        """Dispatches activity updates to all registered listeners."""
        for cb in self.monitor_callbacks:
            try:
                cb(method, path, status_code, payload)
            except Exception as e:
                logger.error(f"❌ [REST] Callback notification failed: {e}")
