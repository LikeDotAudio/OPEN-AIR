import tkinter as tk
from tkinter import ttk
from tkinter import colorchooser
import orjson
import re
import inspect
from oaComBroker.Core.event_bus import event_bus
from ..state import state_manager

# --- Standard Debug Logging Setup ---
from oaLogging.Core.logger import GUI_LOGGER as logger
from oaLogging.Methods.matrix_gate import matrix_log

class JsonEditor(tk.Frame):
    """The workspace for manual JSON editing with Tree and Text views."""

    def __init__(self, parent, is_detached=False, *args, **kwargs):
        self.is_detached = is_detached
        self.parent_widget = parent 
        self.current_json_data = {}

        if self.is_detached:
            self.top_level_window = tk.Toplevel()
            super().__init__(self.top_level_window, bg="#1e1e1e", *args, **kwargs) 
            self.top_level_window.title("JSON Editor (Detached)")
            self.top_level_window.geometry("1000x700") 
            self.top_level_window.grid_rowconfigure(0, weight=1)
            self.top_level_window.grid_columnconfigure(0, weight=1)
            self.pack(in_=self.top_level_window, fill="both", expand=True) 
        else:
            super().__init__(parent, bg="#1e1e1e", *args, **kwargs)
            if hasattr(parent, 'title'):
                parent.title("JSON Editor")

        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🎨🎨🎨 [RENDER] JsonEditor: Initializing workspace...", "DEBUG")
        self._build_ui()
        
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🎨🎨🎨 [RENDER] JsonEditor: Subscribing to EventBus...", "DEBUG")
        event_bus.subscribe("STATE_UPDATED", self._on_state_updated)
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)
        
        current_state = state_manager.get_state()
        if current_state:
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🎨🎨🎨 [RENDER] JsonEditor: Performing initial state sync...", "DEBUG")
            self._on_state_updated(current_state)

        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event):
        if event.widget == self:
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🛑🛑🛑 [STOPPED] JsonEditor: Workspace destroyed. Cleaning up subscriptions.", "INFO")
            event_bus.unsubscribe("STATE_UPDATED", self._on_state_updated)
            event_bus.unsubscribe("FOCUS_REQUESTED", self._on_focus_requested)

    def _pop_out_editor(self):
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🎨🎨🎨 [RENDER] JsonEditor: Popping out editor to a new window.", "INFO")
        detached_editor = JsonEditor(self.master, is_detached=True) 
        detached_editor.pack(fill="both", expand=True)
        detached_editor._on_state_updated(self.current_json_data)

    def _on_scroll(self, *args):
        if len(args) > 0 and not isinstance(args[0], str):
            return
        self.text_area.yview(*args)
        self.line_numbers.yview(*args)

    def _sync_scroll(self, *args):
        self.scrollbar.set(*args)
        self.line_numbers.yview_moveto(args[0])

    def _on_text_configure(self, event):
        self._update_line_numbers()

    def _on_text_modified(self, event=None):
        if not self.text_area.edit_modified():
            return
        self.text_area.edit_modified(False) 
        self._update_line_numbers()

    def _update_line_numbers(self):
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")
        num_lines = int(self.text_area.index("end-1c").split('.')[0]) if self.text_area.get("1.0", "end-1c") else 0
        for i in range(1, num_lines + 1):
            self.line_numbers.insert("end", str(i) + "\n")
        self.line_numbers.config(state="disabled")
        scroll_pos = self.text_area.yview()
        self.line_numbers.yview_moveto(scroll_pos[0])

    def _build_ui(self):
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🎨🎨🎨 [RENDER] JsonEditor: Creating Editor UI components...", "DEBUG")
        
        header = tk.Frame(self, bg="#333333", height=35)
        header.pack(side="top", fill="x")
        
        self.breadcrumb_var = tk.StringVar(value="Project > Root")
        tk.Label(header, textvariable=self.breadcrumb_var, bg="#333333", fg="#00ffcc", 
                 font=("Consolas", 10, "bold")).pack(side="left", padx=10, pady=5)
        
        ttk.Button(header, text="Apply Changes", command=self._apply_changes).pack(side="right", padx=5)
        ttk.Button(header, text="Format JSON", command=self._format_json).pack(side="right", padx=5)

        if not self.is_detached:
            ttk.Button(header, text="Pop Out", command=self._pop_out_editor).pack(side="right", padx=5)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # -------------------------------------------------------------------
        # TAB 1: TREE VIEW + PROPERTIES
        # -------------------------------------------------------------------
        self.tree_tab = tk.Frame(self.notebook, bg="#1e1e1e")
        self.notebook.add(self.tree_tab, text="Tree View")
        
        self.paned = ttk.PanedWindow(self.tree_tab, orient="horizontal")
        self.paned.pack(fill="both", expand=True)

        tree_frame = tk.Frame(self.paned, bg="#1e1e1e")
        self.paned.add(tree_frame, weight=3)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#1e1e1e", foreground="#dcdcdc", fieldbackground="#1e1e1e", font=("Consolas", 10), rowheight=24)
        style.map('Treeview', background=[('selected', '#094771')])

        self.tree = ttk.Treeview(tree_frame, columns=("value", "type"), selectmode="browse")
        self.tree.heading("#0", text="Key / Index", anchor="w")
        self.tree.heading("value", text="Value", anchor="w")
        self.tree.heading("type", text="Type", anchor="w")
        self.tree.column("#0", width=250, anchor="w")
        self.tree.column("value", width=250, anchor="w")
        self.tree.column("type", width=100, anchor="w")

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        self.props_frame = tk.Frame(self.paned, bg="#252526", width=280)
        self.paned.add(self.props_frame, weight=1)

        props_lbl = tk.Label(self.props_frame, text="Properties", bg="#333333", fg="white", font=("Arial", 9, "bold"))
        props_lbl.pack(side="top", fill="x")

        self.props_canvas = tk.Canvas(self.props_frame, bg="#252526", highlightthickness=0)
        self.props_scrollbar = ttk.Scrollbar(self.props_frame, orient="vertical", command=self.props_canvas.yview)
        self.props_scrollable_frame = tk.Frame(self.props_canvas, bg="#252526")

        self.props_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.props_canvas.configure(
                scrollregion=self.props_canvas.bbox("all")
            )
        )
        self.props_canvas.create_window((0, 0), window=self.props_scrollable_frame, anchor="nw", width=280)
        self.props_canvas.configure(yscrollcommand=self.props_scrollbar.set)
        
        self.props_canvas.pack(side="left", fill="both", expand=True)
        self.props_scrollbar.pack(side="right", fill="y")

        # -------------------------------------------------------------------
        # TAB 2: TEXT VIEW
        # -------------------------------------------------------------------
        self.text_tab = tk.Frame(self.notebook, bg="#1e1e1e")
        self.notebook.add(self.text_tab, text="Text View")

        editor_frame = tk.Frame(self.text_tab, bg="#1e1e1e") 
        editor_frame.pack(side="left", fill="both", expand=True)

        self.line_numbers = tk.Text(editor_frame, width=4, padx=4, takefocus=0, border=0,
                                     bg="#252526", fg="#606060", state="disabled", wrap="none")
        self.line_numbers.pack(side="left", fill="y")

        self.text_area = tk.Text(editor_frame, bg="#1e1e1e", fg="#dcdcdc", insertbackground="white",
                                 font=("Consolas", 11), wrap="none", undo=True, bd=0)
        self.text_area.pack(side="left", fill="both", expand=True)
        
        self.scrollbar = ttk.Scrollbar(editor_frame, orient="vertical", command=self._on_scroll)
        self.scrollbar.pack(side="right", fill="y")
        
        self.text_area.config(yscrollcommand=self._sync_scroll)
        self.line_numbers.config(yscrollcommand=self.scrollbar.set) 

        self.text_area.bind("<KeyRelease>", self._on_key_release)
        self.text_area.bind("<Configure>", self._on_text_configure) 
        self.text_area.bind("<<Modified>>", self._on_text_modified) 

        self.text_area.tag_configure("key", foreground="#9CDCFE")
        self.text_area.tag_configure("string", foreground="#CE9178")
        self.text_area.tag_configure("number", foreground="#B5CEA8")
        self.text_area.tag_configure("keyword", foreground="#569CD6")

        self._update_line_numbers()

        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🎨🎨🎨 [RENDER] JsonEditor: Editor UI built.", "DEBUG")

    def _refresh_tree(self):
        open_nodes = [item for item in self._get_all_children("") if self.tree.item(item, "open")]
        selected = self.tree.selection()

        self.tree.delete(*self.tree.get_children())
        self._populate_tree("", "root", self.current_json_data)

        for node in open_nodes:
            if self.tree.exists(node):
                self.tree.item(node, open=True)
                
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected[0])
            self.tree.see(selected[0])

    def _get_all_children(self, item=""):
        children = self.tree.get_children(item)
        for child in children:
            children += self._get_all_children(child)
        return children

    def _populate_tree(self, parent_node, key, value, path=""):
        node_id = f"{path}.{key}" if path else str(key)
        
        if isinstance(value, dict):
            summary = f"{{...}} [{len(value)} items]"
            item = self.tree.insert(parent_node, "end", iid=node_id, text=str(key), values=(summary, "object"))
            for k, v in value.items():
                self._populate_tree(item, k, v, node_id)
        elif isinstance(value, list):
            summary = f"[...] [{len(value)} items]"
            item = self.tree.insert(parent_node, "end", iid=node_id, text=str(key), values=(summary, "array"))
            for i, v in enumerate(value):
                self._populate_tree(item, i, v, node_id)
        else:
            self.tree.insert(parent_node, "end", iid=node_id, text=str(key), values=(str(value), type(value).__name__))

    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
            
        node_id = selected[0]
        self.breadcrumb_var.set(f"Project > {node_id.replace('.', ' > ')}")
        
        for widget in self.props_scrollable_frame.winfo_children():
            widget.destroy()

        path_segments = node_id.split('.')[1:] 
        curr = self.current_json_data
        for seg in path_segments:
            if isinstance(curr, dict) and seg in curr:
                curr = curr[seg]
            elif isinstance(curr, list):
                try:
                    curr = curr[int(seg)]
                except (ValueError, IndexError):
                    break

        if isinstance(curr, dict):
            self._build_properties_panel(node_id, curr)
        elif isinstance(curr, list):
            tk.Label(self.props_scrollable_frame, text=f"Array [{len(curr)} items]", bg="#252526", fg="white").pack(pady=10)
        else:
            self._build_primitive_editor(node_id, curr)
            
        self.props_canvas.update_idletasks()
        self.props_canvas.configure(scrollregion=self.props_canvas.bbox("all"))

    def _build_properties_panel(self, parent_id, data_dict):
        categories = {
            "Geometry": ["x", "y", "width", "height", "row", "column", "rowspan", "columnspan", "padx", "pady", "sticky", "relx", "rely", "relwidth", "relheight"],
            "Colors": ["bg", "fg", "background", "foreground", "color", "bordercolor", "activebackground", "activeforeground", "highlightcolor", "highlightbackground"],
            "Actions": ["command", "on_click", "action", "trigger", "bind", "event"],
            "General": [] 
        }

        categorized_data = {k: {} for k in categories}
        
        for k, v in data_dict.items():
            if not isinstance(v, (dict, list)): 
                placed = False
                for cat, keys in categories.items():
                    if k in keys:
                        categorized_data[cat][k] = v
                        placed = True
                        break
                if not placed:
                    categorized_data["General"][k] = v

        for cat, items in categorized_data.items():
            if not items: continue

            lbl = tk.Label(self.props_scrollable_frame, text=f"▼ {cat}", bg="#333333", fg="#00ffcc", anchor="w", font=("Arial", 9, "bold"))
            lbl.pack(fill="x", pady=(5, 0))

            frame = tk.Frame(self.props_scrollable_frame, bg="#252526")
            frame.pack(fill="x", padx=10, pady=2)

            for key, val in items.items():
                row = tk.Frame(frame, bg="#252526")
                row.pack(fill="x", pady=2)
                
                tk.Label(row, text=key, width=12, anchor="w", bg="#252526", fg="#dcdcdc").pack(side="left")
                
                entry = tk.Entry(row, bg="#3c3c3c", fg="white", bd=0, insertbackground="white")
                entry.pack(side="left", fill="x", expand=True)
                entry.insert(0, str(val))
                
                if cat == "Colors":
                    btn = tk.Button(row, text="🎨", bg="#3c3c3c", fg="white", bd=0, 
                                    command=lambda k=key, ent=entry, p_id=parent_id: self._pick_color(p_id, k, ent))
                    btn.pack(side="right", padx=2)
                
                entry.bind("<FocusOut>", lambda e, k=key, ent=entry, p_id=parent_id: self._update_property(p_id, k, ent.get()))
                entry.bind("<Return>", lambda e, k=key, ent=entry, p_id=parent_id: self._update_property(p_id, k, ent.get()))

    def _pick_color(self, parent_id, key, entry_widget):
        color_code = colorchooser.askcolor(title=f"Choose color for {key}")[1]
        if color_code:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, color_code)
            self._update_property(parent_id, key, color_code)

    def _build_primitive_editor(self, node_id, value):
        tk.Label(self.props_scrollable_frame, text="Value", bg="#333333", fg="#00ffcc", anchor="w").pack(fill="x", pady=5)
        
        entry = tk.Entry(self.props_scrollable_frame, bg="#3c3c3c", fg="white", bd=0, insertbackground="white")
        entry.pack(fill="x", padx=10, pady=5)
        entry.insert(0, str(value))
        
        key = node_id.split('.')[-1]
        parent_id = ".".join(node_id.split('.')[:-1])
        
        entry.bind("<FocusOut>", lambda e: self._update_property(parent_id, key, entry.get()))
        entry.bind("<Return>", lambda e: self._update_property(parent_id, key, entry.get()))

    def _update_property(self, parent_id, key, new_value):
        if new_value.isdigit(): new_value = int(new_value)
        elif new_value.replace('.', '', 1).isdigit() and new_value.count('.') < 2: new_value = float(new_value)
        elif new_value.lower() == "true": new_value = True
        elif new_value.lower() == "false": new_value = False
        elif new_value.lower() == "null": new_value = None

        path_segments = parent_id.split('.')[1:]
        curr = self.current_json_data
        for seg in path_segments:
            if isinstance(curr, dict): curr = curr[seg]
            elif isinstance(curr, list): curr = curr[int(seg)]
            
        if isinstance(curr, dict):
            curr[key] = new_value
        elif isinstance(curr, list):
            curr[int(key)] = new_value

        self._apply_text_area_sync()

        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🖱️🖱️🖱️ [ACTION] JsonEditor: Property {key} updated. Pushing to StateManager...", "SUCCESS")
        state_manager.update_state(self.current_json_data, source=self)
        self._refresh_tree()
        self._on_tree_select(None)

    def _apply_text_area_sync(self):
        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", orjson.dumps(self.current_json_data, option=orjson.OPT_INDENT_2).decode())
        self._apply_highlight()
        self._update_line_numbers()

    def _on_state_updated(self, json_data, source=None):
        if source == self or not self.winfo_exists():
            return
            
        if hasattr(self, '_update_job') and self._update_job:
            self.after_cancel(self._update_job)
            
        self._update_job = self.after(200, lambda: self._process_state_update(json_data, source))

    def _process_state_update(self, json_data, source=None):
        if not self.winfo_exists():
            return
            
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🎨🎨🎨 [RENDER] JsonEditor: Remote state update from {source.__class__.__name__ if source else 'External'}.", "INFO")
        
        self.current_json_data = json_data
        
        if hasattr(self, 'text_area'):
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", orjson.dumps(json_data, option=orjson.OPT_INDENT_2).decode())
            self._apply_highlight()
            self._update_line_numbers()
            
        self._refresh_tree()
        
        if hasattr(self, 'focused_path') and self.focused_path:
            self._on_focus_requested(self.focused_path, source="StateUpdate", new_state=json_data)

    def _on_focus_requested(self, path, source=None, new_state=None):
        if not self.winfo_exists(): return
        
        self.focused_path = path
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", f"🖱️🖱️🖱️ [ACTION] JsonEditor: Focus synchronization for path: {path}", "INFO")
        
        if new_state:
            self.current_json_data = new_state
            
        if not path:
            self._on_state_updated(self.current_json_data)
            return

        def resolve_path(data, segments):
            curr = data
            for seg in segments:
                if isinstance(curr, dict) and seg in curr: curr = curr[seg]
                elif isinstance(curr, list):
                    try: curr = curr[int(seg)]
                    except (ValueError, IndexError): return None
                else: return None
            return curr

        path_segments = path.split('.')
        target_data = resolve_path(self.current_json_data, path_segments)
        
        if target_data is None:
            target_data = self.current_json_data
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name, "⚠️ JsonEditor: Path resolution failed. Defaulting to Root JSON.", "WARNING")

        self.text_area.delete("1.0", "end")
        self.text_area.insert("1.0", orjson.dumps(target_data, option=orjson.OPT_INDENT_2).decode())
        self._apply_highlight()
        self._update_line_numbers()

        tree_path = f"root.{path}"
        parts = tree_path.split('.')
        for i in range(1, len(parts)):
            p = ".".join(parts[:i])
            if self.tree.exists(p):
                self.tree.item(p, open=True)

        if self.tree.exists(tree_path):
            self.tree.selection_set(tree_path)
            self.tree.see(tree_path)
            self._on_tree_select(None)

    def _on_key_release(self, event):
        if event.keysym not in ["Left", "Right", "Up", "Down", "Control_L", "Control_R"]:
            self._apply_highlight()

    def _apply_changes(self):
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🖱️🖱️🖱️ [ACTION] JsonEditor: 'Apply Changes' manual trigger.", "INFO")
        try:
            raw_text = self.text_area.get("1.0", "end-1c")
            new_data = orjson.loads(raw_text)
            self.current_json_data = new_data
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🎨🎨🎨 [RENDER] JsonEditor: Successfully parsed JSON. Pushing to StateManager...", "SUCCESS")
            state_manager.update_state(new_data, source=self)
            self._refresh_tree()
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🎨🎨🎨 [RENDER] JsonEditor: Manual changes applied successfully.", "SUCCESS")
        except Exception as e:
            from oaLogging.Core.logger import WYSIWYG_LOGGER
            WYSIWYG_LOGGER.error(f"❌ JsonEditor: JSON Syntax Error during apply: {e}")

    def _format_json(self):
        matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🖱️🖱️🖱️ [ACTION] JsonEditor: 'Format JSON' manual trigger.", "INFO")
        try:
            raw_text = self.text_area.get("1.0", "end-1c")
            data = orjson.loads(raw_text)
            formatted = orjson.dumps(data, option=orjson.OPT_INDENT_2).decode()
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", formatted)
            matrix_log("ui", "gui_builder", inspect.currentframe().f_code.co_name if "inspect" in globals() else "unknown", "🎨🎨🎨 [RENDER] JsonEditor: JSON beautified. Applying highlights and syncing state_manager...", "DEBUG")
            self._apply_highlight()
            self._apply_changes()
        except Exception as e:
            from oaLogging.Core.logger import WYSIWYG_LOGGER
            WYSIWYG_LOGGER.exception("❌ JsonEditor: Format Error")

    def _apply_highlight(self):
        if not hasattr(self, 'text_area'): return
        
        for tag in ["key", "string", "number", "keyword"]:
            self.text_area.tag_remove(tag, "1.0", "end")
            
        content = self.text_area.get("1.0", "end-1c")
        patterns = [
            (r'"(?:\\.|[^"\\])*"(?=\s*:)', "key"),
            (r'"(?:\\.|[^"\\])*"(?!\s*:)', "string"),
            (r'\b-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b', "number"),
            (r'\b(?:true|false|null)\b', "keyword"),
        ]
        for pattern, tag in patterns:
            for match in re.finditer(pattern, content):
                start, end = match.span()
                self.text_area.tag_add(tag, f"1.0 + {start} chars", f"1.0 + {end} chars")
