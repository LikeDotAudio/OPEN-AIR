# Interface/Tabs/JsonEditor/json_editor.py
import tkinter as tk
from tkinter import ttk
from tkinter import colorchooser
import orjson
import re
import inspect
from oaComBroker.Core.event_bus import event_bus
from ....Core.state import state_manager

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import GUI_LOGGER as logger
from oaLogging.Methods.matrix_gate import matrix_log

# --- JSON Tree Workspace ---
class JsonTreeWorkspace(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, bg="#1e1e1e", *args, **kwargs)
        self.current_json_data = {}
        self._build_ui()
        event_bus.subscribe("STATE_UPDATED", self._on_state_updated)
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)
        current_state = state_manager.get_state()
        if current_state: self._on_state_updated(current_state)

    def _on_focus_requested(self, path, source=None):
        """Syncs the tree selection when an element is focused elsewhere."""
        if source == self or not path: return
        
        # Paths in this tree are prefixed with 'root.' based on _populate_tree
        # but the node_id logic in _populate_tree is:
        # node_id = f"{path}.{key}" if path else str(key)
        
        # We need to find the node that matches the path. 
        # Since _populate_tree uses the actual data keys, we can try to find it.
        # Let's check if the path exists in the tree.
        if self.tree.exists(path):
            self.tree.selection_set(path)
            self.tree.see(path)
        elif self.tree.exists(f"root.{path}"):
            self.tree.selection_set(f"root.{path}")
            self.tree.see(f"root.{path}")

    def _build_ui(self):
        # 1. Header with Level Controls
        header = tk.Frame(self, bg="#333333", height=30)
        header.pack(side="top", fill="x")
        
        tk.Label(header, text="STRUCTURE", bg="#333333", fg="white", font=("Arial", 8, "bold")).pack(side="left", padx=10)
        
        btn_frame = tk.Frame(header, bg="#333333")
        btn_frame.pack(side="right", padx=5)
        
        # Level Buttons
        for lvl in [3, 4, 5, 6]:
            btn = tk.Button(btn_frame, text=f"L{lvl}", bg="#444444", fg="#dcdcdc", relief="flat", 
                            font=("Arial", 7), width=3, command=lambda level=lvl: self._expand_to_level(level))
            btn.pack(side="left", padx=2)
        
        tk.Button(btn_frame, text="EXPAND ALL", bg="#444444", fg="#00ffcc", relief="flat",
                  font=("Arial", 7, "bold"), command=lambda: self._expand_to_level(99), padx=5).pack(side="left", padx=2)

        # 2. Main Tree Area
        self.paned = ttk.PanedWindow(self, orient="vertical")
        self.paned.pack(fill="both", expand=True)
        tree_frame = tk.Frame(self.paned, bg="#1e1e1e")
        self.paned.add(tree_frame, weight=3)
        
        # Add Scrollbars to Treeview (No "value" column as requested)
        self.tree = ttk.Treeview(tree_frame, columns=(), selectmode="browse")
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)
        
        self.tree.heading("#0", text="Hierarchy"); self.tree.column("#0", width=250)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.props_frame = tk.Frame(self.paned, bg="#252526")
        self.paned.add(self.props_frame, weight=2)
        
        # Make the properties panel scrollable
        self.props_canvas = tk.Canvas(self.props_frame, bg="#252526", bd=0, highlightthickness=0)
        vsb = ttk.Scrollbar(self.props_frame, orient="vertical", command=self.props_canvas.yview)
        self.props_scrollable_frame = tk.Frame(self.props_canvas, bg="#252526")
        
        self.props_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.props_canvas.pack(side="left", fill="both", expand=True)
        
        self.props_canvas_win = self.props_canvas.create_window((0, 0), window=self.props_scrollable_frame, anchor="nw")
        self.props_scrollable_frame.bind("<Configure>", lambda e: self.props_canvas.configure(scrollregion=self.props_canvas.bbox("all")))
        self.props_canvas.bind("<Configure>", lambda e: self.props_canvas.itemconfig(self.props_canvas_win, width=e.width))

    def _expand_to_level(self, max_depth):
        """Expands tree nodes up to a specific depth."""
        def _recurse(item, current_depth):
            if current_depth < max_depth:
                self.tree.item(item, open=True)
                for child in self.tree.get_children(item):
                    _recurse(child, current_depth + 1)
            else:
                self.tree.item(item, open=False)

        for root_item in self.tree.get_children(''):
            _recurse(root_item, 1)

    def _on_state_updated(self, json_data, source=None):
        if source == self: return
        self.current_json_data = json_data
        self.tree.delete(*self.tree.get_children())
        self._populate_tree("", "root", json_data)

    def _populate_tree(self, parent, key, value, path=""):
        # We only want to see parents and their children (hierarchy)
        # Primitives/values are shown in the bottom panel
        node_id = f"{path}.{key}" if path else str(key)
        
        if isinstance(value, (dict, list)):
            item = self.tree.insert(parent, "end", iid=node_id, text=str(key))
            if isinstance(value, dict):
                for k, v in value.items(): self._populate_tree(item, k, v, node_id)
            elif isinstance(value, list):
                for i, v in enumerate(value): self._populate_tree(item, i, v, node_id)
        else:
            # We don't insert primitives into the tree anymore as per request
            pass

    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        node_id = selected[0]
        
        # ⚡ LOGGING: Trace user interaction
        matrix_log("ui", "gui_builder", "json_tree", f"🖱️🖱️🖱️ [ACTION] JsonTree: Node selected: {node_id}", "INFO")

        # Normalize path for global focus (Strip 'root.' if present)
        clean_path = node_id.replace("root.", "") if node_id.startswith("root.") else node_id
        if clean_path == "root": clean_path = ""

        # 🚀 SYNC: Open main properties panel on the right
        event_bus.publish("FOCUS_REQUESTED", path=clean_path, source=self)

        # Update Local internal properties panel (below the tree)
        for widget in self.props_scrollable_frame.winfo_children(): widget.destroy()

        # Resolve data for local panel
        path_segments = node_id.split('.')[1:] 
        curr = self.current_json_data
        for seg in path_segments:
            if isinstance(curr, dict) and seg in curr: curr = curr[seg]
            elif isinstance(curr, list):
                try: curr = curr[int(seg)]
                except (ValueError, IndexError): break

        if isinstance(curr, dict): self._build_properties_panel(node_id, curr)
        elif isinstance(curr, list): tk.Label(self.props_scrollable_frame, text=f"Array [{len(curr)} items]", bg="#252526", fg="white").pack(pady=10)
        else: self._build_primitive_editor(node_id, curr)

    def _build_properties_panel(self, parent_id, data_dict):
        # Sort keys so they appear consistently
        for k in sorted(data_dict.keys()):
            v = data_dict[k]
            if isinstance(v, (dict, list)): continue # Hierarchy is in the tree
            
            row = tk.Frame(self.props_scrollable_frame, bg="#252526")
            row.pack(fill="x", pady=1)
            tk.Label(row, text=k, width=15, anchor="w", bg="#252526", fg="#dcdcdc", font=("Consolas", 8)).pack(side="left")
            entry = tk.Entry(row, bg="#3c3c3c", fg="white", bd=0, insertbackground="white", font=("Consolas", 8))
            entry.pack(side="left", fill="x", expand=True); entry.insert(0, str(v))
            entry.bind("<Return>", lambda e, k=k, ent=entry, p_id=parent_id: self._update_property(p_id, k, ent.get()))

    def _build_primitive_editor(self, node_id, value):
        entry = tk.Entry(self.props_scrollable_frame, bg="#3c3c3c", fg="white", bd=0, insertbackground="white")
        entry.pack(fill="x", padx=10, pady=5); entry.insert(0, str(value))
        key = node_id.split('.')[-1]
        parent_id = ".".join(node_id.split('.')[:-1])
        entry.bind("<Return>", lambda e: self._update_property(parent_id, key, entry.get()))

    def _update_property(self, parent_id, key, new_value):
        # Cast logic
        if new_value.isdigit(): new_value = int(new_value)
        elif new_value.lower() == "true": new_value = True
        elif new_value.lower() == "false": new_value = False

        path_segments = parent_id.split('.')[1:]
        curr = self.current_json_data
        for seg in path_segments:
            if isinstance(curr, dict): curr = curr[seg]
            elif isinstance(curr, list): curr = curr[int(seg)]
            
        if isinstance(curr, dict): curr[key] = new_value
        elif isinstance(curr, list): curr[int(key)] = new_value

        matrix_log("ui", "gui_builder", "json_tree", f"💾📁🏁 [STORAGE] JsonTree: Updated {key} to {new_value}", "SUCCESS")
        state_manager.update_state(self.current_json_data, source=self)


# --- ENHANCED CODE WORKSPACE WITH LEVEL-SPECIFIC FOLDING ---
class JsonCodeWorkspace(tk.Frame):
    """Code editor with compressed depth triangles and level-specific expansion buttons."""

    DEPTH_COLORS = ["#569CD6", "#C586C0", "#4EC9B0", "#CE9178", "#DCDCAA", "#9CDCFE"]

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, bg="#1e1e1e", *args, **kwargs)
        self.fold_regions = {} # line -> (start, end, depth)
        self.folded_lines = set()
        
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name, "🎨🎨🎨 [RENDER] JsonCode: Initializing Level-Aware Editor...", "DEBUG")
        self._build_ui()
        
        event_bus.subscribe("STATE_UPDATED", self._on_state_updated)
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)
        
        current_state = state_manager.get_state()
        if current_state: self._on_state_updated(current_state)

    def _on_focus_requested(self, path, source=None):
        """Scrolls the editor to the specified path and highlights it."""
        if source == self or not path: return
        
        content = self.text_area.get("1.0", "end-1c")
        # Simple heuristic to find the path in the JSON string
        # Paths are like 'root.element.property'
        # We look for '"element":' at the correct indentation (simplified)
        parts = path.split('.')
        target_key = f'"{parts[-1]}":'
        
        self.text_area.tag_remove("search_highlight", "1.0", "end")
        
        idx = "1.0"
        while True:
            idx = self.text_area.search(target_key, idx, nocase=False, stopindex="end")
            if not idx: break
            
            # TODO: Add indentation check to ensure it's the CORRECT key for the path
            # For now, we'll just go to the first match for simplicity
            self.text_area.tag_add("search_highlight", idx, f"{idx} + {len(target_key)} chars")
            self.text_area.tag_configure("search_highlight", background="#4b4b00")
            self.text_area.see(idx)
            break

    def _build_ui(self):
        # 1. Main Header
        header = tk.Frame(self, bg="#333333", height=30)
        header.pack(side="top", fill="x")
        ttk.Button(header, text="Apply Changes", command=self._apply_changes).pack(side="right", padx=5)
        ttk.Button(header, text="Format", command=self._format_json).pack(side="right", padx=5)

        # 2. Advanced Fold Controls (Level Specific)
        fold_controls = tk.Frame(self, bg="#2d2d2d", height=25)
        fold_controls.pack(side="top", fill="x")
        
        tk.Label(fold_controls, text="FOLD:", bg="#2d2d2d", fg="#888888", font=("Arial", 7, "bold")).pack(side="left", padx=(10, 5))
        
        # Level Buttons
        for lvl in [3, 4, 5, 6]:
            tk.Button(fold_controls, text=f"L{lvl}", bg="#3c3c3c", fg="#dcdcdc", bd=0, 
                      font=("Arial", 7), command=lambda l=lvl: self.fold_to_level(l), width=3).pack(side="left", padx=1)
        
        tk.Frame(fold_controls, bg="#444444", width=1).pack(side="left", fill="y", padx=5, pady=4)
        
        tk.Button(fold_controls, text="EXPAND ALL", bg="#3c3c3c", fg="#00ffcc", bd=0, 
                  font=("Arial", 7, "bold"), command=self.expand_all, padx=10).pack(side="left", padx=2, pady=2)

        # 3. Editor Area
        container = tk.Frame(self, bg="#1e1e1e")
        container.pack(fill="both", expand=True)

        self.gutter = tk.Text(container, width=8, bg="#1a1a1a", fg="#858585", 
                              font=("Consolas", 11), padx=2, bd=0, state="disabled", wrap="none")
        self.gutter.pack(side="left", fill="y")
        
        # We need a nested frame for the text area and its horizontal scrollbar
        text_frame = tk.Frame(container, bg="#1e1e1e")
        text_frame.pack(side="left", fill="both", expand=True)

        self.text_area = tk.Text(text_frame, bg="#1e1e1e", fg="#dcdcdc", insertbackground="white",
                                 font=("Consolas", 11), wrap="none", undo=True, bd=0)
        
        vsb = ttk.Scrollbar(container, orient="vertical", command=self._sync_scroll)
        hsb = ttk.Scrollbar(text_frame, orient="horizontal", command=self.text_area.xview)
        
        self.text_area.configure(yscrollcommand=self._sync_scroll_move, xscrollcommand=hsb.set)
        
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.text_area.pack(side="top", fill="both", expand=True)

        self.text_area.tag_configure("folded", elide=True)
        self.text_area.tag_configure("key", foreground="#9CDCFE")
        for i, color in enumerate(self.DEPTH_COLORS):
            self.gutter.tag_configure(f"depth_{i}", foreground=color)
        
        self.text_area.bind("<<Modified>>", self._on_text_change)
        self.gutter.tag_bind("fold_marker", "<Button-1>", self._on_fold_click)

    def _sync_scroll(self, *args):
        self.text_area.yview(*args); self.gutter.yview(*args)

    def _sync_scroll_move(self, first, last):
        self.gutter.yview_moveto(first)

    def _on_text_change(self, event=None):
        if self.text_area.edit_modified():
            self._update_gutter()
            self._apply_highlight()
            self.text_area.edit_modified(False)

    def _update_gutter(self):
        self.gutter.config(state="normal")
        self.gutter.delete("1.0", "end")
        
        content = self.text_area.get("1.0", "end-1c")
        lines = content.split('\n')
        self.fold_regions.clear()
        
        folded_ranges = self.text_area.tag_ranges("folded")
        
        for i, line in enumerate(lines):
            original_line_idx = i + 1
            is_hidden = False
            for r in range(0, len(folded_ranges), 2):
                if self.text_area.compare(f"{original_line_idx}.0", ">=", folded_ranges[r]) and \
                   self.text_area.compare(f"{original_line_idx}.0", "<", folded_ranges[r+1]):
                    is_hidden = True; break
            
            if is_hidden: continue
            
            leading_spaces = len(line) - len(line.lstrip())
            depth = leading_spaces // 2
            color_idx = depth % len(self.DEPTH_COLORS)
            
            indent_str = " " * depth
            self.gutter.insert("end", indent_str)
            
            if '{' in line or '[' in line:
                glyph = "▶" if original_line_idx in self.folded_lines else "▼"
                self.gutter.insert("end", glyph, ("fold_marker", f"depth_{color_idx}", f"fold_{original_line_idx}"))
                
                nest = 0
                for j in range(i, len(lines)):
                    nest += lines[j].count('{') + lines[j].count('[')
                    nest -= lines[j].count('}') + lines[j].count(']')
                    if nest == 0:
                        # ⚡ STORE DEPTH: Needed for level-specific folding
                        self.fold_regions[original_line_idx] = (f"{original_line_idx}.end", f"{j+1}.end", depth)
                        break
            
            self.gutter.insert("end", "\n")
        self.gutter.config(state="disabled")

    def expand_all(self):
        self.text_area.tag_remove("folded", "1.0", "end")
        self.folded_lines.clear()
        self._update_gutter()

    def fold_to_level(self, target_level):
        """
        Intelligently collapses the hierarchy.
        Anything at depth >= target_level will be hidden.
        L1 = Show only the root object.
        L2 = Show root and its immediate children.
        """
        self.text_area.tag_remove("folded", "1.0", "end")
        self.folded_lines.clear()
        
        # Refresh regions to ensure we have current mapping
        self._update_gutter()
        
        # Sort by depth descending so nested folds are applied inside-out
        sorted_regions = sorted(self.fold_regions.items(), key=lambda x: x[1][2], reverse=True)
        
        for line_num, (start, end, depth) in sorted_regions:
            if depth >= target_level:
                self.text_area.tag_add("folded", start, end)
                self.folded_lines.add(line_num)
        
        self._update_gutter()

    def _on_fold_click(self, event):
        index = self.gutter.index(f"@{event.x},{event.y}")
        tags = self.gutter.tag_names(index)
        fold_tag = [t for t in tags if t.startswith("fold_") and t != "fold_marker"]
        
        if fold_tag:
            orig_line_num = int(fold_tag[0].split('_')[1])
            if orig_line_num in self.fold_regions:
                start, end, depth = self.fold_regions[orig_line_num]
                if orig_line_num in self.folded_lines:
                    self.text_area.tag_remove("folded", start, end)
                    self.folded_lines.remove(orig_line_num)
                else:
                    self.text_area.tag_add("folded", start, end)
                    self.folded_lines.add(orig_line_num)
                self._update_gutter()

    def _on_state_updated(self, json_data, source=None):
        if source == self or not self.winfo_exists(): return
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", orjson.dumps(json_data, option=orjson.OPT_INDENT_2).decode())
        self._update_gutter()
        self._apply_highlight()

    def _apply_changes(self):
        try:
            data = orjson.loads(self.text_area.get("1.0", "end-1c"))
            state_manager.update_state(data, source=self)
        except Exception as e:
            logger.error(f"❌📂🤦‍♂️ [STORAGE] JsonCode: Syntax Error: {e}")

    def _format_json(self):
        try:
            data = orjson.loads(self.text_area.get("1.0", "end-1c"))
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", orjson.dumps(data, option=orjson.OPT_INDENT_2).decode())
            self.folded_lines.clear()
            self._apply_highlight(); self._update_gutter()
        except: pass

    def _apply_highlight(self):
        content = self.text_area.get("1.0", "end-1c")
        for tag in ["key"]: self.text_area.tag_remove(tag, "1.0", "end")
        for match in re.finditer(r'"(?:\\.|[^"\\])*"(?=\s*:)', content):
            self.text_area.tag_add("key", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
