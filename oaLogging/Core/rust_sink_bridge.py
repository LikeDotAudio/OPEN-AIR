# oaLogging/Core/rust_sink_bridge.py
# Author: Gemini (Collaborator)
# Version: 20260413.1000.1
#
# Description: Bridge for Native Rust Asynchronous Log Sinking.

try:
    from oaRustCore.oa_async_sink_rs import AsyncSink
    _rust_async_sink = AsyncSink()
    HAS_RUST_SINK = True
except Exception:
    _rust_async_sink = None
    HAS_RUST_SINK = False

def get_rust_sink():
    """Returns the initialized Rust sink instance, if available."""
    return _rust_async_sink

def has_rust_sink():
    """Checks if the Native Rust Asynchronous sink is active."""
    return HAS_RUST_SINK

def teardown_rust_sink():
    """Safely terminates the Rust sink bridge."""
    global _rust_async_sink
    if HAS_RUST_SINK:
        _rust_async_sink = None
