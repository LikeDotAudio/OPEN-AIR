import time
import orjson
from workers.mqtt.mqtt_topic_utils import get_topic
from workers.mqtt.mqtt_publisher_service import is_connected
import tkinter as tk

class HiddenBreakoffManagerMixin:
    """
    The 'Break-off Snitch'. Reports if the widget is in a separate window.
    """
    def _setup_breakoff_snitch(self):
        """Called during __init__ to bind events."""
        if not self.state_mirror_engine:
            return
            
        self.main_root = self.state_mirror_engine.root
        self.is_broken_off = False
        self.toplevel_window = None

        self.breakoff_topic = get_topic(
            self.state_mirror_engine.base_topic,
            self.base_mqtt_topic_from_path,
            "visibility/breakoff"
        )
        
        # Check the state when the widget is mapped
        self.bind("<Map>", self._check_breakoff_state)

    def _check_breakoff_state(self, event=None):
        """Checks if the widget has been broken off into a new window."""
        if not self.winfo_exists():
            return

        current_toplevel = self.winfo_toplevel()

        # State: Broken Off
        if current_toplevel is not self.main_root:
            if not self.is_broken_off:
                self.is_broken_off = True
                self.toplevel_window = current_toplevel
                self._publish_breakoff_state()
                self.toplevel_window.bind("<Configure>", self._on_broken_off_configure)
                self.toplevel_window.bind("<Destroy>", self._on_broken_off_destroy)
        
        # State: Not Broken Off (or returned)
        else:
            if self.is_broken_off:
                self.is_broken_off = False
                if self.toplevel_window:
                    try:
                        self.toplevel_window.unbind("<Configure>")
                        self.toplevel_window.unbind("<Destroy>")
                    except tk.TclError:
                        pass # Window might already be destroyed
                self.toplevel_window = None
                self._publish_breakoff_state()

    def _on_broken_off_configure(self, event):
        """Handles geometry changes of the broken-off window."""
        self._publish_breakoff_state()

    def _on_broken_off_destroy(self, event):
        """Handles the destruction of the broken-off window."""
        if self.is_broken_off:
             # Make sure the event is for the toplevel window
            if event.widget == self.toplevel_window:
                self.is_broken_off = False
                self.toplevel_window = None
                self._publish_breakoff_state()
                # Don't publish here, as the visibility snitch will handle the destroy event of the widget itself.
                # and we might not be connected to the broker anymore
                
    def _publish_breakoff_state(self):
        if not is_connected():
            return
            
        width = 0
        height = 0
        x = 0
        y = 0

        if self.is_broken_off and self.toplevel_window:
            try:
                self.toplevel_window.update_idletasks() # Ensure geometry is up to date
                width = self.toplevel_window.winfo_width()
                height = self.toplevel_window.winfo_height()
                x = self.toplevel_window.winfo_x()
                y = self.toplevel_window.winfo_y()
            except tk.TclError:
                # The window might be destroyed before we can get its geometry
                self.is_broken_off = False

        payload = {
            "is_broken_off": self.is_broken_off,
            "width": width,
            "height": height,
            "x": x,
            "y": y,
            "ts": time.time(),
            "tab_name": getattr(self, "tab_name", "Unknown")
        }
        
        self.state_mirror_engine.publish_command(
            self.breakoff_topic,
            orjson.dumps(payload)
        )
