# Methods/pipeline.py
#
# Logic for processing splink pipelines (Scale, Invert, Deadband, etc.)
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Version: 20260331.2235.1

from loguru import logger
from oaLogging.Methods.matrix_gate import matrix_log, is_debug_allowed
from oaConfiguration.Entry import Config

try:
    from oasplinkcore_rs import SplinkPipeline as RustSplinkPipeline
except ImportError as e:
    logger.critical("🚀❌ [FATAL] Rust Splink Core module missing. Pure Rust mode is mandatory.")
    raise e

def _is_debug():
    return is_debug_allowed(system="CORE", element="SPLINKER")

class SplinkPipeline:
    def __init__(self, splink, splinker_manager):
        self.splink = splink
        self.splinker_manager = splinker_manager
        self.rust_pipeline = None
        self._build_pipeline()

    def _build_pipeline(self):
        handler_configs = self.splink.get("handlers", [])
        
        # In pure Rust mode, we MUST use RustSplinkPipeline
        # We assume Rust supports the standard handler types (scale, invert, deadband)
        try:
            self.rust_pipeline = RustSplinkPipeline(handler_configs)
            if _is_debug():
                matrix_log("core", "splinker", "_build_pipeline", 
                           f"🚀 SplinkPipeline: Using HIGH-PERFORMANCE RUST core for {self.splink['id']}.", "DEBUG")
        except Exception as e:
            matrix_log("core", "splinker", "_build_pipeline", 
                       f"🚀❌ [FATAL] Rust SplinkPipeline init failed for {self.splink['id']}: {e}", "ERROR")
            raise e

    def process(self, value, state=None, direction="FORWARD"):
        """Processes a value through the pipeline."""
        if state is None: state = {}
        if self.rust_pipeline:
            # Rust signature: process(value, _splink, state, direction)
            return self.rust_pipeline.process(value, self.splink, state, direction)
        return value
