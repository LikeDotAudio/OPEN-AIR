# oaComREST/Methods/rest_server.py
# Author: Anthony Peter Kuzub
# Version: 20260331.1830.2
#
# Description: Pure Rust REST server (No Python fallback).

from .oaFastAPI_rs.compiler_hook import ensure_compiled
ensure_compiled()
from .oaFastAPI_rs.oafastapi_rs import RestServer as RustRestServer

class RestServer:
    """
    High-performance REST server using Rust Axum.
    MANDATORY Rust backend.
    """
    def __init__(self):
        print("🚀🛠️🔗 [REST] Using PURE RUST server (Axum).")
        self._server = RustRestServer()

    def add_route(self, path: str, callback):
        self._server.add_route(path, callback)

    def start(self, host: str = "0.0.0.0", port: int = 8080):
        self._server.start(host, port)
