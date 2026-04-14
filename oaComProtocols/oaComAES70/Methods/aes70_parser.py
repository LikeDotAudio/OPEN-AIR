# oaComProtocols.oaComAES70/Methods/aes70_parser.py
# Author: Anthony Peter Kuzub
# Version: 20260331.1530.2
#
# Description: Pure Rust OCP.1 parser (No Python fallback).
try:
    from oaRustCore.oa_aes70_core_rs import OcaParser as RustOcaParser
    HAS_RUST_AES70 = True
except ImportError:
    HAS_RUST_AES70 = False

LOCAL_DEBUG = False

class OcaParser:
    """
    Handles decoding of AES70 OCP.1 (TCP/IP) packets.
    """
    def __init__(self):
        self._parser = RustOcaParser() if HAS_RUST_AES70 else None
        if LOCAL_DEBUG:
            print("📻🛠️🔗 [AES70] Using PURE RUST parser.")
        self._parser = RustOcaParser()

    def decode(self, data: bytes):
        """Decodes a raw OCP.1 PDU using the Rust engine."""
        return self._parser.decode(data)
