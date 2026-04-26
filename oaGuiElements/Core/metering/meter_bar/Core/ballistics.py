# Core/ballistics.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2245.1
#
# Description: Ballistics engine for meter movement, now strictly Rust-powered.

from loguru import logger

try:
    from oaRustCore.oa_metering_engine_rs import BallisticsEngine as RustBallisticsEngine
    HAS_RUST_METERING = True
except ImportError:
    logger.warning("🚀⚠️ [GUI] Rust Metering Engine missing. Falling back to slow Python ballistics.")
    HAS_RUST_METERING = False

    class RustBallisticsEngine:
        """Fallback Python implementation of the ballistics engine."""
        def __init__(self, config):
            self.config = config
            self._current_value = -100.0 # Starting floor
            self._peak_value = -100.0
            self._target_value = -100.0
            self.overload_fade_factor = 0.0
        def set_target(self, value): self._target_value = float(value)
        def update(self, dt_ms):
            # Slow fallback math
            alpha = 0.2
            self._current_value = self._current_value * (1-alpha) + self._target_value * alpha
            if self._current_value > self._peak_value: self._peak_value = self._current_value
            else: self._peak_value -= 0.1 # Slow decay
            return self._current_value
        def reset(self): self._current_value = -100.0; self._peak_value = -100.0
        @property
        def current_value(self): return self._current_value
        @property
        def peak_value(self): return self._peak_value
        @property
        def is_overload(self): return self._current_value > 0.0
        @property
        def overload_fade(self): return self.overload_fade_factor

class BallisticsEngine:
    """Handles the physics math for meter movement."""

    def __init__(self, config):
        self.configuration = config
        try:
            self._engine = RustBallisticsEngine(config)
        except Exception as e:
            logger.critical(f"🚀❌ [FATAL] BallisticsEngine init failed: {e}")
            # Ensure we don't crash the builder, but this is a critical state
            self._engine = None

    def set_target(self, value):
        if self._engine: self._engine.set_target(value)

    def update(self, dt_ms):
        """Processes the ballistic state for one time step."""
        if self._engine: return self._engine.update(dt_ms)
        return 0.0

    @property
    def overload_fade_factor(self):
        if self._engine: return self._engine.overload_fade_factor
        return 0.0

    def reset(self):
        """Resets the engine to default values."""
        if self._engine: self._engine.reset()

    @property
    def current_value(self):
        if self._engine: return self._engine.current_value
        return -100.0

    @property
    def peak_value(self):
        if self._engine: return self._engine.peak_value
        return -100.0

    @property
    def is_overload(self):
        if self._engine: return self._engine.is_overload
        return False

    @property
    def overload_fade(self):
        if self._engine: return self._engine.overload_fade_factor
        return 0.0
