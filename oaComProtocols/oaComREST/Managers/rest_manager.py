# oaComProtocols.oaComREST/Managers/rest_manager.py
#
# Orchestrator for the REST API service. Manages the lifecycle of the 
# FastAPI application and uvicorn worker thread.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260330.1600.1

import importlib
import threading
import time
import os
from loguru import logger
from oaLogging.Methods.matrix_gate import matrix_log

def check_fastapi_availability():
    """Checks if FastAPI and its required dependencies are installed."""
    try:
        importlib.import_module("fastapi")
        importlib.import_module("uvicorn")
        return True
    except ImportError as e:
        matrix_log("comms", "rest", "check_fastapi_availability", f"❌ [REST] Dependency check failed: {e}", "ERROR")
        return False

from ..Constants.rest_constants import LOCAL_DEBUG, REST_BIND_HOST, REST_REPORT_HOST, REST_PORT, REST_CORS_ORIGINS
from ..Workers.uvicorn_worker import UvicornWorker
from ..Interface.routes import create_router
from ..Methods.port_utils import zap_port, get_process_on_port, is_friendly_process

class RESTManager:
    """
    Manages the lifecycle of the FastAPI REST service.
    
    Mandate: Always Online. The REST API is a core system service and 
    cannot be disabled while the module is present.
    """
    STATE_TOPIC = "OPEN-AIR/System/Config/REST/Status" # Changed from Enabled to Status

    def __init__(self, state_cache_manager, protocol_router):
        self.state_cache = state_cache_manager
        self.router = protocol_router
        self.app = None
        self.worker = None
        self.monitor_callbacks = []
        self._initialized = False
        self._should_run = True # ⚡ MANDATORY: Always active on boot
        self._health_thread = None
        self._sibling_active = False

        # 1. Dependency Check
        self._initialized = self._try_initialize()
        
        # 2. State Integration (Read-only status now)
        if self.state_cache:
            # We no longer listen for 'Enabled' toggles; REST is mandatory.
            self.state_cache.handle_external_update(self.STATE_TOPIC, True, source="REST-INIT")

        # 3. Launch Monitor
        self._start_health_monitor()

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
            matrix_log("comms", "rest", "_try_initialize", "📡⚙️✅ [REST] FastAPI Application initialized.", "SUCCESS")
            return True
        except Exception as e:
            matrix_log("comms", "rest", "_try_initialize", f"❌ [REST] Initialization crash: {e}", "ERROR")
            return False

    def _start_health_monitor(self):
        if self._health_thread and self._health_thread.is_alive(): return
        self._health_thread = threading.Thread(target=self._health_loop, daemon=True, name="REST-HealthMonitor")
        self._health_thread.start()

    def _health_loop(self):
        while True:
            try:
                # ⚡ MANDATORY: Always attempt to keep the service alive
                is_local = self.is_running()
                proc = get_process_on_port(REST_PORT)
                is_sibling = proc and is_friendly_process(proc) and not is_local
                
                if is_local: 
                    self._sibling_active = False
                elif is_sibling: 
                    self._sibling_active = True
                else:
                    self._sibling_active = False
                    self._launch_instance()
                    
                # Update status in cache
                if self.state_cache:
                    self.state_cache.handle_external_update(self.STATE_TOPIC, self.is_running() or self._sibling_active, source="REST-HB")

            except Exception as e: 
                matrix_log("comms", "rest", "_health_loop", f"❌ [REST] Health loop error: {e}", "ERROR")
            time.sleep(2.0)

    def _launch_instance(self):
        if not self._initialized: return
        proc = get_process_on_port(REST_PORT)
        if proc:
            if is_friendly_process(proc):
                self._sibling_active = True
                return
            elif not zap_port(REST_PORT): return

        try:
            self.worker = UvicornWorker(self.app, host=REST_BIND_HOST, port=REST_PORT)
            matrix_log("comms", "rest", "_launch_instance", f"🌐 [REST] Launching Mandatory API Service on {REST_BIND_HOST}:{REST_PORT} (URL: http://{REST_REPORT_HOST}:{REST_PORT})...", "INFO")
            self.worker.start()
        except Exception as e: 
            matrix_log("comms", "rest", "_launch_instance", f"❌ [REST] Launch failed: {e}", "ERROR")

    def _shutdown_local_worker(self):
        """DEPRECATED: REST API is mandatory and cannot be shut down manually."""
        matrix_log("comms", "rest", "_shutdown_local_worker", "⚠️ [REST] Shutdown request ignored: Service is mandatory.", "WARNING")

    def start(self):
        """Ensures the service is running. Always returns True as it is mandatory."""
        if not self._initialized:
            if not self._try_initialize(): return False
        self._launch_instance()
        return True

    def stop(self):
        """DEPRECATED: REST API is mandatory and cannot be stopped."""
        matrix_log("comms", "rest", "stop", "ℹ️ [REST] Service is mandatory and remains active.", "INFO")
        return False

    def is_running(self):
        return self.worker is not None and self.worker.is_alive()

    def get_status(self):
        status = {
            "running": self.is_running() or self._sibling_active,
            "local_host": self.is_running(),
            "sibling_host": self._sibling_active,
            "should_run": self._should_run,
            "initialized": self._initialized,
            "host": REST_REPORT_HOST,
            "port": REST_PORT,
            "url": f"http://{REST_REPORT_HOST}:{REST_PORT}",
            "docs_url": f"http://{REST_REPORT_HOST}:{REST_PORT}/docs",
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
            except Exception as e: 
                matrix_log("comms", "rest", "notify_activity", f"❌ [REST] Callback failed: {e}", "ERROR")
