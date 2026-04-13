# oaComProtocols.oaComREST/Methods/rest_server.py
# Author: Anthony Peter Kuzub
# Version: 20260413.1100.1
#
# Description: High-performance REST server with Rust fallback.
import logging

try:
    from oaRustCore.oa_fast_api_rs import RestServer as RustRestServer
    HAS_RUST_REST = True
except ImportError:
    import logging
    logging.warning("🚀⚠️ [REST] Rust RestServer missing. REST API will be non-functional.")
    HAS_RUST_REST = False

LOCAL_DEBUG = False

class RestServer:
    """
    High-performance REST server using Rust Axum.
    """
    def __init__(self):
        if LOCAL_DEBUG:
            print("🚀🛠️🔗 [REST] Initializing REST server.")
        self._server = RustRestServer() if HAS_RUST_REST else None

    def add_route(self, path: str, callback):
        """Adds a route to the REST server."""
        if self._server:
            return self._server.add_route(path, callback)
        if LOCAL_DEBUG:
            print(f"🚀⚠️ [REST] Skipping route registration (No Rust Server): {path}")

    def start(self, host: str = "0.0.0.0", port: int = 8080):
        """Starts the REST server."""
        if self._server:
            self._server.start(host, port)
        else:
            logging.error(f"🚀❌ [REST] Cannot start server on {host}:{port}. Rust binary missing.")
