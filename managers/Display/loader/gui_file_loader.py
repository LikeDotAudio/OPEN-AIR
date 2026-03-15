# core/gui_file_loader.py
#
# Handles File I/O and Hash Verification.
# Now delegates to the standalone BlueprintLoader.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
# Version 20260222.Adapter.1

from pathlib import Path
from loguru import logger
from .blueprint_loader import BlueprintLoader

class GuiFileLoaderMixin:
    """
    Legacy Mixin for File Loading.
    Acts as a wrapper around BlueprintLoader.
    """

    def _load_and_build_from_file(self):
        """Loads JSON, checks hash, merges defaults, and triggers build."""
        
        config_data, new_hash, is_changed = BlueprintLoader.load_blueprint(
            self.json_filepath, 
            self.tab_name, 
            self.last_build_hash
        )
        
        if not is_changed and self.json_filepath:
            return  # Content unchanged

        if config_data is None: 
            # Error or empty
            if self.json_filepath: return
            config_data = {} # Fallback for no file

        self.config_data = config_data
        if new_hash:
            self.last_build_hash = new_hash

        # --- AUTO-PATCH METAL FOLDS ---
        # If metal_fold is enabled but has no creases, auto-populate them
        # based on the presence of columns or break lines.
        self._auto_configure_metal_folds()

        # --- Apply Tab-Level Panel Background ---
        bg_config = self.config_data.get("background")
        if bg_config != "none" and bg_config:
            self._apply_panel_background(bg_config)

        # ⚡ AUTO-PUBLISH: Announce this GUI and all its initial widget states to MQTT
        # This populates the OID tree and SNMP bridge immediately on load.
        # ⚡ ICE: User requested to stop GUI from announcing itself
        # if hasattr(self, "_publish_json_to_topic"):
        #     self._publish_json_to_topic(self.config_data)
        # if hasattr(self, "_publish_initial_widget_states"):
        #     self._publish_initial_widget_states(self.config_data)

        self._rebuild_gui()
        self.gui_built = True

    def _auto_configure_metal_folds(self):
        """
        Analyzes the config_data and automatically populates 
        metal_fold creases if they are missing.
        """
        # ⚡ DISABLED: We now rely on DynamicGuiBuilder's 'Fold Sync' engine 
        # which detects explicit OcaFold widgets in real-time.
        # This prevents OcaBlocks with columns from generating phantom folds.
        return 

    def _load_default_background(self):
        """Helper to specifically get the background config from the default panel."""
        # We can re-use the loader's cache access via a private method or just reload
        # For efficiency, we assume BlueprintLoader has it cached
        default_config = BlueprintLoader._load_default_config()
        return default_config.get("background")
