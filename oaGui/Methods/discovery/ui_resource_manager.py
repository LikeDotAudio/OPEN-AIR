# Methods/ui_resource_manager.py
# Author: Anthony Peter Kuzub
# Version: 20260501.1000.1
#
# Description: Periodic resource maintenance for the OPEN-AIR UI service.

import gc


class UIResourceManager:
    """Periodic resource maintenance for the OPEN-AIR UI service."""
    @staticmethod
    def start_periodic_gc(root, interval_ms=30000):
        """Starts a periodic garbage collection loop."""
        def _periodic_gc():
            gc.collect()
            if not getattr(root, '_shutdown', False) and root.winfo_exists():
                root.after(interval_ms, _periodic_gc)

        root.after(interval_ms, _periodic_gc)
        gc.collect()
        return _periodic_gc
