# builder_core/gui_rebuilder.py
#
# Handles the destruction and re-initialization of the GUI Frame.
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
import tkinter as tk
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args


class GuiRebuilderMixin:
    """Handles the destruction and re-initialization of the GUI Frame."""

    # Forces a complete rebuild of the GUI by clearing the hash and reloading from file.
    # This method is used when an explicit refresh of the GUI is required, bypassing
    # any optimization that might prevent rebuilding from unchanged configuration.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def _force_rebuild_gui(self):
        self.last_build_hash = None
        self._load_and_build_from_file()

    # Rebuilds the GUI by destroying existing widgets and recreating them from the configuration.
    # This method iterates through the configured widgets and uses the batch builder to
    # efficiently construct the new GUI layout.
    # Inputs:
    #     None.
    # Outputs:
    #     None.
    def _rebuild_gui(self):
        try:
            # Destroy all children in the scroll frame
            for child in self.scroll_frame.winfo_children():
                child.destroy()

            self.topic_widgets.clear()
            self.update_idletasks()

            widget_configs = list(self.config_data.items())
            # Start the batch builder (Logic in separate file)
            self._create_widgets_in_batches(self.scroll_frame, widget_configs)

        except Exception as e:
            debug_logger(message=f"❌ Error in _rebuild_gui: {e}", **_get_log_args())