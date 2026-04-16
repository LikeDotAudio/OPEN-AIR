import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# grab_bag/grab_bag_view.py
# Author: Gemini CLI
# Version: 1.0.0
#
# Description: The UI palette for the Grab Bag.

import tkinter as tk
from tkinter import ttk
import copy
from ...FileReaders.grab_bag_loader import GrabBagLoader
from oaComBroker.Core.event_bus import event_bus
from ...Core.state import state_manager
from oaLogging.Core.logger import GUI_LOGGER as logger



class AutoScrollbar(ttk.Scrollbar):
    """A scrollbar that hides itself when it's not needed."""
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.pack_forget()
        else:
            self.pack(side="right", fill="y")
        ttk.Scrollbar.set(self, lo, hi)

class GrabBagView(tk.Frame):
    """A palette of draggable/selectable GUI components."""

    def __init__(self, parent, library_cache=None, *args, **kwargs):
        kwargs.pop("bg", None)
        super().__init__(parent, bg="#2b2b2b", *args, **kwargs)
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "GrabBagView: Initializing palette...", "DEBUG")
        self.loader = GrabBagLoader()
        self.library = library_cache if library_cache is not None else self.loader.scan_library()
        self.last_focused_path = None
        self._build_ui()
        
        # Track selection to know where to insert
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "GrabBagView: Subscribing to FOCUS_REQUESTED...", "DEBUG")
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)
        
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event):
        if event.widget == self:
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "GrabBagView: Workspace destroyed. Cleaning up subscriptions and bindings.", "INFO")
            event_bus.unsubscribe("FOCUS_REQUESTED", self._on_focus_requested)
            
            # CRITICAL: Cleanup bind_all to prevent memory leaks and crashes on relaunch
            try:
                matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "GrabBagView: Unbinding global mousewheel events...", "DEBUG")
                self.canvas.unbind_all("<MouseWheel>")
                self.canvas.unbind_all("<Button-4>")
                self.canvas.unbind_all("<Button-5>")
            except: pass

    def _on_focus_requested(self, path, source=None):
        self.last_focused_path = path
        # logger.debug(f"GrabBag: Tracking focus path for insertion: {path}")

    def _build_ui(self):
        """Builds the Grab Bag UI."""
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "GrabBagView: Building Palette UI...", "DEBUG")
        header = tk.Frame(self, bg="#333333", height=35)
        header.pack(side="top", fill="x")
        
        tk.Label(header, text="GRAB BAG COMPONENTS", bg="#333333", fg="white", 
                 font=("Arial", 9, "bold")).pack(side="left", padx=10, pady=5)
        
        ttk.Button(header, text="Refresh", command=self._refresh_library).pack(side="right", padx=5)

        # Scrollable area for components
        self.canvas = tk.Canvas(self, bg="#2b2b2b", bd=0, highlightthickness=0)
        self.scrollbar = AutoScrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg="#2b2b2b")
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        self.scroll_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Mousewheel bindings
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "GrabBagView: Binding global mousewheel...", "DEBUG")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

        self._refresh_library()

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if not self.winfo_exists() or not self.canvas.winfo_viewable(): return
        if event.num == 4: delta = -1
        elif event.num == 5: delta = 1
        else: delta = int(-1 * (event.delta / 120))
        self.canvas.yview_scroll(delta, "units")

    def _refresh_library(self):
        """Reloads components from disk and rebuilds the UI."""
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "GrabBag: Refreshing component library...", "INFO")
        for child in self.scroll_frame.winfo_children():
            child.destroy()
            
        library = getattr(self, 'library', None)
        if library is None:
            library = self.loader.scan_library()
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"GrabBag: Scan complete. Found {len(library)} component templates.", "INFO")
        
        for name, info in library.items():
            comp_frame = tk.Frame(self.scroll_frame, bg="#333333", bd=1, relief="raised", padx=10, pady=10)
            comp_frame.pack(fill="x", padx=10, pady=5)
            
            tk.Label(comp_frame, text=name, bg="#333333", fg="white", font=("Arial", 10, "bold")).pack(side="left")
            tk.Label(comp_frame, text=f"({info['type']})", bg="#333333", fg="#888888", font=("Arial", 8)).pack(side="left", padx=5)
            
            # Button to Add After Selected
            btn = ttk.Button(comp_frame, text="Add After Selected", command=lambda n=name: self._add_component(n))
            btn.pack(side="right")

    def _add_component(self, name):
        """Adds the selected component to the master JSON state after the focused item."""
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"GrabBag: Component addition sequence started for '{name}'", "INFO")
        component = self.loader.get_component(name)
        if not component: 
            logger.error(f"GrabBag: Failed to load template for '{name}'")
            return
        
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"GrabBag: Publishing ADD_COMPONENT_REQUESTED event for '{name}' to path '{self.last_focused_path}'", "INFO")
        event_bus.publish("ADD_COMPONENT_REQUESTED", 
                          component_name=name, 
                          component_schema=component['schema'], 
                          target_path=self.last_focused_path,
                          source=self)
