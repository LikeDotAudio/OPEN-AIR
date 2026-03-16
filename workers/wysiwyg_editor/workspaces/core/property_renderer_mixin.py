import tkinter as tk
from tkinter import ttk
from ..core.state import state
from .leaf_editor_factory import LeafEditorFactory

class PropertyRendererMixin:
    """Handles the recursive generation of the properties UI tree."""

    def _render_recursive_properties(self, data, parent, prefix="", depth=0, actual_data=None):
        if actual_data is None: actual_data = {}
        if depth > 5:
            tk.Label(parent, text="... (Depth Limit Reached)", bg="#2b2b2b", fg="#ffaa00").pack(fill="x")
            return

        for key, value in data.items():
            full_path = f"{prefix}.{key}"
            is_virtual = (key not in actual_data)
            
            if isinstance(value, dict):
                self._render_section(parent, key, value, full_path, is_virtual, depth, actual_data)
            elif isinstance(value, list):
                self._render_list_info(parent, key, value)
            else:
                if is_virtual:
                    self._render_virtual_leaf(parent, key, value, full_path)
                else:
                    LeafEditorFactory.create(parent, key, value, full_path, self)

    def _render_section(self, parent, key, value, full_path, is_virtual, depth, actual_data):
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

        if is_virtual:
            tk.Button(h_frame, text="+ ADD SECTION", bg="#2ecc71", fg="white", relief="flat", font=("Arial", 6, "bold"),
                      command=lambda p=full_path, v=value: self._add_state_item(p, v)).pack(side="right", padx=5)
        else:
            if ".fields." in full_path or full_path.count(".") == 0:
                ctrl = tk.Frame(h_frame, bg="#3a3a3a")
                ctrl.pack(side="right", padx=5)
                ttk.Button(ctrl, text="↑", width=2, command=lambda p=full_path: self._reorder(p, "up")).pack(side="left", padx=1)
                ttk.Button(ctrl, text="↓", width=2, command=lambda p=full_path: self._reorder(p, "down")).pack(side="left", padx=1)
        
        child_container = tk.Frame(parent, bg="#2b2b2b", padx=15)
        child_container.pack(fill="x")
        
        def toggle(e):
            if is_expanded.get(): child_container.pack_forget(); toggle_lbl.config(text="▶"); is_expanded.set(False)
            else: child_container.pack(fill="x"); toggle_lbl.config(text="▼"); is_expanded.set(True)
        
        title_lbl.bind("<Button-1>", toggle); toggle_lbl.bind("<Button-1>", toggle)
        self._render_recursive_properties(value, child_container, prefix=full_path, depth=depth + 1, actual_data=actual_data.get(key, {}))

    def _render_list_info(self, parent, key, value):
        f = tk.Frame(parent, bg="#2b2b2b")
        f.pack(fill="x", pady=2)
        tk.Label(f, text=f"{key}:", bg="#2b2b2b", fg="#888888", width=15, anchor="e").pack(side="left")
        tk.Label(f, text=f"[List: {len(value)} items]", bg="#2b2b2b", fg="#666666").pack(side="left", padx=10)

    def _render_virtual_leaf(self, parent, key, value, full_path):
        f = tk.Frame(parent, bg="#2b2b2b")
        f.pack(fill="x", pady=2)
        tk.Label(f, text=f"{key}:", bg="#2b2b2b", fg="#555555", width=15, anchor="e").pack(side="left")
        tk.Button(f, text="+ ADD", bg="#3a3a3a", fg="#aaaaaa", relief="flat", font=("Arial", 7, "bold"),
                  command=lambda p=full_path, v=value: self._add_state_item(p, v)).pack(side="left", padx=10)
        tk.Label(f, text=f"({value})", bg="#2b2b2b", fg="#444444", font=("Arial", 7, "italic")).pack(side="left")

    def _add_state_item(self, path, value):
        state_manager.update_state(value, path=path, source=self)
        self._refresh_content()
