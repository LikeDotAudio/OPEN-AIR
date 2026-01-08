# builder_core/gui_file_loader.py
#
# Handles File I/O and Hash Verification.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20250821.200641.1
import hashlib
import orjson
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args


class GuiFileLoaderMixin:
    """Handles File I/O and Hash Verification."""

    # Loads a GUI configuration from a JSON file and triggers a rebuild of the GUI.
    # This method reads the JSON file, verifies its content against a hash to avoid
    # unnecessary rebuilds, and then initiates the GUI reconstruction process.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def _load_and_build_from_file(self):
        if self.json_filepath is None:
            self._rebuild_gui()
            self.gui_built = True
            return

        try:
            if self.json_filepath.exists():
                with open(self.json_filepath, "r") as f:
                    raw_content = f.read()

                current_hash = hashlib.md5(raw_content.encode("utf-8")).hexdigest()
                if self.last_build_hash == current_hash:
                    return  # Content unchanged

                self.last_build_hash = current_hash
                self.config_data = orjson.loads(raw_content)
                self._publish_json_to_topic(self.config_data)
                self._rebuild_gui()
                self.gui_built = True
            else:
                debug_logger(
                    message=f"🟡 Warning: Config file missing at {self.json_filepath}",
                    **_get_log_args(),
                )
                if not self.config_data:
                    self.config_data = {}
                self._rebuild_gui()
                self.gui_built = True
        except Exception as e:
            debug_logger(
                message=f"❌ Error in _load_and_build_from_file: {e}", **_get_log_args()
            )