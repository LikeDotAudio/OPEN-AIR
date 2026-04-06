# Core/property_renderer_mixin.py
# Author: Anthony Peter Kuzub
# Version: 1.0.0
#
# Description: Brief summary of purpose

import tkinter as tk
from tkinter import ttk
from ...state import state_manager
from .leaf_editor_factory import LeafEditorFactory

class PropertyRendererMixin:
    """Handles the recursive generation of the properties UI tree."""

    def __init__(self):
        super().__init__()
        self.widget_cache = {} # Cache to store rendered widgets by path

    def _render_recursive_properties(self, data, parent, prefix="", depth=0, actual_data=None, widget_cache=None, new_widget_cache=None):
        if actual_data is None: actual_data = {}
        if widget_cache is None: widget_cache = {}
        if new_widget_cache is None: new_widget_cache = {}

        if depth > 5:
            tk.Label(parent, text="... (Depth Limit Reached)", bg="#2b2b2b", fg="#ffaa00").pack(fill="x")
            return



        for key, value in data.items():
            full_path = f"{prefix}.{key}"
            is_virtual = (key not in actual_data)
            
            # Check if a widget for this path already exists in the cache
            existing_widget_info = widget_cache.get(full_path)
            existing_widget = existing_widget_info.get("widget") if existing_widget_info else None
            
            # 🛡️ VALIDATION: If the widget has been destroyed in Tkinter, treat it as None
            if existing_widget and not existing_widget.winfo_exists():
                existing_widget = None
                widget_cache.pop(full_path, None)
            
            if isinstance(value, dict):
                # Check if the schema type has changed for this section
                schema_type_changed = (
                    existing_widget_info is None or
                    value.get("type", value.get("widget_type")) != existing_widget_info.get("schema_type")
                )
                
                # Reuse or create child_container
                child_container = None
                if existing_widget and not schema_type_changed:
                    child_container = existing_widget # Assuming existing_widget is the container
                else:
                    # If section structure changed or it's new, destroy old and create new
                    if existing_widget: # Destroy old section widget if it was a container
                         # Ensure proper cleanup if it was a frame or similar
                        if hasattr(existing_widget, 'destroy'):
                            existing_widget.destroy()
                        # Remove from cache
                        widget_cache.pop(full_path, None)
                    child_container = tk.Frame(parent, bg="#2b2b2b", padx=15)
                    child_container.pack(fill="x")
                    widget_cache[full_path] = {"widget": child_container, "schema_type": value.get("type", value.get("widget_type"))}

                self._render_section(parent, key, value, full_path, is_virtual, depth, actual_data, child_container, widget_cache, new_widget_cache)
            
            elif isinstance(value, list):
                self._render_list_info(parent, key, value, full_path, existing_widget, widget_cache, new_widget_cache)
            else:
                # Handle leaf properties
                if is_virtual:
                    self._render_virtual_leaf(parent, key, value, full_path, existing_widget, widget_cache, new_widget_cache)
                else:
                    # Try to update existing leaf widget or create a new one
                    editor_widget = LeafEditorFactory.create(parent, key, value, full_path, self, existing_widget=existing_widget)
                    if new_widget_cache is not None:
                        new_widget_cache[full_path] = {"widget": editor_widget}


        



    def _render_section(self, parent, key, value, full_path, is_virtual, depth, actual_data, child_container=None, widget_cache=None, new_widget_cache=None):
        
        h_frame = tk.Frame(parent, bg="#3a3a3a", pady=2)
        h_frame.pack(fill="x", pady=(5, 2))
        
        is_expanded = tk.BooleanVar(value=True)
        
        w_type = value.get("type", value.get("widget_type", ""))
        type_emoji = "📦" if w_type == "OcaBlock" else "🔹"
        fg_col = "#aaaaaa" if not is_virtual else "#666666"
        
        toggle_lbl = tk.Label(h_frame, text="▼", bg="#3a3a3a", fg="#33A1FD", font=("Arial", 8))
        toggle_lbl.pack(side="left", padx=(5, 2))
        tk.Label(h_frame, text=type_emoji, bg="#3a3a3a", font=("Arial", 8)).pack(side="left", padx=(0, 5))
        title_lbl = tk.Label(h_frame, text=key.upper(), bg="#3a3a3a", fg=fg_col, font=("Arial", 8, "bold"), cursor="hand2")
        title_lbl.pack(side="left")

        # Store the header frame itself as the "widget" for this section in the cache
        if new_widget_cache is not None:
            new_widget_cache[full_path] = {"widget": h_frame, "schema_type": w_type}

        if is_virtual:
            tk.Button(h_frame, text="+ ADD SECTION", bg="#2ecc71", fg="white", relief="flat", font=("Arial", 6, "bold"),
                      command=lambda p=full_path, v=value: self._add_state_item(p, v)).pack(side="right", padx=5)
        else:
            # Add reorder buttons if applicable (e.g., within .fields. or root level)
            if ".fields." in full_path or full_path.count(".") == 0:
                ctrl = tk.Frame(h_frame, bg="#3a3a3a")
                ctrl.pack(side="right", padx=5)
                ttk.Button(ctrl, text="↑", width=2, command=lambda p=full_path: self._reorder(p, "up")).pack(side="left", padx=1)
                ttk.Button(ctrl, text="↓", width=2, command=lambda p=full_path: self._reorder(p, "down")).pack(side="left", padx=1)
        
        # Child container logic: Reuse if possible, create if not or if schema changed
        if child_container is None: # Create if it doesn't exist from parent's cache
            child_container = tk.Frame(parent, bg="#2b2b2b", padx=15)
            child_container.pack(fill="x")
            
        # Store the child_container for potential reuse by the recursive call
        if new_widget_cache is not None:
            new_widget_cache[full_path] = {"widget": child_container, "schema_type": w_type}

        def toggle(e):
            if is_expanded.get(): child_container.pack_forget(); toggle_lbl.config(text="▶"); is_expanded.set(False)
            else: child_container.pack(fill="x"); toggle_lbl.config(text="▼"); is_expanded.set(True)
        
        title_lbl.bind("<Button-1>", toggle); toggle_lbl.bind("<Button-1>", toggle)
        
        # Recursive call, passing down the cache and ensuring child_container is provided
        self._render_recursive_properties(value, child_container, prefix=full_path, depth=depth + 1, actual_data=actual_data.get(key, {}), widget_cache=widget_cache, new_widget_cache=new_widget_cache)

    def _render_list_info(self, parent, key, value, full_path, existing_widget=None, widget_cache=None, new_widget_cache=None):
        # For lists, we might not have complex widgets to cache or update.
        # If a list property changes, we might need to rebuild its representation.
        # For now, we'll treat it like a simple leaf and potentially update text.
        f = tk.Frame(parent, bg="#2b2b2b")
        f.pack(fill="x", pady=2)
        tk.Label(f, text=f"{key}:", bg="#2b2b2b", fg="#888888", width=15, anchor="e").pack(side="left")
        list_text = f"[List: {len(value)} items]"
        
        if existing_widget and isinstance(existing_widget, tk.Label):
            existing_widget.config(text=list_text)
            if new_widget_cache is not None:
                new_widget_cache[full_path] = {"widget": existing_widget}
        else:
            lbl = tk.Label(f, text=list_text, bg="#2b2b2b", fg="#666666")
            lbl.pack(side="left", padx=10)
            if new_widget_cache is not None:
                new_widget_cache[full_path] = {"widget": lbl}

    def _render_virtual_leaf(self, parent, key, value, full_path, existing_widget=None, widget_cache=None, new_widget_cache=None):
        f = tk.Frame(parent, bg="#2b2b2b")
        f.pack(fill="x", pady=2)
        tk.Label(f, text=f"{key}:", bg="#2b2b2b", fg="#555555", width=15, anchor="e").pack(side="left")
        
        # Add button logic: if it exists, update it, else create it.
        if existing_widget and isinstance(existing_widget, tk.Button) and existing_widget.cget("text") == "+ ADD":
            # It's an existing ADD button, no need to recreate. Just ensure it's cached.
            pass # Already exists, no action needed for the button itself.
        else:
            # Create a new ADD button if it doesn't exist or is not the right type.
            add_button = tk.Button(f, text="+ ADD", bg="#3a3a3a", fg="#aaaaaa", relief="flat", font=("Arial", 7, "bold"),
                                   command=lambda p=full_path, v=value: self._add_state_item(p, v))
            add_button.pack(side="left", padx=10)
            existing_widget = add_button # Update existing_widget to the new button if created

        tk.Label(f, text=f"({value})", bg="#2b2b2b", fg="#444444", font=("Arial", 7, "italic")).pack(side="left")

        if new_widget_cache is not None and existing_widget:
            new_widget_cache[full_path] = {"widget": existing_widget}

    def _add_state_item(self, path, value):
        state_manager.update_state(value, path=path, source=self)
        # Refresh content to reflect the added item
        if hasattr(self, '_refresh_content'): # Ensure method exists in context
            self._refresh_content()

    # Placeholder for reorder functionality, assuming it exists in a mixin
    def _reorder(self, path, direction):
        print(f"Reordering {path} {direction}") # Placeholder

# --- The following methods were in the original PropertyRendererMixin and are kept ---

    # def _render_recursive_properties(self, data, parent, prefix="", depth=0, actual_data=None): # Original signature
    #     if actual_data is None: actual_data = {}
    #     if depth > 5:
    #         tk.Label(parent, text="... (Depth Limit Reached)", bg="#2b2b2b", fg="#ffaa00").pack(fill="x")
    #         return

    #     for key, value in data.items():
    #         full_path = f"{prefix}.{key}"
    #         is_virtual = (key not in actual_data)
            
    #         if isinstance(value, dict):
    #             self._render_section(parent, key, value, full_path, is_virtual, depth, actual_data)
    #         elif isinstance(value, list):
    #             self._render_list_info(parent, key, value)
    #         else:
    #             if is_virtual:
    #                 self._render_virtual_leaf(parent, key, value, full_path)
    #             else:
    #                 LeafEditorFactory.create(parent, key, value, full_path, self)

    # def _render_section(self, parent, key, value, full_path, is_virtual, depth, actual_data): # Original signature
    #     h_frame = tk.Frame(parent, bg="#3a3a3a", pady=2)
    #     h_frame.pack(fill="x", pady=(5, 2))
    #     is_expanded = tk.BooleanVar(value=True)
        
    #     w_type = value.get("type", value.get("widget_type", ""))
    #     type_emoji = "📦" if w_type == "OcaBlock" else "🔹"
    #     fg_col = "#aaaaaa" if not is_virtual else "#666666"
        
    #     toggle_lbl = tk.Label(h_frame, text="▼", bg="#3a3a3a", fg="#33A1FD", font=("Arial", 8))
    #     toggle_lbl.pack(side="left", padx=(5, 2))
    #     tk.Label(h_frame, text=type_emoji, bg="#3a3a3a", font=("Arial", 8)).pack(side="left", padx=(0, 5))
    #     title_lbl = tk.Label(h_frame, text=key.upper(), bg="#3a3a3a", fg=fg_col, font=("Arial", 8, "bold"), cursor="hand2")
    #     title_lbl.pack(side="left")

    #     if is_virtual:
    #         tk.Button(h_frame, text="+ ADD SECTION", bg="#2ecc71", fg="white", relief="flat", font=("Arial", 6, "bold"),
    #                   command=lambda p=full_path, v=value: self._add_state_item(p, v)).pack(side="right", padx=5)
    #     else:
    #         if ".fields." in full_path or full_path.count(".") == 0:
    #             ctrl = tk.Frame(h_frame, bg="#3a3a3a")
    #             ctrl.pack(side="right", padx=5)
    #             ttk.Button(ctrl, text="↑", width=2, command=lambda p=full_path: self._reorder(p, "up")).pack(side="left", padx=1)
    #             ttk.Button(ctrl, text="↓", width=2, command=lambda p=full_path: self._reorder(p, "down")).pack(side="left", padx=1)
        
    #     child_container = tk.Frame(parent, bg="#2b2b2b", padx=15)
    #     child_container.pack(fill="x")
        
    #     def toggle(e):
    #         if is_expanded.get(): child_container.pack_forget(); toggle_lbl.config(text="▶"); is_expanded.set(False)
    #         else: child_container.pack(fill="x"); toggle_lbl.config(text="▼"); is_expanded.set(True)
        
    #     title_lbl.bind("<Button-1>", toggle); toggle_lbl.bind("<Button-1>", toggle)
    #     self._render_recursive_properties(value, child_container, prefix=full_path, depth=depth + 1, actual_data=actual_data.get(key, {}))

    # def _render_list_info(self, parent, key, value): # Original signature
    #     f = tk.Frame(parent, bg="#2b2b2b")
    #     f.pack(fill="x", pady=2)
    #     tk.Label(f, text=f"{key}:", bg="#2b2b2b", fg="#888888", width=15, anchor="e").pack(side="left")
    #     tk.Label(f, text=f"[List: {len(value)} items]", bg="#2b2b2b", fg="#666666").pack(side="left", padx=10)

    # def _render_virtual_leaf(self, parent, key, value, full_path): # Original signature
    #     f = tk.Frame(parent, bg="#2b2b2b")
    #     f.pack(fill="x", pady=2)
    #     tk.Label(f, text=f"{key}:", bg="#2b2b2b", fg="#555555", width=15, anchor="e").pack(side="left")
    #     tk.Button(f, text="+ ADD", bg="#3a3a3a", fg="#aaaaaa", relief="flat", font=("Arial", 7, "bold"),
    #               command=lambda p=full_path, v=value: self._add_state_item(p, v)).pack(side="left", padx=10)
    #     tk.Label(f, text=f"({value})", bg="#2b2b2b", fg="#444444", font=("Arial", 7, "italic")).pack(side="left")

    # def _add_state_item(self, path, value): # Original signature
    #     state_manager.update_state(value, path=path, source=self)
    #     self._refresh_content()
