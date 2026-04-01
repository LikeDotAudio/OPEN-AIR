# oaComEmber/Methods/ember_parser.py
# Author: Anthony Peter Kuzub
# Version: 20260331.1630.2
#
# Description: Pure Rust Ember+ BER parser (No Python fallback).

from .oaEmberTree_rs.compiler_hook import ensure_compiled
ensure_compiled()
from .oaEmberTree_rs.oaembertree_rs import EmberParser as RustEmberParser

class EmberParser:
    """
    Handles decoding of Ember+ BER (ASN.1) payloads.
    MANDATORY Rust backend.
    """
    def __init__(self):
        print("🌳🛠️🔗 [EMBER] Using PURE RUST parser.")
        self._parser = RustEmberParser()

    def parse_ber_payload(self, data: bytes):
        """Parses a raw BER payload using the Rust engine."""
        return self._parser.parse_ber_payload(data)
