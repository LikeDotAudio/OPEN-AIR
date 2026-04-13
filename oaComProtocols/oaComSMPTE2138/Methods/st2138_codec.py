# oaComProtocols.oaComSMPTE2138/Methods/st2138_codec.py
# Author: Anthony Peter Kuzub
# Version: 20260331.1850.2
#
# Description: Pure Rust ST2138 Protobuf codec (No Python fallback).
from oaRustCore.oa_st2138_codec_rs import St2138Codec as RustSt2138Codec

LOCAL_DEBUG = False

class St2138Codec:
    """
    Handles encoding/decoding of SMPTE 2138 Protobuf messages.
    MANDATORY Rust implementation for speed.
    """
    def __init__(self):
        if LOCAL_DEBUG:
            print("📽️🛠️🔗 [ST2138] Using PURE RUST codec.")
        self._codec = RustSt2138Codec()

    def encode_param(self, name: str, value: float):
        return self._codec.encode_param(name, value)

    def decode_param(self, data: bytes):
        return self._codec.decode_param(data)
