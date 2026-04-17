import inspect
from oaLogging.Methods.matrix_gate import matrix_log
# Interface/Tabs/GrabBagView/grab_bag_view.py
# Author: Gemini CLI
# Version: 1.0.1
#
# Description: The UI palette for the Grab Bag with categorization and layout tools.

import tkinter as tk
from tkinter import ttk
import copy
from ....FileReaders.grab_bag_loader import GrabBagLoader
from oaComBroker.Core.event_bus import event_bus
from ....Core.state import state_manager
from oaLogging.Core.logger import GUI_LOGGER as logger
from ...renderers.section_renderer import SectionRenderer

class AutoScrollbar(ttk.Scrollbar):
    """A scrollbar that hides itself when it's not needed."""
    def __init__(self, master=None, **kwargs):
        self.grid_kwargs = {}
        super().__init__(master, **kwargs)

    def grid(self, **kwargs):
        self.grid_kwargs.update(kwargs)
        super().grid(**kwargs)

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid(**self.grid_kwargs)
        ttk.Scrollbar.set(self, lo, hi)

class GrabBagView(tk.Frame):
    """A palette of draggable/selectable GUI components grouped by category."""

    def __init__(self, parent, library_cache=None, *args, **kwargs):
        kwargs.pop("bg", None)
        super().__init__(parent, bg="#2b2b2b", *args, **kwargs)
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🎨🎨🎨 [RENDER] GrabBagView: Initializing palette...", "DEBUG")
        self.loader = GrabBagLoader()
        self.library = library_cache if library_cache is not None else self.loader.scan_library()
        self.last_focused_path = None
        self._build_ui()
        
        # Track selection to know where to insert
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🎧👂🎧 [LISTENING] GrabBagView: Subscribing to FOCUS_REQUESTED...", "DEBUG")
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)
        
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event):
        if event.widget == self:
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🛑🛑🛑 [STOPPED] GrabBagView: Workspace destroyed. Cleaning up subscriptions.", "INFO")
            event_bus.unsubscribe("FOCUS_REQUESTED", self._on_focus_requested)
            
            # CRITICAL: Cleanup bind_all to prevent memory leaks and crashes on relaunch
            try:
                matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🧹🧹🧹 [SWEEPING] GrabBagView: Unbinding global mousewheel events...", "DEBUG")
                self.canvas.unbind_all("<MouseWheel>")
                self.canvas.unbind_all("<Button-4>")
                self.canvas.unbind_all("<Button-5>")
            except: pass

    def _on_focus_requested(self, path, source=None):
        self.last_focused_path = path

    def _build_ui(self):
        """Builds the Grab Bag UI."""
        header = tk.Frame(self, bg="#333333", height=35)
        header.pack(side="top", fill="x")
        
        tk.Label(header, text="GRAB BAG", bg="#333333", fg="white", 
                 font=("Arial", 9, "bold")).pack(side="left", padx=10, pady=5)
        
        ttk.Button(header, text="Refresh", command=self._refresh_library).pack(side="right", padx=5)

        # Main Workspace Container
        ws_container = tk.Frame(self, bg="#2b2b2b")
        ws_container.pack(fill="both", expand=True)
        ws_container.grid_rowconfigure(0, weight=1)
        ws_container.grid_columnconfigure(0, weight=1)

        # Scrollable area for components
        self.canvas = tk.Canvas(ws_container, bg="#2b2b2b", bd=0, highlightthickness=0)
        self.v_scrollbar = AutoScrollbar(ws_container, orient="vertical", command=self.canvas.yview)
        self.h_scrollbar = AutoScrollbar(ws_container, orient="horizontal", command=self.canvas.xview)
        
        self.scroll_frame = tk.Frame(self.canvas, bg="#2b2b2b")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        self.scroll_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

        self._refresh_library()

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=max(event.width, self.scroll_frame.winfo_reqwidth()))

    def _on_mousewheel(self, event):
        if not self.winfo_exists() or not self.canvas.winfo_viewable(): return
        if event.num == 4: delta = -1
        elif event.num == 5: delta = 1
        else: delta = int(-1 * (event.delta / 120))
        self.canvas.yview_scroll(delta, "units")

    def _refresh_library(self):
        """Reloads components and rebuilds the UI with categorization."""
        matrix_log("ui", "gui_builder", "grab_bag", "📦🔬🔍 [PACKAGE] Refreshing component library with grouping...", "INFO")
        for child in self.scroll_frame.winfo_children():
            child.destroy()
            
        library = self.loader.scan_library()
        
        # 1. 🏗️ LAYOUT TOOLS
        self._render_layout_tools_section()
        
        # 2. 📦 DYNAMIC COMPONENTS (Grouped by Category)
        categories = {}
        for name, info in library.items():
            cat = info.get("category", "General")
            if cat not in categories: categories[cat] = []
            categories[cat].append((name, info))
            
        for cat_name in sorted(categories.keys()):
            self._render_category_section(cat_name, categories[cat_name])

    def _render_layout_tools_section(self):
        """Renders the top-level section for structural generators."""
        self.tools_container = tk.Frame(self.scroll_frame, bg="#2b2b2b")
        
        def on_toggle(state):
            if state: self.tools_container.pack(fill="x", padx=15)
            else: self.tools_container.pack_forget()

        h_frame, is_expanded = SectionRenderer.render(self.scroll_frame, "Layout Tools", "layout_tools#header", True, True, on_toggle, lambda: None)
        self.tools_container.pack(fill="x", padx=15)
        
        tools = [
            ("Container", "OcaBlock", "Standard structural block"),
            ("Array", "OcaArray", "Repeatable widget collection"),
            ("Table (Grid)", "OcaTable", "Multi-column grid container"),
            ("Foldable", "OcaFoldableBlock", "Collapsible container"),
            ("Metal Folder", "OcaMetalFolder", "Styled industrial folder")
        ]
        
        for name, w_type, desc in tools:
            btn_frame = tk.Frame(self.tools_container, bg="#333333", bd=1, relief="raised", padx=10, pady=5)
            btn_frame.pack(fill="x", pady=2)
            
            lbl = tk.Label(btn_frame, text=name, bg="#333333", fg="#33A1FD", font=("Arial", 8, "bold"))
            lbl.pack(side="left")
            tk.Label(btn_frame, text=desc, bg="#333333", fg="#888888", font=("Arial", 7)).pack(side="left", padx=10)
            
            ttk.Button(btn_frame, text="PLACE", width=7, command=lambda t=w_type: self._generate_structure(t)).pack(side="right")

            # 🖱️ DRAG BINDINGS
            mock_info = {"schema": self._get_boilerplate(w_type)}
            for w in [btn_frame, lbl]:
                w.bind("<ButtonPress-1>", lambda e, n=name, i=mock_info: self._on_drag_start(e, n, i))
                w.bind("<B1-Motion>", self._on_drag_motion)
                w.bind("<ButtonRelease-1>", self._on_drag_stop)

    def _render_category_section(self, category_name, components):
        """Renders a collapsible section for a component category."""
        container_key = f"cat_{category_name}"
        cat_container = tk.Frame(self.scroll_frame, bg="#2b2b2b")
        
        def on_toggle(state):
            if state: cat_container.pack(fill="x", padx=15)
            else: cat_container.pack_forget()

        h_frame, is_expanded = SectionRenderer.render(self.scroll_frame, category_name, f"{container_key}#header", True, True, on_toggle, lambda: None)
        cat_container.pack(fill="x", padx=15)

        for name, info in sorted(components):
            comp_frame = tk.Frame(cat_container, bg="#333333", bd=1, relief="raised", padx=10, pady=5)
            comp_frame.pack(fill="x", pady=2)
            
            lbl = tk.Label(comp_frame, text=name, bg="#333333", fg="white", font=("Arial", 8))
            lbl.pack(side="left")
            tk.Label(comp_frame, text=f"({info['type']})", bg="#333333", fg="#888888", font=("Arial", 7)).pack(side="left", padx=5)
            
            btn = ttk.Button(comp_frame, text="PLACE", width=7, command=lambda n=name: self._add_component(n))
            btn.pack(side="right")

            # 🖱️ DRAG BINDINGS
            for w in [comp_frame, lbl]:
                w.bind("<ButtonPress-1>", lambda e, n=name, i=info: self._on_drag_start(e, n, i))
                w.bind("<B1-Motion>", self._on_drag_motion)
                w.bind("<ButtonRelease-1>", self._on_drag_stop)

    def _on_drag_start(self, event, name, info):
        """Initializes the drag operation with a visual proxy."""
        self.drag_data = {"name": name, "info": info}
        
        # Create a floating proxy window
        self.proxy = tk.Toplevel(self)
        self.proxy.overrideredirect(True)
        self.proxy.attributes("-topmost", True)
        self.proxy.attributes("-alpha", 0.7)
        
        tk.Label(self.proxy, text=name, bg="#33A1FD", fg="white", 
                 padx=10, pady=5, font=("Arial", 8, "bold")).pack()
        
        self._on_drag_motion(event)

    def _on_drag_motion(self, event):
        """Moves the proxy window with the mouse."""
        if hasattr(self, 'proxy'):
            x = event.x_root + 10
            y = event.y_root + 10
            self.proxy.geometry(f"+{x}+{y}")
            
            # Notify the system about the drag position
            event_bus.publish("COMPONENT_DRAGGING", 
                              x=event.x_root, 
                              y=event.y_root, 
                              name=self.drag_data["name"])

    def _on_drag_stop(self, event):
        """Finalizes the drag-and-drop operation."""
        if hasattr(self, 'proxy'):
            self.proxy.destroy()
            del self.proxy
            
            # Publish drop event
            matrix_log("ui", "gui_builder", "grab_bag", f"🎯🖱️🔨 [ACTION] GrabBag: Dropping component '{self.drag_data['name']}'", "INFO")
            event_bus.publish("COMPONENT_DROPPED", 
                              x=event.x_root, 
                              y=event.y_root, 
                              name=self.drag_data["name"],
                              schema=self.drag_data["info"]["schema"])
            self.drag_data = None

    def _get_boilerplate(self, w_type):
        """Returns the boilerplate schema for a structural element."""
        schema = {"type": w_type, "layout": {"sticky": "nsew"}}
        
        if w_type == "OcaBlock" or w_type == "OcaContainer":
            schema["fields"] = {}
        elif w_type == "OcaArray":
            schema.update({
                "blueprint": {"type": "OcaBlock", "fields": {}},
                "data": [{}, {}]
            })
        elif w_type == "OcaTable":
            schema.update({
                "columns": ["Col 1", "Col 2"],
                "rows": [
                    {"Col 1": {"type": "OcaText"}, "Col 2": {"type": "OcaText"}},
                    {"Col 1": {"type": "OcaText"}, "Col 2": {"type": "OcaText"}}
                ]
            })
        return schema

    def _generate_structure(self, w_type):
        """Generates complex structural boilerplates."""
        matrix_log("ui", "gui_builder", "grab_bag", f"🏗️⚙️🔨 [ACTION] GrabBag: Generating structural boilerplate for '{w_type}'", "INFO")
        schema = self._get_boilerplate(w_type)
        target = self._resolve_insertion_path()
        
        event_bus.publish("ADD_COMPONENT_REQUESTED", 
                          component_name=w_type, 
                          component_schema=schema, 
                          target_path=target,
                          source=self)

    def _add_component(self, name):
        """Adds component to state."""
        matrix_log("ui", "gui_builder", "grab_bag", f"🖱️🔨➕ [ACTION] GrabBag: Adding component '{name}' via button click.", "INFO")
        component = self.loader.get_component(name)
        if component:
            target = self._resolve_insertion_path()
            event_bus.publish("ADD_COMPONENT_REQUESTED", 
                              component_name=name, 
                              component_schema=component['schema'], 
                              target_path=target,
                              source=self)

    def _resolve_insertion_path(self):
        """Helper to find the best path for programmatic insertion (Button Clicks)."""
        path = self.last_focused_path
        
        if not path:
            # Default to root
            full_state = state_manager.get_state()
            if full_state:
                path = list(full_state.keys())[0]
            else:
                return "" # Pure root

        # Resolve container sub-path if needed
        val = state_manager.get_value_at_path(path)
        if isinstance(val, dict):
            w_type = val.get("type", "")
            if "Block" in w_type and "fields" not in path:
                return f"{path}.fields"
            if "Table" in w_type and "rows" not in path:
                return f"{path}.rows.0"
        
        return path
