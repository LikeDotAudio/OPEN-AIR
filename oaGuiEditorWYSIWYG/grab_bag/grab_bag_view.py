# grab_bag/grab_bag_view.py
# Author: Gemini CLI
# Version: 1.0.0
#
# Description: The UI palette for the Grab Bag.

import tkinter as tk
from tkinter import ttk
import copy
from .grab_bag_loader import GrabBagLoader
from ..Core.event_bus import event_bus
from ..Core.state import state_manager
from oaLogging.Core.logger import initialize_logging, set_log_directory
from loguru import logger

LOCAL_DEBUG = True    # Set to False in production, True for dev on this file


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

    def __init__(self, parent, *args, **kwargs):
        kwargs.pop("bg", None)
        super().__init__(parent, bg="#2b2b2b", *args, **kwargs)
        if LOCAL_DEBUG: logger.debug("🎒 GrabBagView: Initializing palette...")
        self.loader = GrabBagLoader()
        self.last_focused_path = None
        self._build_ui()
        
        # Track selection to know where to insert
        if LOCAL_DEBUG: logger.debug("🎒 GrabBagView: Subscribing to FOCUS_REQUESTED...")
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)
        
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event):
        if event.widget == self:
            if LOCAL_DEBUG: logger.info("🎒 GrabBagView: Workspace destroyed. Cleaning up subscriptions and bindings.")
            event_bus.unsubscribe("FOCUS_REQUESTED", self._on_focus_requested)
            
            # ⚡ CRITICAL: Cleanup bind_all to prevent memory leaks and crashes on relaunch
            try:
                if LOCAL_DEBUG: logger.debug("🎒 GrabBagView: Unbinding global mousewheel events...")
                self.canvas.unbind_all("<MouseWheel>")
                self.canvas.unbind_all("<Button-4>")
                self.canvas.unbind_all("<Button-5>")
            except: pass

    def _on_focus_requested(self, path, source=None):
        self.last_focused_path = path
        # logger.debug(f"🎒 GrabBag: Tracking focus path for insertion: {path}")

    def _build_ui(self):
        """Builds the Grab Bag UI."""
        if LOCAL_DEBUG: logger.debug("🎒 GrabBagView: Building Palette UI...")
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
        if LOCAL_DEBUG: logger.debug("🎒 GrabBagView: Binding global mousewheel...")
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
        if LOCAL_DEBUG: logger.info("🎒 GrabBag: Refreshing component library from disk...")
        for child in self.scroll_frame.winfo_children():
            child.destroy()
            
        library = self.loader.scan_library()
        if LOCAL_DEBUG: logger.info(f"🎒 GrabBag: Scan complete. Found {len(library)} component templates.")
        
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
        if LOCAL_DEBUG: logger.info(f"🎒 GrabBag: Component addition sequence started for '{name}'")
        component = self.loader.get_component(name)
        if not component: 
            logger.error(f"❌ GrabBag: Failed to load template for '{name}'")
            return
        
        current_state = state_manager.get_state()
        
        # 1. Determine parent container and target insertion index
        parent_path_parts = []
        target_field_key = None
        
        if self.last_focused_path:
            parts = self.last_focused_path.split(".")
            target_field_key = parts[-1]
            parent_path_parts = parts[:-1] # Usually ends in ".fields"
            if LOCAL_DEBUG: logger.debug(f"🎒 GrabBag: Insertion point identified: {target_field_key} within {'.'.join(parent_path_parts)}")
        else:
            if LOCAL_DEBUG: logger.debug("🎒 GrabBag: No insertion point selected. Adding to root.")
        
        # 2. Resolve the parent dictionary
        parent_dict = current_state
        if parent_path_parts:
            for part in parent_path_parts:
                parent_dict = parent_dict.get(part, {})
        
        # 3. Create a NEW dictionary with the item inserted in the correct position
        if isinstance(parent_dict, dict):
            new_fields = {}
            base_key = f"new_{component['folder'].replace('builder_', '')}"
            new_key = base_key
            counter = 1
            while new_key in parent_dict:
                new_key = f"{base_key}_{counter}"
                counter += 1
            
            if LOCAL_DEBUG: logger.debug(f"🎒 GrabBag: Generated unique key: '{new_key}'")

            inserted = False
            for k, v in parent_dict.items():
                new_fields[k] = v
                if k == target_field_key:
                    if LOCAL_DEBUG: logger.debug(f"🎒 GrabBag: Splicing '{new_key}' after '{k}'")
                    new_fields[new_key] = copy.deepcopy(component['schema'])
                    inserted = True
            
            if not inserted:
                if LOCAL_DEBUG: logger.debug(f"🎒 GrabBag: Appending '{new_key}' to end of dictionary.")
                new_fields[new_key] = copy.deepcopy(component['schema'])
            
            # 4. Update the state at the parent level
            state_manager.update_state(new_fields, path=parent_path_parts if parent_path_parts else None, source=self)
            if LOCAL_DEBUG: logger.success(f"✅ GrabBag: Successfully inserted '{new_key}'.")
        else:
            logger.error("❌ GrabBag Error: Resolved parent container is not a dictionary.")
