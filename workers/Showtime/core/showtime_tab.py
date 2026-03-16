import tkinter as tk
from tkinter import ttk
from loguru import logger

from .showtime_state_mixin import ShowtimeStateMixin
from .showtime_group_mixin import ShowtimeGroupMixin
from .showtime_read_mixin import ShowtimeReadMixin
from .showtime_interaction_mixin import ShowtimeInteractionMixin
from .showtime_tune_mixin import ShowtimeTuneMixin
from .showtime_ui_mixin import ShowtimeUIMixin

class ShowtimeTab(
    tk.Frame,
    ShowtimeStateMixin,
    ShowtimeGroupMixin,
    ShowtimeReadMixin,
    ShowtimeInteractionMixin,
    ShowtimeTuneMixin,
    ShowtimeUIMixin
):
    """
    The unified, modularized Showtime Tab component.
    Adheres to SRP and follows the 'self-only' argument rule for stateful logic.
    """

    def __init__(self, parent, config=None, json_path=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.config_data = config or {}
        self.json_path = json_path
        
        # 1. Initialize Mixin State
        self._initialize_showtime_state()
        
        # 2. Build Scaffold
        self._build_scaffold()
        
        # 3. Load & Process Initial Data
        self.load_marker_data()
        self.process_and_sort_markers()
        
        # 4. Initial Render
        self._refresh_showtime_ui()

    def _build_scaffold(self):
        """Creates the primary layout frames for Zones, Groups, and Devices."""
        self.zone_frame = tk.Frame(self, bg=self.cget("bg"))
        self.zone_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        self.group_frame = tk.Frame(self, bg=self.cget("bg"))
        self.group_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # Device area with scrollbar
        self.device_container = tk.Frame(self, bg=self.cget("bg"))
        self.device_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(self.device_container, bg=self.cget("bg"), highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.device_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.device_frame = tk.Frame(self.canvas, bg=self.cget("bg"))
        
        self.canvas.create_window((0, 0), window=self.device_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.device_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def render(self):
        """Standard render entry point for DynamicGuiBuilder."""
        self._refresh_showtime_ui()
