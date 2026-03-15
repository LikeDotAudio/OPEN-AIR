# workers/wysiwyg_editor/workspaces/element_properties.py
#
# The Element Properties Workspace.
# Provides a high-level UI for adjusting parameters of the focused element.
# Recursively displays all JSON properties on a single page with collapsible sections.
#
# Author: Gemini CLI

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import orjson
from ..core.event_bus import event_bus
from ..core.state_manager import state_manager
from ..grab_bag.grab_bag_loader import GrabBagLoader
from workers.logger.logger import initialize_logging, set_log_directory
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

class ElementProperties(tk.Frame):
    """A dedicated workspace for editing the properties of a selected element."""

    def __init__(self, parent, *args, **kwargs):
        kwargs.pop("bg", None)
        super().__init__(parent, bg="#2b2b2b", *args, **kwargs)
        if LOCAL_DEBUG: logger.debug("🛠️ ElementProperties: Initializing workspace...")
        self.focused_path = None
        self.scrub_start_val = 0
        self.scrub_start_x = 0
        self._refresh_job = None
        
        # 🎒 LIBRARY AWARENESS
        self.library_loader = GrabBagLoader()
        self.library = self.library_loader.scan_library()

        # Configure custom style for entries
        self.style = ttk.Style()
        self.style.configure("Property.TEntry", 
                             fieldbackground="#1e1e1e", 
                             foreground="#dcdcdc", 
                             insertcolor="white",
                             bordercolor="#444444",
                             lightcolor="#444444",
                             darkcolor="#444444")
        
        self._build_ui()
        
        # Subscribe to focus events
        if LOCAL_DEBUG: logger.debug("🛠️ ElementProperties: Subscribing to EventBus...")
        event_bus.subscribe("FOCUS_REQUESTED", self._on_focus_requested)
        event_bus.subscribe("STATE_UPDATED", self._on_state_updated)
        
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event):
        if event.widget == self:
            if LOCAL_DEBUG: logger.info("🛠️ ElementProperties: Workspace destroyed. Cleaning up subscriptions.")
            event_bus.unsubscribe("FOCUS_REQUESTED", self._on_focus_requested)
            event_bus.unsubscribe("STATE_UPDATED", self._on_state_updated)

    def _on_state_updated(self, json_data, source=None):
        """Keep properties in sync if JSON changed elsewhere, but don't force a full redraw if we are the source."""
        if source == self or not self.focused_path: return
        if LOCAL_DEBUG: logger.info(f"🛠️ ElementProperties: State update detected (Source: {source.__class__.__name__ if source else 'External'}). Refreshing view for {self.focused_path}.")
        self._request_debounced_refresh()

    def _request_debounced_refresh(self, delay=1500):
        """Schedules a full properties rebuild after a delay to prevent flickering during rapid editing."""
        if self._refresh_job:
            self.after_cancel(self._refresh_job)
        self._refresh_job = self.after(delay, self._refresh_content)

    def _on_focus_requested(self, path, source=None):
        if not self.winfo_exists(): return
        if LOCAL_DEBUG: logger.info(f"🛠️ ElementProperties: Focus synchronization for path: {path} (Source: {source.__class__.__name__ if source else 'Unknown'})")
        self.focused_path = path
        self._refresh_content()

    def _refresh_content(self):
        """Redraws the entire property tree for the focused element."""
        if not self.focused_path or not self.winfo_exists(): return
        
        if LOCAL_DEBUG: logger.debug(f"🛠️ ElementProperties: Rebuilding property tree for path: {self.focused_path}")
        for child in self.scroll_frame.winfo_children(): child.destroy()
        
        self.path_lbl.config(text=f"Path: {self.focused_path}")

        actual_data = state_manager.get_value_at_path(self.focused_path)
        if actual_data is not None:
            # --- 1. HEADER ACTIONS ---
            self._render_header_actions()

            # --- 2. QUICK TOOLS (Alignment & Sticky) ---
            if isinstance(actual_data, dict) and (actual_data.get("type") or actual_data.get("widget_type")):
                tools_container = tk.Frame(self.scroll_frame, bg="#252525", pady=10)
                tools_container.pack(fill="x", pady=(0, 10))
                self._render_alignment_quick_tools(actual_data, tools_container)
                self._render_sticky_quick_tools(actual_data, tools_container)

            # --- 3. MAIN PROPERTIES (PROACTIVE LIBRARY MERGE) ---
            # Instead of just rendering actual_data, we merge it with the Library Schema
            # so ALL possible properties are visible.
            if isinstance(actual_data, dict):
                w_type = actual_data.get("type", actual_data.get("widget_type"))
                schema = {}
                # Find matching library component
                for name, comp in self.library.items():
                    if comp["type"] == w_type:
                        schema = comp.get("schema", {})
                        break
                
                # Perform deep merge for display (template + actual)
                display_data = self._deep_merge_for_display(schema, actual_data)
                self._render_recursive_properties(display_data, self.scroll_frame, prefix=self.focused_path, actual_data=actual_data)
            else:
                self._render_leaf_editor(self.focused_path.split(".")[-1], actual_data, self.scroll_frame, self.focused_path)
        else:
            logger.warning(f"❌ ElementProperties: Path {self.focused_path} not found in state manager.")
            tk.Label(self.scroll_frame, text=f"Error: Path {self.focused_path} not found.", bg="#2b2b2b", fg="red").pack(pady=20)

    def _deep_merge_for_display(self, template, actual):
        """Creates a merged dictionary containing all template keys and all actual keys."""
        if not isinstance(template, dict) or not isinstance(actual, dict):
            return actual
        
        result = template.copy()
        for k, v in actual.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = self._deep_merge_for_display(result[k], v)
            else:
                result[k] = v
        return result

    def _build_ui(self):
        if LOCAL_DEBUG: logger.debug("🛠️ ElementProperties: Building UI components...")
        header = tk.Frame(self, bg="#333333", height=35)
        header.pack(side="top", fill="x")
        tk.Label(header, text="PROPERTIES", bg="#333333", fg="white", font=("Arial", 9, "bold")).pack(side="left", padx=10)
        
        # 🗑️ DELETE BUTTON
        self.del_btn = tk.Button(header, text="DELETE WIDGET", bg="#cc0000", fg="white", 
                                 font=("Arial", 7, "bold"), relief="flat", padx=5,
                                 command=self._delete_focused_element)
        self.del_btn.pack(side="right", padx=5)

        self.path_lbl = tk.Label(header, text="No Selection", bg="#333333", fg="#33A1FD", font=("Arial", 8))
        self.path_lbl.pack(side="right", padx=10)

        self.canvas = tk.Canvas(self, bg="#2b2b2b", bd=0, highlightthickness=0)
        self.scrollbar = AutoScrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg="#2b2b2b")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        
        tk.Label(self.scroll_frame, text="Select a widget to edit properties.", bg="#2b2b2b", fg="#888888").pack(pady=50)
        if LOCAL_DEBUG: logger.debug("🛠️ ElementProperties: UI build complete.")

    def _delete_focused_element(self):
        if not self.focused_path: return
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{self.focused_path}'?\nThis cannot be undone."):
            state_manager.delete_element(self.focused_path, source=self)
            self.focused_path = None
            self._refresh_content()

    def _render_header_actions(self):
        """Renders element-level actions at the top of the properties list."""
        pass 

    def _render_alignment_quick_tools(self, data, container):
        """Specialized UI for L R C T B alignment mapping to 'layout.align'."""
        tk.Label(container, text="QUICK ALIGNMENT (ANCHOR)", bg="#252525", fg="#888888", font=("Arial", 7, "bold")).pack()
        
        btn_frame = tk.Frame(container, bg="#252525")
        btn_frame.pack(pady=(5, 10))

        layout = data.get("layout", {})
        align = str(layout.get("align", "")).lower()
        stretch = str(layout.get("stretch", "")).lower()
        
        buttons = {}

        def set_align(mode):
            current_data = state_manager.get_value_at_path(self.focused_path)
            curr_layout = current_data.get("layout", {})
            curr_align = set(str(curr_layout.get("align", "")).lower().split())
            curr_stretch = set(str(curr_layout.get("stretch", "")).lower().split())
            
            if mode == "L":
                if "left" in curr_align: curr_align.discard("left")
                else:
                    curr_align.discard("right")
                    curr_align.add("left")
                    curr_stretch.discard("width")
                    curr_stretch.discard("both")
            elif mode == "R":
                if "right" in curr_align: curr_align.discard("right")
                else:
                    curr_align.discard("left")
                    curr_align.add("right")
                    curr_stretch.discard("width")
                    curr_stretch.discard("both")
            elif mode == "T":
                if "top" in curr_align: curr_align.discard("top")
                else:
                    curr_align.discard("bottom")
                    curr_align.add("top")
                    curr_stretch.discard("height")
                    curr_stretch.discard("both")
            elif mode == "B":
                if "bottom" in curr_align: curr_align.discard("bottom")
                else:
                    curr_align.discard("top")
                    curr_align.add("bottom")
                    curr_stretch.discard("height")
                    curr_stretch.discard("both")
            elif mode == "C":
                curr_align.clear()

            new_align = " ".join(sorted(list(curr_align)))
            new_stretch = " ".join(sorted(list(curr_stretch)))
            
            l_path = f"{self.focused_path}.layout"
            if "layout" not in current_data:
                state_manager.update_state({"align": new_align, "stretch": new_stretch}, path=l_path, source=self)
            else:
                state_manager.update_state(new_align, path=f"{l_path}.align", source=self)
                state_manager.update_state(new_stretch, path=f"{l_path}.stretch", source=self)
            
            self._update_tool_highlights(new_align, new_stretch, buttons, self._sticky_buttons)
            self._request_debounced_refresh()

        for label in ["L", "R", "T", "B", "C"]:
            is_active = False
            if label == "L" and "left" in align: is_active = True
            elif label == "R" and "right" in align: is_active = True
            elif label == "T" and "top" in align: is_active = True
            elif label == "B" and "bottom" in align: is_active = True
            elif label == "C" and not align: is_active = True

            color = "#33A1FD" if is_active else "#444444"
            btn = tk.Button(btn_frame, text=label, width=3, bg=color, fg="white", 
                      relief="flat", font=("Arial", 8, "bold"),
                      command=lambda l=label: set_align(l))
            btn.pack(side="left", padx=2)
            buttons[label] = btn
        self._align_buttons = buttons

    def _render_sticky_quick_tools(self, data, container):
        """Specialized UI for NSEW sticky (Stretching)."""
        tk.Label(container, text="QUICK STICKY (STRETCH)", bg="#252525", fg="#888888", font=("Arial", 7, "bold")).pack()
        
        btn_frame = tk.Frame(container, bg="#252525")
        btn_frame.pack(pady=5)

        layout = data.get("layout", {})
        align = str(layout.get("align", "")).lower()
        stretch = str(layout.get("stretch", "")).lower()
        
        buttons = {}

        def set_sticky_preset(mode):
            current_data = state_manager.get_value_at_path(self.focused_path)
            curr_layout = current_data.get("layout", {})
            curr_align = set(str(curr_layout.get("align", "")).lower().split())
            curr_stretch = set(str(curr_layout.get("stretch", "")).lower().split())
            
            new_mode = mode.lower()
            if new_mode == "width":
                if "width" in curr_stretch: curr_stretch.discard("width")
                elif "both" in curr_stretch: curr_stretch.discard("both"); curr_stretch.add("height")
                else: 
                    curr_stretch.add("width")
                    curr_align.discard("left")
                    curr_align.discard("right")
            elif new_mode == "height":
                if "height" in curr_stretch: curr_stretch.discard("height")
                elif "both" in curr_stretch: curr_stretch.discard("both"); curr_stretch.add("width")
                else: 
                    curr_stretch.add("height")
                    curr_align.discard("top")
                    curr_align.discard("bottom")
            elif new_mode == "both":
                if "both" in curr_stretch: curr_stretch.clear()
                else: 
                    curr_stretch = {"both"}
                    curr_align.clear()
            else: # NONE
                curr_stretch.clear()

            new_align = " ".join(sorted(list(curr_align)))
            new_stretch = " ".join(sorted(list(curr_stretch)))
            
            l_path = f"{self.focused_path}.layout"
            if "layout" not in current_data:
                state_manager.update_state({"align": new_align, "stretch": new_stretch}, path=l_path, source=self)
            else:
                state_manager.update_state(new_align, path=f"{l_path}.align", source=self)
                state_manager.update_state(new_stretch, path=f"{l_path}.stretch", source=self)
            
            self._update_tool_highlights(new_align, new_stretch, self._align_buttons, buttons)
            self._request_debounced_refresh()

        # Presets
        presets = [("EW", "width"), ("NS", "height"), ("NSEW", "both"), ("NONE", "")]
        for label, val in presets:
            is_active = (val in stretch) or (label == "NONE" and not stretch)
            color = "#2ecc71" if is_active else "#444444"
            btn = tk.Button(btn_frame, text=label, width=5, bg=color, fg="white", 
                      relief="flat", font=("Arial", 7, "bold"),
                      command=lambda v=val: set_sticky_preset(v))
            btn.pack(side="left", padx=2)
            buttons[label] = btn
        self._sticky_buttons = buttons

    def _update_tool_highlights(self, align_str, stretch_str, align_btns, sticky_buttons):
        """Helper to sync button colors without a full re-render."""
        a = set(align_str.split())
        s = set(stretch_str.split())
        
        for label, btn in align_btns.items():
            active = False
            if label == "L" and "left" in a: active = True
            elif label == "R" and "right" in a: active = True
            elif label == "T" and "top" in a: active = True
            elif label == "B" and "bottom" in a: active = True
            elif label == "C" and not a: active = True
            btn.config(bg="#33A1FD" if active else "#444444")
            
        for label, btn in sticky_buttons.items():
            active = False
            if label == "EW" and ("width" in s or "both" in s): active = True
            elif label == "NS" and ("height" in s or "both" in s): active = True
            elif label == "NSEW" and "both" in s: active = True
            elif label == "NONE" and not s: active = True
            btn.config(bg="#2ecc71" if active else "#444444")

    def _render_missing_library_properties(self, data):
        """No longer used directly as main pass now proactive, but keeping for standalone adds."""
        pass

    def _render_recursive_properties(self, data, parent, prefix="", depth=0, actual_data=None):
        """Recursively renders all properties with collapsible headers and structural controls."""
        if actual_data is None: actual_data = {}
        if depth > 5:
            tk.Label(parent, text="... (Depth Limit Reached)", bg="#2b2b2b", fg="#ffaa00").pack(fill="x")
            return

        MAX_KEYS = 100
        key_count = 0
        
        for key, value in data.items():
            key_count += 1
            if key_count > MAX_KEYS:
                tk.Label(parent, text=f"... and {len(data) - MAX_KEYS} more keys", bg="#2b2b2b", fg="#ffaa00").pack(fill="x")
                break

            full_path = f"{prefix}.{key}"
            is_virtual = (key not in actual_data)
            
            if isinstance(value, dict):
                # Section Header
                h_frame = tk.Frame(parent, bg="#3a3a3a", pady=2)
                h_frame.pack(fill="x", pady=(5, 2))
                is_expanded = tk.BooleanVar(value=True)
                
                w_type = value.get("type", value.get("widget_type", ""))
                is_block = (w_type == "OcaBlock")
                type_emoji = "📦" if is_block else "🔹"
                
                # Visual distinction for virtual sections
                fg_col = "#aaaaaa" if not is_virtual else "#666666"
                
                toggle_lbl = tk.Label(h_frame, text="▼", bg="#3a3a3a", fg="#33A1FD", font=("Arial", 8))
                toggle_lbl.pack(side="left", padx=(5, 2))
                tk.Label(h_frame, text=type_emoji, bg="#3a3a3a", font=("Arial", 8)).pack(side="left", padx=(0, 5))
                title_lbl = tk.Label(h_frame, text=key.upper(), bg="#3a3a3a", fg=fg_col, font=("Arial", 8, "bold"), cursor="hand2")
                title_lbl.pack(side="left")

                if is_virtual:
                    def add_block(p=full_path, v=value):
                        state_manager.update_state(v, path=p, source=self)
                        self._refresh_content()
                    tk.Button(h_frame, text="+ ADD SECTION", bg="#2ecc71", fg="white", relief="flat", 
                              font=("Arial", 6, "bold"), command=add_block).pack(side="right", padx=5)
                else:
                    # Normal controls for existing blocks
                    if ".fields." in full_path or full_path.count(".") == 0:
                        ctrl_frame = tk.Frame(h_frame, bg="#3a3a3a")
                        ctrl_frame.pack(side="right", padx=5)
                        ttk.Button(ctrl_frame, text="↑", width=2, command=lambda p=full_path: state_manager.reorder_element(p, "up", source=self)).pack(side="left", padx=1)
                        ttk.Button(ctrl_frame, text="↓", width=2, command=lambda p=full_path: state_manager.reorder_element(p, "down", source=self)).pack(side="left", padx=1)
                
                child_container = tk.Frame(parent, bg="#2b2b2b", padx=15)
                child_container.pack(fill="x")
                
                def _toggle(event, container=child_container, var=is_expanded, lbl=toggle_lbl):
                    if var.get():
                        container.pack_forget(); lbl.config(text="▶"); var.set(False)
                    else:
                        container.pack(fill="x"); lbl.config(text="▼"); var.set(True)
                
                title_lbl.bind("<Button-1>", _toggle)
                toggle_lbl.bind("<Button-1>", _toggle)
                self._render_recursive_properties(value, child_container, prefix=full_path, depth=depth + 1, actual_data=actual_data.get(key, {}))
                
            elif isinstance(value, list):
                f = tk.Frame(parent, bg="#2b2b2b")
                f.pack(fill="x", pady=2)
                tk.Label(f, text=f"{key}:", bg="#2b2b2b", fg="#888888", width=15, anchor="e").pack(side="left")
                tk.Label(f, text=f"[List: {len(value)} items]", bg="#2b2b2b", fg="#666666").pack(side="left", padx=10)
            else:
                self._render_leaf_editor(key, value, parent, full_path, is_virtual=is_virtual)

    def _move_out(self, path):
        parts = path.split(".")
        if len(parts) < 3: return
        target_parts = parts[:-2] 
        state_manager.move_element(path, target_parts, source=self)

    def _move_in(self, path):
        parts = path.split(".")
        key = parts[-1]
        parent_path = ".".join(parts[:-1])
        parent_data = state_manager.get_value_at_path(parent_path)
        if not isinstance(parent_data, dict): return
        keys = list(parent_data.keys())
        idx = keys.index(key)
        if idx == 0: return
        prev_key = keys[idx-1]
        prev_sibling = parent_data[prev_key]
        if isinstance(prev_sibling, dict) and prev_sibling.get("type") == "OcaBlock":
            target_path = f"{parent_path}.{prev_key}.fields"
            state_manager.move_element(path, target_path, source=self)

    def _render_leaf_editor(self, key, value, parent, full_path, is_virtual=False):
        f = tk.Frame(parent, bg="#2b2b2b")
        f.pack(fill="x", pady=2)
        
        # Virtual parameters are greyed out until added
        fg_col = "#cccccc" if not is_virtual else "#555555"
        lbl = tk.Label(f, text=f"{key}:", bg="#2b2b2b", fg=fg_col, width=15, anchor="e")
        lbl.pack(side="left")
        
        if is_virtual:
            def add_prop(p=full_path, v=value):
                state_manager.update_state(v, path=p, source=self)
                self._refresh_content()
            tk.Button(f, text="+ ADD", bg="#3a3a3a", fg="#aaaaaa", relief="flat", 
                      font=("Arial", 7, "bold"), command=add_prop).pack(side="left", padx=10)
            tk.Label(f, text=f"({value})", bg="#2b2b2b", fg="#444444", font=("Arial", 7, "italic")).pack(side="left")
            return

        is_color = False
        val_str = str(value).lower().strip()
        if "color" in key.lower() or "colour" in key.lower(): is_color = True
        elif val_str.startswith("#") and (len(val_str) == 4 or len(val_str) == 7): is_color = True

        if is_color:
            # 🛡️ INDUSTRIAL STABILITY: Handle non-standard color names
            s_bg = val_str
            if s_bg == "transparent" or not s_bg.startswith("#"):
                s_bg = "#2b2b2b" # Safe theme fallback
                
            try:
                swatch = tk.Canvas(f, width=25, height=18, bg=s_bg, highlightthickness=1, highlightbackground="#444444", cursor="hand2")
            except:
                swatch = tk.Canvas(f, width=25, height=18, bg="#2b2b2b", highlightthickness=1, highlightbackground="#444444", cursor="hand2")
            
            swatch.pack(side="left", padx=(10, 5))
            entry = ttk.Entry(f, style="Property.TEntry")
            entry.insert(0, str(value))
            entry.pack(side="left", fill="x", expand=True)

            def _pick_color(event, p=full_path, s=swatch, en=entry, k=key):
                initial = en.get() or "#ffffff"
                color = colorchooser.askcolor(title=f"Pick Color for {key}", initialcolor=initial)
                if color[1]:
                    new_col = color[1]
                    try: s.config(bg=new_col)
                    except: pass
                    en.delete(0, tk.END)
                    en.insert(0, new_col)
                    state_manager.update_state(new_col, path=p, source=self)
            swatch.bind("<Button-1>", _pick_color)
        else:
            lbl.config(cursor="sb_h_double_arrow")
            entry = ttk.Entry(f, style="Property.TEntry")
            entry.insert(0, str(value))
            entry.pack(side="left", fill="x", expand=True, padx=(10, 0))

            if isinstance(value, (int, float)):
                def _start_scrub(e, val=value, k=key):
                    self.scrub_start_val = val
                    self.scrub_start_x = e.x_root
                def _do_scrub(e, en=entry, k=full_path, is_float=isinstance(value, float), kn=key):
                    delta = (e.x_root - self.scrub_start_x) // 2
                    new_v = self.scrub_start_val + (delta * 0.1 if is_float else delta)
                    en.delete(0, tk.END)
                    en.insert(0, f"{new_v:.3f}".rstrip('0').rstrip('.') if is_float else str(int(new_v)))
                    state_manager.update_state(new_v, path=k, source=self)
                lbl.bind("<Button-1>", _start_scrub)
                lbl.bind("<B1-Motion>", _do_scrub)

        def _on_focus_in(e): f.config(bg="#444444"); lbl.config(bg="#444444", fg="#33A1FD")
        def _on_focus_out(e, k=full_path, en=entry, kn=key):
            f.config(bg="#2b2b2b"); lbl.config(bg="#2b2b2b", fg="#cccccc")
            try:
                v = en.get()
                if v.lower() == "true": final = True
                elif v.lower() == "false": final = False
                elif v.startswith("#"): final = v 
                else: final = float(v) if "." in v else int(v)
                if final != value:
                    state_manager.update_state(final, path=k, source=self)
            except: pass

        entry.bind("<FocusIn>", _on_focus_in)
        entry.bind("<FocusOut>", _on_focus_out)
        entry.bind("<Return>", lambda e: self.focus_set())
