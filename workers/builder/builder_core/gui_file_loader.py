import hashlib
import orjson
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args

class GuiFileLoaderMixin:
    """Handles File I/O and Hash Verification."""

    def _load_and_build_from_file(self):
        if self.json_filepath is None:
            self._rebuild_gui()
            self.gui_built = True
            return

        try:
            if self.json_filepath.exists():
                with open(self.json_filepath, 'r') as f:
                    raw_content = f.read()

                current_hash = hashlib.md5(raw_content.encode('utf-8')).hexdigest()
                if self.last_build_hash == current_hash:
                    return # Content unchanged

                self.last_build_hash = current_hash
                self.config_data = orjson.loads(raw_content)
                self._rebuild_gui()
                self.gui_built = True
            else:
                debug_logger(message=f"🟡 Warning: Config file missing at {self.json_filepath}", **_get_log_args())
                if not self.config_data:
                    self.config_data = {}
                self._rebuild_gui()
                self.gui_built = True
        except Exception as e:
            debug_logger(message=f"❌ Error in _load_and_build_from_file: {e}", **_get_log_args())
