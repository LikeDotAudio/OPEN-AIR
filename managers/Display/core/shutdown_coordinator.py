import sys
from loguru import logger

class ShutdownCoordinator:
    """Manages the clean, sequential shutdown of all background services."""

    def __init__(self, root, shared_instances, debug_enabled=True):
        self.root = root
        self.shared_instances = shared_instances
        self.debug_enabled = debug_enabled

    def on_closing(self):
        """Gracefully terminates all UI and Communication sub-processes."""
        if self.debug_enabled: logger.debug("🖥️🎨 [UI] Initiating shutdown...")
        self.root._shutdown = True
        
        # Sequentially stop all active managers
        for name, instance in self.shared_instances.items():
            if instance:
                try:
                    if hasattr(instance, "stop"): instance.stop()
                    elif hasattr(instance, "shutdown"): instance.shutdown()
                    elif hasattr(instance, "disconnect"): instance.disconnect()
                except Exception as e:
                    logger.warning(f"⚠️ Error shutting down {name}: {e}")
        
        self.root.destroy()
        sys.exit(0)

    def attach_to_root(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
