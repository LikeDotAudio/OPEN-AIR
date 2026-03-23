# workspaces/tree_refactor.py
# Author: Gemini CLI
# Version: 1.0.0
#
# Description: A hierarchical Treeview for refactoring the GUI structure.

import tkinter as tk
from tkinter import ttk
from ..event_bus import event_bus
from ..state import state_manager

# --- Standard Debug Logging Setup ---
LOCAL_DEBUG = True    # Set to False in production, True for dev on this file
from oaLogging.Core.logger import GUI_LOGGER as logger

class TreeRefactor(ttk.Frame):
    """Hierarchical tree view for GUI structure refactoring."""

    def __init__(self, parent):
        self._setup_styles()
        super().__init__(parent, style="Dark.TFrame")
        self._build_ui()
        
        # Subscribe to state updates
        event_bus.subscribe("STATE_UPDATED", self._on_state_updated)
        
        # Internal state
        self._dragging_item = None

    def _setup_styles(self):
        """Configures the dark mode styles for the Treeview and containers."""
        style = ttk.Style()
        
        # Dark Frame
        style.configure("Dark.TFrame", background="#2b2b2b")
        
        # Dark Treeview
        style.configure("Treeview",
            background="#1a1a1a",
            foreground="#dcdcdc",
            fieldbackground="#1a1a1a",
            borderwidth=0,
            font=("Segoe UI", 9)
        )
        style.map("Treeview",
            background=[('selected', '#33A1FD')],
            foreground=[('selected', 'white')]
        )
        
        # Dark Treeview Heading
        style.configure("Treeview.Heading",
            background="#333333",
            foreground="#888888",
            relief="flat",
            font=("Segoe UI", 9, "bold")
        )
        style.map("Treeview.Heading",
            background=[('active', '#444444')]
        )

    def _build_ui(self):
        """Creates the Treeview and control buttons."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Main Treeview
        self.tree_container = ttk.Frame(self, style="Dark.TFrame")
        self.tree_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.tree_container.grid_rowconfigure(0, weight=1)
        self.tree_container.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(self.tree_container, selectmode="browse", style="Treeview")
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Define Columns (hidden values)
        self.tree["columns"] = ("path", "type")
        self.tree.column("#0", width=300, minwidth=200)
        self.tree.column("path", width=0, stretch=tk.NO)
        self.tree.column("type", width=0, stretch=tk.NO)
        self.tree.heading("#0", text="GUI Hierarchy", anchor="w")
        
        # Scrollbar for Tree
        tree_scroll = ttk.Scrollbar(self.tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.grid(row=0, column=1, sticky="ns")

        # 2. Control Buttons
        self.btn_frame = ttk.Frame(self, style="Dark.TFrame")
        self.btn_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        ttk.Button(self.btn_frame, text="▲ UP", command=self._move_up, width=8).pack(side="left", padx=2)
        ttk.Button(self.btn_frame, text="▼ DOWN", command=self._move_down, width=8).pack(side="left", padx=2)
        
        # Delete button with warning style
        delete_btn = tk.Button(self.btn_frame, text="DELETE", bg="#e74c3c", fg="white", 
                               font=("Arial", 8, "bold"), relief="flat", padx=10,
                               command=self._delete_item)
        delete_btn.pack(side="right", padx=5)

        # 3. Instruction Label
        tk.Label(self, text="Tip: Drag & Drop to move items between containers", 
                  font=("Helvetica", 8, "italic"), bg="#2b2b2b", fg="#888888").grid(row=2, column=0, sticky="w", padx=10, pady=(0,5))

        # --- Drag and Drop Bindings ---
        self.tree.bind("<ButtonPress-1>", self._on_drag_start)
        self.tree.bind("<B1-Motion>", self._on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self._on_drag_stop)
        
        # Selection binding for focus sync
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _on_state_updated(self, json_data, source=None):
        """Refreshes the tree when the master state changes."""
        if source == self: return # Avoid infinite loops
        
        # Save selection and open states if possible
        # (Implementing a full sync is complex, so we'll do a simple clear/rebuild)
        self.tree.delete(*self.tree.get_children())
        self._populate_tree("", json_data)

    def _populate_tree(self, parent_node, data):
        """Recursively populates the tree from JSON data."""
        
        # Handle List (e.g. OcaArray.data)
        if isinstance(data, list):
            for i, val in enumerate(data):
                node_text = f"[{i}]"
                node_type = "Data"
                
                # Heuristic: try to find an id or description for the list item
                if isinstance(val, dict):
                    node_type = val.get("id", val.get("type", "Item"))
                    node_text = f"[{i}] {val.get('description', val.get('id', 'Item'))}"

                # Path construction for list item
                parent_path = ""
                if parent_node != "":
                    p_info = self.tree.item(parent_node, "values")
                    if p_info: parent_path = p_info[0]
                
                full_path = f"{parent_path}.{i}" if parent_path else str(i)
                
                node_id = self.tree.insert(parent_node, "end", text=node_text, values=(full_path, node_type))
                if isinstance(val, (dict, list)):
                    self._populate_tree(node_id, val)
            return

        if not isinstance(data, dict): return

        # Determine container items based on standard keys
        items = []
        
        # Standard Container Keys
        container_keys = ["fields", "items", "blueprint", "data"]
        
        # If it's the root, just iterate everything
        if parent_node == "":
            for k, v in data.items():
                items.append((k, v, k))
        else:
            # Check for standard containers
            for ck in container_keys:
                if ck in data:
                    val = data[ck]
                    items.append((ck, val, ck))
            
            # If NO standard container keys found, and it's not a leaf (widgets might be leaves)
            # This is a fallback for custom structures
            if not items and any(isinstance(v, (dict, list)) for v in data.values()):
                # Exclude internal metadata if any
                exclude = ["type", "description", "layout", "geometry", "domain", "dynamics", "cosmetics"]
                for k, v in data.items():
                    if k not in exclude and isinstance(v, (dict, list)):
                        items.append((k, v, k))

        for key, val, relative_path in items:
            node_text = key
            node_type = "Element"
            
            if isinstance(val, dict):
                node_type = val.get("type", "Block")
                node_text = f"{key} ({node_type})"
            
            # Full path for state manager operations
            parent_path = ""
            if parent_node != "":
                p_info = self.tree.item(parent_node, "values")
                if p_info: parent_path = p_info[0]
            
            full_path = f"{parent_path}.{relative_path}" if parent_path else relative_path

            node_id = self.tree.insert(parent_node, "end", text=node_text, values=(full_path, node_type))
            
            # Recurse if it's a container
            if isinstance(val, (dict, list)):
                self._populate_tree(node_id, val)

    def _on_tree_select(self, event):
        """Syncs selection with the global focus."""
        selected = self.tree.selection()
        if not selected: return
        
        path = self.tree.item(selected[0], "values")[0]
        event_bus.publish("FOCUS_REQUESTED", path=path, source=self)

    def _move_up(self):
        selected = self.tree.selection()
        if not selected: return
        
        path = self.tree.item(selected[0], "values")[0]
        state_manager.reorder_element(path, "up", source=self)
        self._refresh_after_op()

    def _move_down(self):
        selected = self.tree.selection()
        if not selected: return
        
        path = self.tree.item(selected[0], "values")[0]
        state_manager.reorder_element(path, "down", source=self)
        self._refresh_after_op()

    def _delete_item(self):
        selected = self.tree.selection()
        if not selected: return
        
        path = self.tree.item(selected[0], "values")[0]
        if tk.messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{path}'?"):
            state_manager.delete_element(path, source=self)
            self._refresh_after_op()

    def _refresh_after_op(self):
        """Manually triggers a tree rebuild after a local operation."""
        self._on_state_updated(state_manager.get_state())

    # --- Drag and Drop Logic ---
    
    def _on_drag_start(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self._dragging_item = item

    def _on_drag_motion(self, event):
        if self._dragging_item:
            # Optional: Visual feedback during drag
            pass

    def _on_drag_stop(self, event):
        if not self._dragging_item: return
        
        target_item = self.tree.identify_row(event.y)
        if not target_item: 
            self._dragging_item = None
            return

        if target_item == self._dragging_item:
            self._dragging_item = None
            return

        source_path = self.tree.item(self._dragging_item, "values")[0]
        target_parent_path = self.tree.item(target_item, "values")[0]
        
        # Logic: If target is a container (Block), move INTO it. 
        # If target is an element, move INTO its parent.
        target_type = self.tree.item(target_item, "values")[1]
        
        # Check if we are moving a child into its own parent (redundant)
        source_parent_path = ".".join(source_path.split(".")[:-1])
        
        # If target is NOT a block, move to target's parent
        if "Block" not in target_type and "Array" not in target_type:
            target_parent_path = ".".join(target_parent_path.split(".")[:-1])

        if target_parent_path == source_parent_path:
            logger.info("🌳 TreeRefactor: Drop target is same as source parent. Use UP/DOWN buttons for reordering.")
        else:
            # Perform Move
            # Note: We need to append '.fields' if target is a Block to match our schema
            target_val = state_manager.get_value_at_path(target_parent_path)
            if isinstance(target_val, dict) and "type" in target_val:
                if "Block" in target_val.get("type", ""):
                    target_parent_path = f"{target_parent_path}.fields"
            
            state_manager.move_element(source_path, target_parent_path, source=self)
            self._refresh_after_op()

        self._dragging_item = None
