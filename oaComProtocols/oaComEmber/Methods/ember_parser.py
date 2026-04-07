# oaComProtocols.oaComEmber/Methods/ember_parser.py
# Author: Anthony Peter Kuzub
# Version: 20260331.1630.2
#
# Description: Pure Rust Ember+ BER parser (No Python fallback).

LOCAL_DEBUG = False

import logging
from .oaEmberTree_rs.compiler_hook import ensure_compiled

try:
    ensure_compiled()
    from oaembertree_rs import EmberParser as RustEmberParser
    HAS_RUST = True
except ImportError:
    logging.warning("⚠️ [EMBER] oaembertree_rs not found. Ember parsing will be disabled.")
    HAS_RUST = False
except Exception as e:
    logging.error(f"❌ [EMBER] Failed to initialize Rust Ember Parser: {e}")
    HAS_RUST = False

LOCAL_DEBUG = False

class EmberParser:
    """
    Handles decoding of Ember+ BER (ASN.1) payloads.
    MANDATORY Rust backend.
    """
    def __init__(self):
        self._parser = None
        if not HAS_RUST:
            return

        if LOCAL_DEBUG:
            print("🌳🛠️🔗 [EMBER] Using PURE RUST parser.")
        try:
            self._parser = RustEmberParser()
        except Exception as e:
            logging.error(f"❌ [EMBER] Rust engine instantiation failed: {e}")
            self._parser = None

    def parse_ber_payload(self, data: bytes):
        """Parses a raw BER payload using the Rust engine."""
        if self._parser:
            try:
                return self._parser.parse_ber_payload(data)
            except Exception as e:
                logging.error(f"❌ [EMBER] Rust parsing failed: {e}")
                return {}
        return {}

