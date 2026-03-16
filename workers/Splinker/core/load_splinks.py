import orjson
from ..constants import Splinker_debug_enabled, splinker_logger

def _load_splinks(self):
    try:
        if Splinker_debug_enabled:
            splinker_logger.debug(f"📂🔗⚙️ [SPLINKER] Storage Path: "
                                  f"{self.storage_path.absolute()}")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        if Splinker_debug_enabled:
            splinker_logger.debug(f"📂🔗📥 [SPLINKER] Loading splinks from "
                                  f"{self.storage_path}")
            
        self.splinks = []
        for f in self.storage_path.glob("*.json"):
            with open(f, "rb") as splink_file:
                self.splinks.append(orjson.loads(splink_file.read()))
        self._publish_splinks()
    except Exception as e:
        # Gravity of Errors: Non-gated failure reporting.
        splinker_logger.error(f"📂🔗🚫 [SPLINKER] ERROR: Failed to load "
                              f"splinks: {e}")
        self.splinks = []
