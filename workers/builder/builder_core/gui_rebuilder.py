import tkinter as tk
from workers.logger.logger import debug_logger
from workers.logger.log_utils import _get_log_args


class GuiRebuilderMixin:
    """Handles the destruction and re-initialization of the GUI Frame."""

    def _force_rebuild_gui(self):
        self.last_build_hash = None
        self._load_and_build_from_file()

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
