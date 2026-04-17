# oaGuiEditorWYSIWYG/Interface/renderers/tree_renderer.py
# Author: Anthony Peter Kuzub
# Version: 20260416.01.0
#
# Description: Core recursive engine for rendering the property tree.

import tkinter as tk
from ..factories.leaf_editor_factory import LeafEditorFactory
from .section_renderer import SectionRenderer
from .info_renderer import InfoRenderer

class TreeRenderer:
    """Orchestrates the recursive generation of the property UI."""

    @staticmethod
    def render_recursive(data, parent, prefix="", depth=0, actual_data=None, widget_cache=None, new_widget_cache=None, mixin_ref=None):
        """
        Recursively renders property editors and sections.
        """
        if actual_data is None: actual_data = {}
        if widget_cache is None: widget_cache = {}
        if new_widget_cache is None: new_widget_cache = {}

        if depth > 5:
            tk.Label(parent, text="... (Depth Limit Reached)", bg="#2b2b2b", fg="#ffaa00").pack(fill="x")
            return

        # 🛡️ TYPE GUARD: Ensure data is a dictionary
        if not isinstance(data, dict):
            if isinstance(data, list):
                f = InfoRenderer.render_list(parent, "LIST_CONTENT", data)
                new_widget_cache[f"{prefix}.LIST"] = {"widget": f}
            return

        for key, value in data.items():
            full_path = f"{prefix}.{key}"
            is_virtual = (key not in actual_data)

            # Special handling for language fields under 'text'
            if key == 'text' and isinstance(value, dict):
                lang_container = tk.Frame(parent, bg="#2b2b2b")
                lang_container.pack(fill="x", pady=2, padx=15)
                tk.Label(lang_container, text="Text Content:", bg="#2b2b2b", fg="#888888").pack(fill="x", anchor="w")

                editors_frame = tk.Frame(lang_container, bg="#2b2b2b")
                editors_frame.pack(fill="x")

                for lang_key, lang_value in value.items():
                    lang_full_path = f"{full_path}.{lang_key}"
                    row_frame = tk.Frame(editors_frame, bg="#2b2b2b")
                    row_frame.pack(fill="x", side="top")
                    
                    editor_widget = LeafEditorFactory.create(row_frame, lang_key, lang_value, lang_full_path, mixin_ref)
                    new_widget_cache[lang_full_path] = {"widget": editor_widget}
                continue

            existing_widget_info = widget_cache.get(full_path)
            existing_widget = existing_widget_info.get("widget") if existing_widget_info else None
            
            if existing_widget and not existing_widget.winfo_exists():
                existing_widget = None
                widget_cache.pop(full_path, None)
            
            if isinstance(value, dict):
                schema_type_changed = (
                    existing_widget_info is None or
                    value.get("type", value.get("widget_type")) != existing_widget_info.get("schema_type")
                )
                
                child_container = None
                if existing_widget and not schema_type_changed:
                    child_container = existing_widget
                else:
                    if existing_widget:
                        if hasattr(existing_widget, 'destroy'): existing_widget.destroy()
                        widget_cache.pop(full_path, None)
                    child_container = tk.Frame(parent, bg="#2b2b2b", padx=15)
                    child_container.pack(fill="x")
                
                new_widget_cache[full_path] = {
                    "widget": child_container, 
                    "schema_type": value.get("type", value.get("widget_type"))
                }

                TreeRenderer._render_section_with_header(parent, key, value, full_path, is_virtual, depth, actual_data, child_container, widget_cache, new_widget_cache, mixin_ref)
            
            elif isinstance(value, list):
                if existing_widget and existing_widget.winfo_exists(): existing_widget.destroy()
                f = InfoRenderer.render_list(parent, key, value)
                new_widget_cache[full_path] = {"widget": f}
            else:
                if is_virtual:
                    if existing_widget and existing_widget.winfo_exists(): existing_widget.destroy()
                    f = InfoRenderer.render_virtual_leaf(parent, key, value, lambda p=full_path, v=value: mixin_ref._add_state_item(p, v))
                    new_widget_cache[full_path] = {"widget": f}
                else:
                    editor_widget = LeafEditorFactory.create(parent, key, value, full_path, mixin_ref, existing_widget=existing_widget)
                    new_widget_cache[full_path] = {"widget": editor_widget}

    @staticmethod
    def _render_section_with_header(parent, key, value, full_path, is_virtual, depth, actual_data, child_container, widget_cache, new_widget_cache, mixin_ref):
        header_key = full_path + "#header"
        existing_header_info = widget_cache.get(header_key)
        
        is_expanded_val = True
        if existing_header_info and "is_expanded" in existing_header_info:
            is_expanded_val = existing_header_info["is_expanded"].get()
            
        existing_header = existing_header_info.get("widget") if existing_header_info else None
        if existing_header and existing_header.winfo_exists():
            existing_header.destroy()
            
        def on_toggle(new_state):
            if not child_container.winfo_exists(): return
            if new_state: child_container.pack(fill="x")
            else: child_container.pack_forget()

        def on_add():
            mixin_ref._add_state_item(full_path, value)

        h_frame, is_expanded = SectionRenderer.render(parent, key, full_path, is_virtual, is_expanded_val, on_toggle, on_add)
        
        if not is_expanded_val:
            child_container.pack_forget()

        new_widget_cache[header_key] = {"widget": h_frame, "is_expanded": is_expanded}
        
        TreeRenderer.render_recursive(value, child_container, prefix=full_path, depth=depth + 1, actual_data=actual_data.get(key, {}), widget_cache=widget_cache, new_widget_cache=new_widget_cache, mixin_ref=mixin_ref)
