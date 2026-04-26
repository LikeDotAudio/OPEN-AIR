# Core/load_splinks.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import orjson

from ..Constants.constants import Splinker_debug_enabled, splinker_logger


def load_splinks(self):
    try:
        if Splinker_debug_enabled:
            splinker_logger.debug(f"📂🔗⚙️ [SPLINKER] Storage Path: "
                                  f"{self.storage_path.absolute()}")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        if Splinker_debug_enabled:
            splinker_logger.debug(f"📂🔗📥 [SPLINKER] Loading splinks from "
                                  f"{self.storage_path}")

        self.registry.clear()
        for f in self.storage_path.glob("*.json"):
            with open(f, "rb") as splink_file:
                s = orjson.loads(splink_file.read())
                # Key by source topic for fast lookup
                self.registry.add_splink(s["source"], s)
        self.publish_splinks()
    except Exception as e:
        # Gravity of Errors: Non-gated failure reporting.
        splinker_logger.error(f"📂🔗🚫 [SPLINKER] ERROR: Failed to load "
                              f"splinks: {e}")
        self.registry.clear()
