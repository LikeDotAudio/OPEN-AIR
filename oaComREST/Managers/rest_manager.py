# oaComREST/Managers/rest_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260327.1830.1
#
# Description: Orchestrator for the REST API service with deep activity tracking.

import importlib
import threading
import time
import os
from loguru import logger

def check_fastapi_availability():
    """Checks if FastAPI and its required dependencies are installed."""
    try:
        importlib.import_module("fastapi")
        importlib.import_module("uvicorn")
        return True
    except ImportError as e:
        logger.error(f"❌ [REST] Dependency check failed: {e}")
        return False

from ..Constants.rest_constants import LOCAL_DEBUG, REST_HOST, REST_PORT, REST_CORS_ORIGINS
from ..Workers.uvicorn_worker import UvicornWorker
from ..Interface.routes import create_router
from ..Methods.port_utils import zap_port, get_process_on_port, is_friendly_process

class RESTManager:
    """
    Manages the lifecycle of the FastAPI REST service.
    Features a sibling-aware health monitor and detailed traffic capturing.
    """
    STATE_TOPIC = "OPEN-AIR/System/Config/REST/Enabled"

    def __init__(self, state_cache_manager, protocol_router):
        self.state_cache = state_cache_manager
        self.router = protocol_router
        self.app = None
        self.worker = None
        self.monitor_callbacks = []
        self._initialized = False
        self._should_run = False
        self._health_thread = None
        self._sibling_active = False

        # 1. Dependency Check
        self._initialized = self._try_initialize()
        
        # 2. State Integration
        if self.state_cache:
            self.state_cache.register_cache_observer(self._on_global_state_change)
            initial = self.state_cache.get_cached_value(self.STATE_TOPIC)
            if initial is not None:
                self._should_run = bool(initial)

        # 3. Launch Monitor
        self._start_health_monitor()

    def _on_global_state_change(self, topic, payload):
        if topic != self.STATE_TOPIC: return
        value = payload.get("val") if isinstance(payload, dict) else payload
        new_state = bool(value)
        if new_state != self._should_run:
            logger.info(f"📡⚙️🔄 [REST] Global state toggle: {new_state}")
            self._should_run = new_state
            if not new_state: self._shutdown_local_worker()
            else: self._launch_instance()

    def _try_initialize(self):
        if not check_fastapi_availability(): return False
        try:
            from fastapi import FastAPI
            from fastapi.middleware.cors import CORSMiddleware
            self.app = FastAPI(title="OPEN-AIR REST API", version="1.0.0")
            self.app.add_middleware(CORSMiddleware, allow_origins=REST_CORS_ORIGINS, 
                                    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
            
            # 🛰️ TRAFFIC MONITORING MIDDLEWARE
            @self.app.middleware("http")
            async def activity_log_middleware(request, call_next):
                payload = None
                if request.method == "POST":
                    try:
                        # Peek at the body for logging
                        body = await request.body()
                        payload = body.decode()[:100]
                    except: pass
                
                response = await call_next(request)
                
                self.notify_activity(
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    payload=payload
                )
                return response

            api_router = create_router(self.state_cache, self.router)
            self.app.include_router(api_router)
            logger.success("📡⚙️✅ [REST] FastAPI Application initialized.")
            return True
        except Exception as e:
            logger.error(f"❌ [REST] Initialization crash: {e}")
            return False

    def _start_health_monitor(self):
        if self._health_thread and self._health_thread.is_alive(): return
        self._health_thread = threading.Thread(target=self._health_loop, daemon=True, name="REST-HealthMonitor")
        self._health_thread.start()

    def _health_loop(self):
        while True:
            try:
                if self._should_run:
                    is_local = self.is_running()
                    proc = get_process_on_port(REST_PORT)
                    is_sibling = proc and is_friendly_process(proc) and not is_local
                    if is_local: self._sibling_active = False
                    elif is_sibling: self._sibling_active = True
                    else:
                        self._sibling_active = False
                        self._launch_instance()
                else:
                    if self.is_running(): self._shutdown_local_worker()
            except Exception as e: logger.error(f"❌ [REST] Health loop error: {e}")
            time.sleep(10.0)

    def _launch_instance(self):
        if not self._initialized: return
        proc = get_process_on_port(REST_PORT)
        if proc:
            if is_friendly_process(proc):
                self._sibling_active = True
                return
            elif not zap_port(REST_PORT): return

        try:
            self.worker = UvicornWorker(self.app, host=REST_HOST, port=REST_PORT)
            if LOCAL_DEBUG: logger.info(f"🌐 [REST] Launching API Service on {REST_HOST}:{REST_PORT}...")
            self.worker.start()
        except Exception as e: logger.error(f"❌ [REST] Launch failed: {e}")

    def _shutdown_local_worker(self):
        if self.worker and self.worker.is_alive():
            if LOCAL_DEBUG: logger.info("🌐 [REST] Shutting down local instance.")
            self.worker.stop()
            self.worker.join(timeout=2.0)

    def start(self):
        if not self._initialized:
            if not self._try_initialize(): return False
        if self.state_cache:
            self.state_cache.handle_external_update(self.STATE_TOPIC, True, source="REST-CTRL")
        self._should_run = True
        self._launch_instance()
        return True

    def stop(self):
        if self.state_cache:
            self.state_cache.handle_external_update(self.STATE_TOPIC, False, source="REST-CTRL")
        self._should_run = False
        self._shutdown_local_worker()
        return True

    def is_running(self):
        return self.worker is not None and self.worker.is_alive()

    def get_status(self):
        status = {
            "running": self.is_running() or self._sibling_active,
            "local_host": self.is_running(),
            "sibling_host": self._sibling_active,
            "should_run": self._should_run,
            "initialized": self._initialized,
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

    def add_monitor_callback(self, cb):
        if cb not in self.monitor_callbacks: self.monitor_callbacks.append(cb)
    def remove_monitor_callback(self, cb):
        if cb in self.monitor_callbacks: self.monitor_callbacks.remove(cb)
    def notify_activity(self, method, path, status_code, payload=None):
        for cb in self.monitor_callbacks:
            try: cb(method, path, status_code, payload)
            except Exception as e: logger.error(f"❌ [REST] Callback failed: {e}")
