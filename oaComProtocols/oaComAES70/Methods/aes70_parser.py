# oaComProtocols.oaComAES70/Methods/aes70_parser.py
# Author: Anthony Peter Kuzub
# Version: 20260331.1530.2
#
# Description: Pure Rust OCP.1 parser (No Python fallback).

from .oaAES70Core_rs.compiler_hook import ensure_compiled
ensure_compiled()
from .oaAES70Core_rs.oaaes70core_rs import OcaParser as RustOcaParser

LOCAL_DEBUG = False

class OcaParser:
    """
    Handles decoding of AES70 OCP.1 (TCP/IP) packets.
    MANDATORY Rust implementation for high performance.
    """
    def __init__(self):
        if LOCAL_DEBUG:
            print("📻🛠️🔗 [AES70] Using PURE RUST parser.")
        self._parser = RustOcaParser()

    def decode(self, data: bytes):
        """Decodes a raw OCP.1 PDU using the Rust engine."""
        return self._parser.decode(data)
