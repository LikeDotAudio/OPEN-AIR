# Core/ballistics.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2245.1
#
# Description: Ballistics engine for meter movement, now strictly Rust-powered.

import time
from loguru import logger
from oaConfigurationManager.Entry import Config

try:
    from oaRustCore.oa_metering_engine_rs import BallisticsEngine as RustBallisticsEngine
    HAS_RUST_METERING = True
except ImportError:
    logger.warning("🚀⚠️ [GUI] Rust Metering Engine missing. Falling back to slow Python ballistics.")
    HAS_RUST_METERING = False

class BallisticsEngine:
    """Handles the physics math for meter movement."""
    
    def __init__(self, config):
        self._engine = RustBallisticsEngine(config) if HAS_RUST_METERING else None
        self.configuration = config
        try:
            self.rust_engine = RustBallisticsEngine(config)
        except Exception as e:
            logger.critical(f"🚀❌ [FATAL] Rust BallisticsEngine init failed: {e}")
            raise e

    def set_target(self, value):
        self.rust_engine.set_target(value)

    def update(self, dt_ms):
        """Processes the ballistic state for one time step."""
        return self.rust_engine.update(dt_ms)

    @property
    def overload_fade_factor(self):
        return self.rust_engine.overload_fade_factor

    def reset(self):
        """Resets the engine to default values."""
        self.rust_engine.reset()

    @property
    def current_value(self):
        return self.rust_engine.current_value

    @property
    def peak_value(self):
        return self.rust_engine.peak_value

    @property
    def is_overload(self):
        return self.rust_engine.is_overload

    @property
    def overload_fade(self):
        return self.rust_engine.overload_fade_factor
