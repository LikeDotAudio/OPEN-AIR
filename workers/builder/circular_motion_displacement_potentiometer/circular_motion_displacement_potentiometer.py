# workers/builder/circular_motion_displacement_potentiometer/Builder_CMDP.py
import tkinter as tk
from tkinter import ttk
import math
# --- Standard Debug Logging Setup ---
BUILDER_DEBUG = True    # Set to False in production, True for dev on this file
from workers.logger.logger import initialize_logging, set_log_directory, builder_logger
from loguru import logger

# --- Component Imports ---
from managers.Display.transparency.transparency_mixin import TransparencyMixin
from managers.Display.factory.widget_registry import WidgetRegistry
from workers.builder.circular_motion_displacement_potentiometer.cmdp_group_handler import CMDPGroupHandler
from workers.builder.circular_motion_displacement_potentiometer.cmdp_file_handler import CMDPFileHandler
from workers.builder.circular_motion_displacement_potentiometer.cmdp_channel_handler import CMDP_LTPObject

class CMDPWidget(tk.Frame, TransparencyMixin):
    """Coordinator for the CMDP widget, delegating logic to specialized handlers."""
    def __init__(self, master, config, mixin_ref, **kwargs):
        self.path = kwargs.pop("path", config.get("path", ""))
        self.base_mqtt_topic = kwargs.pop("base_mqtt_topic_from_path", "")
        super().__init__(master, **{k: v for k, v in kwargs.items() if k in ["bg", "background", "padx", "pady"]})
        
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🕹️ [BUILDER] Initializing CMDPWidget")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config}")

        self.widget_config, self.mixin_ref = config, mixin_ref
        self.faders, self.active_fader, self.hovered_fader = [], None, None
        self.tree_window, self.pop_tree = None, None
        self.center_x, self.center_y, self.near_radius, self.far_radius = 500, 500, 120, 380
        
        self.show_groups_var = tk.BooleanVar(value=True)
        self.show_channels_var = tk.BooleanVar(value=False)
        
        self.group_vars, self.group_color_vars, self.group_name_vars = {}, {}, {}
        self.group_buttons, self.group_labels = {}, {}
        
        # Instantiate Handlers
        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🗂️⚙️ [CONSTRUCT] Instantiating specialized CMDP handlers.")
        self.gh = CMDPGroupHandler(self)
        self.fh = CMDPFileHandler(self)
        
        self._setup_ui()

    def _setup_ui(self):
        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🪟🎨 [SCAFFOLD] Setting up CMDP grid layout and sidebar components.")
        # Configure Grid to exploit vertical space
        self.grid_columnconfigure(0, weight=1) # Canvas
        self.grid_columnconfigure(1, weight=0) # Sidebar
        self.grid_rowconfigure(0, weight=1)    # Canvas/Sidebar Row
        self.grid_rowconfigure(1, weight=0)    # Control Bar Row (Static height)
        
        # Canvas
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Apply Industrial Transparency
        if self.mixin_ref and hasattr(self.mixin_ref, '_apply_transparency'):
            if BUILDER_DEBUG: builder_logger.trace(f"👻🌀🪟 [ALPHA] Applying industrial transparency to CMDP canvas.")
            self.mixin_ref._apply_transparency(self, self.canvas, self.widget_config, self.mixin_ref)

        # --- Main Layout Area (Row 0) ---
        # Sidebar
        self.sidebar = tk.Frame(self, width=125)
        self.sidebar.grid(row=0, column=1, sticky="nsew")
        self.sidebar.pack_propagate(False)
        
        self.sidebar_controls = tk.Frame(self.sidebar)
        self.sidebar_controls.pack(side=tk.TOP, fill=tk.X, pady=2)
        
        self.btn_toggle_groups = tk.Button(self.sidebar_controls, text="Groups", bg="#f4902c", fg="black", font=("Arial", 7, "bold"), bd=1, relief="flat", command=self.toggle_groups_pane)
        self.btn_toggle_groups.pack(side=tk.TOP, fill=tk.X, padx=5, pady=1)
        self.btn_toggle_groups.bind("<Button-3>", lambda e: self.gh.groups_menu.post(e.x_root, e.y_root))

        self.groups_pane = tk.Frame(self.sidebar)
        self.groups_pane.pack(side=tk.TOP, fill=tk.BOTH, expand=False)
        self.groups_container = tk.Frame(self.groups_pane)
        self.groups_container.pack(fill=tk.BOTH, expand=True)
        
        self.btn_toggle_channels = tk.Button(self, text="Channels", bg="#f4902c", fg="black", font=("Arial", 7, "bold"), bd=1, relief="flat", command=self.toggle_channels_pane)
        self.btn_toggle_channels.place(relx=0.005, rely=0.005, anchor="nw")
        
        if BUILDER_DEBUG: builder_logger.trace("🖱️👆🔗 [EVENTS] Binding input protocols to main CMDP canvas.")
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-2>", self.on_mid_click)
        self.canvas.bind("<B2-Motion>", self.on_mid_drag)
        self.canvas.bind("<ButtonRelease-2>", self.on_release)
        self.canvas.bind("<Button-4>", self.on_scroll)
        self.canvas.bind("<Button-5>", self.on_scroll)
        self.canvas.bind("<MouseWheel>", self.on_scroll)
        self.canvas.bind("<Motion>", self.on_motion)
        
        # --- Control Bar (Row 1) ---
        self.ctrl_bar = tk.Frame(self) # Height determined by content
        self.ctrl_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        tk.Button(self.ctrl_bar, text="Revert to Defaults", bg="#f4902c", fg="black", font=("Arial", 8, "bold"), 
                  bd=1, relief="flat", command=self.revert_to_defaults).pack(side=tk.LEFT, padx=10, pady=2)
        
        tk.Button(self.ctrl_bar, text="Import JSON", bg="#444", fg="white", font=("Arial", 8, "bold"), 
                  bd=1, relief="flat", command=self.fh.import_json).pack(side=tk.LEFT, padx=5, pady=2)
        
        tk.Button(self.ctrl_bar, text="Export JSON", bg="#444", fg="white", font=("Arial", 8, "bold"), 
                  bd=1, relief="flat", command=self.fh.export_json).pack(side=tk.LEFT, padx=5, pady=2)

        def sync_bg():
            bg = self.canvas.cget("bg")
            self.sidebar.config(bg=bg)
            self.sidebar_controls.config(bg=bg)
            self.groups_pane.config(bg=bg)
            self.groups_container.config(bg=bg)
            self.ctrl_bar.config(bg=bg)
            self.draw_static_ui()
            for f in self.faders: f.render()

        self._draw = sync_bg
        self.draw_static_ui()

    def add_group_ui(self, name, color, initial_visible=True):
        self.gh.add_group_ui(name, color, initial_visible)

    def on_canvas_resize(self, event):
        """Update center coordinates and redraw when canvas is resized."""
        if BUILDER_DEBUG: builder_logger.debug(f"📐📏🔄 [LAYOUT] CMDP canvas resizing to {event.width}x{event.height}")
        self.center_x, self.center_y = event.width // 2, event.height // 2
        
        # Scale radii proportionally to size - Use more vertical space
        size = min(event.width, event.height)
        self.near_radius = size * 0.12
        self.far_radius = size * 0.45
        
        self.draw_static_ui()
        for f in self.faders: f.update_position_and_render()

    def toggle_groups_pane(self):
        iv = not self.show_groups_var.get(); self.show_groups_var.set(iv)
        if BUILDER_DEBUG: builder_logger.info(f"🔄🗂️🔳 [VIEW] Toggling CMDP groups pane: {iv}")
        if iv: 
            self.groups_pane.pack(side=tk.TOP, fill=tk.BOTH, expand=False, after=self.sidebar_controls)
            self.btn_toggle_groups.config(text="Groups ON", bg="#f4902c", fg="black")
        else: 
            self.groups_pane.pack_forget()
            self.btn_toggle_groups.config(text="Groups OFF", bg="#444", fg="white")

    def toggle_channels_pane(self):
        is_vis = not self.show_channels_var.get(); self.show_channels_var.set(is_vis)
        if BUILDER_DEBUG: builder_logger.info(f"🔄📑🔳 [VIEW] Toggling CMDP channel tree window: {is_vis}")
        if is_vis:
            self.tree_window = tk.Toplevel(self); self.tree_window.title("Channel Tree"); self.tree_window.geometry("600x700"); self.tree_window.configure(bg="#222")
            self.tree_window.protocol("WM_DELETE_WINDOW", self.toggle_channels_pane)
            
            style = ttk.Style(self.tree_window)
            style.configure("CMDP_Pop.Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
            style.map("CMDP_Pop.Treeview", background=[('selected', '#f4902c')], foreground=[('selected', 'black')])
            
            cols = ("Name", "Mute", "Level", "Depth", "Angle", "ID")
            self.pop_tree = ttk.Treeview(self.tree_window, columns=cols, show="tree headings", style="CMDP_Pop.Treeview")
            self.pop_tree.heading("#0", text="Groups")
            for c in cols: self.pop_tree.heading(c, text=c); self.pop_tree.column(c, width=70, anchor="center")
            self.pop_tree.pack(fill=tk.BOTH, expand=True)
            self.refresh_pop_tree()
            
            self.pop_tree.bind("<Button-1>", self._on_tree_click)
            self.pop_tree.bind("<B1-Motion>", self._on_tree_drag)
            self.pop_tree.bind("<ButtonRelease-1>", self._on_tree_release)
            self.pop_tree.bind("<Control-Up>", lambda e: self._move_channel_keyboard("up"))
            self.pop_tree.bind("<Control-Down>", lambda e: self._move_channel_keyboard("down"))

            self.btn_toggle_channels.config(text="Channels ON", bg="#f4902c", fg="black")
        else:
            if self.tree_window: self.tree_window.destroy(); self.tree_window, self.pop_tree = None, None
            self.btn_toggle_channels.config(text="Channels OFF", bg="#444", fg="white")

    def _on_tree_click(self, event):
        item = self.pop_tree.identify_row(event.y); col = self.pop_tree.identify_column(event.x)
        if not item: return
        if col == "#2":
            if item.startswith("ch_"):
                ch_idx = int(item[3:]); f = self.faders[ch_idx]; f.mute_var.set(not f.mute_var.get())
            elif item.startswith("grp_"):
                gn = item[4:]; self.gh.toggle_group_mute(gn)
            self.refresh_pop_tree(); return
        if item.startswith("ch_") and col in ("#3", "#4", "#5"):
            self._spawn_edit_entry(item, col, event); return
        if item.startswith("ch_"): self._drag_item = item
        else: self._drag_item = None

    def _spawn_edit_entry(self, item, col, event):
        x, y, w, h = self.pop_tree.bbox(item, col); ch_idx = int(item[3:]); f = self.faders[ch_idx]
        var = f.rot_var if col == "#3" else f.val_var if col == "#4" else f.angle_var
        entry = tk.Entry(self.pop_tree, bg="white", fg="black", justify="center")
        entry.insert(0, str(int(float(var.get())))); entry.place(x=x, y=y, width=w, height=h); entry.focus_set(); entry.select_range(0, tk.END)
        def _save(event=None):
            try:
                val = float(entry.get()); var.set(val)
                if self.mixin_ref.state_mirror_engine:
                    p = "rot" if col == "#3" else "val" if col == "#4" else "angle"
                    self.mixin_ref.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{self.path}/ch{ch_idx}/{p}")
                self.refresh_pop_tree()
            except: pass
            entry.destroy()
        def _cancel(event=None): entry.destroy()
        entry.bind("<Return>", _save); entry.bind("<Escape>", _cancel); entry.bind("<FocusOut>", _save)

    def _move_channel_keyboard(self, direction):
        sel = self.pop_tree.selection()
        if not sel or not sel[0].startswith("ch_"): return
        ch_idx = int(sel[0][3:]); f = self.faders[ch_idx]; all_grps = list(self.group_name_vars.keys())
        try: curr_idx = all_grps.index(f.group_name)
        except: curr_idx = 0
        next_idx = max(0, curr_idx - 1) if direction == "up" else min(len(all_grps) - 1, curr_idx + 1)
        if next_idx != curr_idx:
            new_grp = all_grps[next_idx]; f.group_name = new_grp; f.color_highlight = self.group_color_vars[new_grp].get()
            self.refresh_pop_tree(); f.render(); self.pop_tree.selection_set(f"ch_{ch_idx}"); self.pop_tree.see(f"ch_{ch_idx}")

    def _on_tree_drag(self, event):
        if hasattr(self, "_drag_item") and self._drag_item: self.pop_tree.configure(cursor="hand2")

    def _on_tree_release(self, event):
        if hasattr(self, "_drag_item") and self._drag_item:
            target = self.pop_tree.identify_row(event.y)
            if target and target.startswith("grp_"):
                new_grp = target[4:]; ch_idx = int(self._drag_item[3:]); f = self.faders[ch_idx]
                f.group_name = new_grp; f.color_highlight = self.group_color_vars[new_grp].get()
                self.refresh_pop_tree(); f.render()
            self.pop_tree.configure(cursor=""); self._drag_item = None

    def refresh_pop_tree(self):
        if not self.pop_tree: return
        self.pop_tree.delete(*self.pop_tree.get_children())
        for gn in self.group_name_vars:
            group_muted = all(f.mute_var.get() for f in self.faders if f.group_name == gn)
            g_icon = "☐ Muted" if group_muted else "☑ Active"
            self.pop_tree.insert("", "end", iid=f"grp_{gn}", text=gn, values=("(Group)", g_icon, "", "", "", ""), open=True)
        for i, f in enumerate(self.faders):
            p = f"grp_{f.group_name}" if f"grp_{f.group_name}" in self.pop_tree.get_children("") else ""
            m_icon = "☐ Muted" if f.mute_var.get() else "☑ Active"
            self.pop_tree.insert(p, "end", iid=f"ch_{i}", text="", values=(f.label, m_icon, int(float(f.rot_var.get())), int(float(f.val_var.get())), int(float(f.angle_var.get())), i+1))

    def revert_to_defaults(self):
        for i, f in enumerate(self.faders):
            cfg = self.widget_config.get("channels", [])[i]
            f.val_var.set(cfg.get("depth", 50.0)); f.rot_var.set(cfg.get("level", 50.0)); f.angle_var.set(cfg.get("angle", 0.0)); f.mute_var.set(False)
            if self.mixin_ref.state_mirror_engine:
                fp = f"{self.path}/ch{i}"
                for p in ["val", "rot", "angle", "mute"]: self.mixin_ref.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{fp}/{p}")
            self.update_tree(f); self.refresh_pop_tree()

    def draw_static_ui(self):
        self.canvas.delete("static_ui"); cx, cy, n, f = self.center_x, self.center_y, self.near_radius, self.far_radius; accent = "#f4902c"
        self.canvas.create_oval(cx-n, cy-n, cx+n, cy+n, outline=accent, dash=(5,5), width=2, tags="static_ui")
        self.canvas.create_oval(cx-f, cy-f, cx+f, cy+f, outline=accent, dash=(5,5), width=2, tags="static_ui")
        r = 40; self.canvas.create_oval(cx-r-10, cy-15, cx-r+5, cy+15, fill="#444", outline=accent, width=2, tags="static_ui")
        self.canvas.create_oval(cx+r-5, cy-15, cx+r+10, cy+15, fill="#444", outline=accent, width=2, tags="static_ui")
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#444", outline=accent, width=2, tags="static_ui")
        self.canvas.create_polygon(cx, cy-r-15, cx-10, cy-r+5, cx+10, cy-r+5, fill=accent, tags="static_ui")

    def get_fader_at(self, x, y):
        ids = self.canvas.find_closest(x, y, halo=20)
        if not ids: return None
        for t in self.canvas.gettags(ids[0]):
            if t.startswith("cmdp_fader_"): return next((f for f in self.faders if f.widget_id == int(t.split("_")[-1])), None)
        return None

    def on_click(self, e):
        f = self.get_fader_at(e.x, e.y)
        if f: self.active_fader = f; f.dragging = True; f.lift(); f.start_val, f.start_x, f.start_y = float(f.val_var.get()), e.x, e.y

    def on_drag(self, e):
        f = self.active_fader
        if f and f.dragging:
            if (e.state & 0x0008) or (e.state & 0x20000): f.angle_var.set(math.degrees(math.atan2(e.y-self.center_y, e.x-self.center_x)))
            else:
                rad = math.radians(float(f.angle_var.get())); proj = (e.x-f.start_x)*math.cos(rad) + (e.y-f.start_y)*math.sin(rad)
                f.val_var.set(max(0, min(100, f.start_val - (proj/f.track_len)*100)))
            self.update_tree(f)

    def on_mid_click(self, e):
        f = self.get_fader_at(e.x, e.y)
        if f: self.active_fader = f; f.dragging = True

    def on_mid_drag(self, e):
        f = self.active_fader
        if f and f.dragging: f.angle_var.set(math.degrees(math.atan2(e.y-self.center_y, e.x-self.center_x))); self.update_tree(f)

    def on_release(self, e):
        if self.active_fader: self.active_fader.dragging = False; self.active_fader = None

    def on_motion(self, e):
        f = self.get_fader_at(e.x, e.y)
        if f != self.hovered_fader:
            if self.hovered_fader: self.hovered_fader.set_hover(False)
            if f: f.set_hover(True); self.hovered_fader = f

    def on_scroll(self, e):
        f = self.get_fader_at(e.x, e.y)
        if f:
            f.lift(); delta = 1 if (e.num == 4 or (hasattr(e, 'delta') and e.delta > 0)) else -1
            is_alt = (e.state & 0x0008) or (e.state & 0x20000)
            if is_alt: f.angle_var.set(float(f.angle_var.get()) + delta * 3)
            else: f.rot_var.set(max(0, min(100, float(f.rot_var.get()) + delta * 5)))
            self.update_tree(f)

    def update_tree(self, f):
        if self.pop_tree and self.pop_tree.winfo_exists():
            try:
                if self.pop_tree.exists(f"ch_{f.widget_id}"):
                    m_icon = "☐ Muted" if f.mute_var.get() else "☑ Active"
                    self.pop_tree.item(f"ch_{f.widget_id}", values=(f.label, m_icon, int(float(f.rot_var.get())), int(float(f.val_var.get())), int(float(f.angle_var.get())), f.widget_id+1))
            except: pass

@WidgetRegistry.register("_CMDP")
class BuilderCircularMotionDisplacementPotentiometerCreator:
    """Mixin to create a Circular/Composite Motion Draggable Potentiometer (CMDP) widget."""
    
    @staticmethod
    def make(parent_widget, config_data, context=None, **kwargs):
        """
        Static factory method for creating a CMDP widget.
        """
        if BUILDER_DEBUG: 
            builder_logger.trace(f"🔬🏗️🕹️ [BUILDER] Entering BuilderCircularMotionDisplacementPotentiometerCreator.make")
            builder_logger.debug(f"📜📑💻 [CONFIG] Raw config received: {config_data}")

        path = config_data.get("path", "")
        
        # ⚡ HARDENED INTERFACE: Extract from context if available
        if BUILDER_DEBUG: builder_logger.trace("🔗🗂️⚙️ [CONTEXT] Extracting engine and router context...")
        if context:
            state_mirror_engine = context.state_mirror_engine
            subscriber_router = context.subscriber_router
            base_mqtt_topic_from_path = context.base_mqtt_topic_from_path
            app_instance = context.app_instance
            builder_instance = context.builder_instance or app_instance
            if BUILDER_DEBUG: builder_logger.debug("✅🆗💻 [CONTEXT] Successfully extracted from WidgetContext object.")
        else:
            state_mirror_engine = kwargs.get("state_mirror_engine")
            subscriber_router = kwargs.get("subscriber_router")
            base_mqtt_topic_from_path = kwargs.get("base_mqtt_topic_from_path", "")
            builder_instance = kwargs.get("builder_instance")
            app_instance = kwargs.get("app_instance")
            if BUILDER_DEBUG: builder_logger.debug("⚠️🔔🖱️ [CONTEXT] Context missing; fell back to kwargs.")

        # Create CMDPWidget instance
        if BUILDER_DEBUG: builder_logger.trace(f"🔬⚡️🕹️ [BUILDER] Spawning CMDPWidget at path '{path}'.")
        cmdp_widget = CMDPWidget(parent_widget, config_data, builder_instance, path=path, base_mqtt_topic_from_path=base_mqtt_topic_from_path, **kwargs)
        
        if state_mirror_engine:
            if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering CMDP UI state variables.")
            state_mirror_engine.register_widget(f"{path}/show_groups", cmdp_widget.show_groups_var, base_mqtt_topic_from_path, {"type": "_CMDP_UI"})
            state_mirror_engine.register_widget(f"{path}/show_channels", cmdp_widget.show_channels_var, base_mqtt_topic_from_path, {"type": "_CMDP_UI"})
            def _bc(p):
                if not getattr(state_mirror_engine, "_silent_update", False): 
                    if BUILDER_DEBUG: builder_logger.debug(f"⚡🔴📡 [EVENT] CMDP UI toggle: {p}. Broadcasting.")
                    state_mirror_engine.broadcast_gui_change_to_mqtt(p)
            cmdp_widget.show_groups_var.trace_add("write", lambda *a: _bc(f"{path}/show_groups")); cmdp_widget.show_channels_var.trace_add("write", lambda *a: _bc(f"{path}/show_channels"))
        
        channels = config_data.get("channels", []); group_configs = { g["name"]: g for g in config_data.get("group_configs", []) }
        if BUILDER_DEBUG: builder_logger.trace(f"🏗️🔳🕹️ [CONSTRUCT] Iterating through {len(channels)} channels for state and object initialization.")
        for i, chan in enumerate(channels):
            group_name = chan.get("group", "Default"); group_cfg = group_configs.get(group_name, {"color": "#00FF00", "visible": True})
            cmdp_widget.add_group_ui(group_name, group_cfg.get("color", "#00FF00"), initial_visible=group_cfg.get("visible", True))
            cid, name = chan.get("id", i + 1), chan.get("name", f"Ch {i+1}")
            f_path = f"{path}/ch{i}"
            v_var, r_var, a_var, m_var = tk.DoubleVar(value=chan.get("depth", 50)), tk.DoubleVar(value=chan.get("level", 50)), tk.DoubleVar(value=chan.get("angle", 0)), tk.BooleanVar(value=chan.get("mute", False))
            if state_mirror_engine:
                if BUILDER_DEBUG: builder_logger.trace(f"📡📶🔗 [MQTT] Registering state for channel {i+1} at path '{f_path}'")
                state_mirror_engine.register_widget(f"{f_path}/val", v_var, base_mqtt_topic_from_path, {"type": "_CMDP_Val", "min": 0, "max": 100})
                state_mirror_engine.register_widget(f"{f_path}/rot", r_var, base_mqtt_topic_from_path, {"type": "_CMDP_Rot", "min": 0, "max": 100})
                state_mirror_engine.register_widget(f"{f_path}/angle", a_var, base_mqtt_topic_from_path, {"type": "_CMDP_Angle", "min": -360, "max": 360})
                state_mirror_engine.register_widget(f"{f_path}/mute", m_var, base_mqtt_topic_from_path, {"type": "_GuiButtonToggle"})
                
                def _bcp(p): 
                    if BUILDER_DEBUG: builder_logger.trace(f"⚡🔴📡 [EVENT] Channel component change: {p}. Broadcasting.")
                    state_mirror_engine.broadcast_gui_change_to_mqtt(p)
                v_var.trace_add("write", lambda *a, p=f"{f_path}/val": _bcp(p))
                r_var.trace_add("write", lambda *a, p=f"{f_path}/rot": _bcp(p))
                a_var.trace_add("write", lambda *a, p=f"{f_path}/angle": _bcp(p))
                m_var.trace_add("write", lambda *a, p=f"{f_path}/mute": _bcp(p))
                
                for p, v in [("val", v_var), ("rot", r_var), ("angle", a_var), ("mute", m_var)]:
                    t = state_mirror_engine.get_widget_topic(f"{f_path}/{p}")
                    if subscriber_router and t: 
                        if BUILDER_DEBUG: builder_logger.debug(f"📥📶🔄 [MQTT] Subscribing channel component to topic: {t}")
                        subscriber_router.subscribe_to_topic(t, state_mirror_engine.sync_incoming_mqtt_to_gui)
                    state_mirror_engine.initialize_widget_state(f"{f_path}/{p}")
            
            f = CMDP_LTPObject(cmdp_widget.canvas, i, group_cfg.get("color", "#00FF00"), i, name, v_var, r_var, a_var, m_var, cmdp_widget.update_tree, cmdp_widget)
            f.group_name = group_name; cmdp_widget.faders.append(f)
            
        if BUILDER_DEBUG: builder_logger.success(f"✅🆗🕹️ [SUCCESS] The Circular Motion Potentiometer has materialized!")
        return cmdp_widget

    def make_circular_motion_displacement_potentiometer(self, parent_widget, config_data, context=None, **kwargs):
        return BuilderCircularMotionDisplacementPotentiometerCreator.make(parent_widget, config_data, context, builder_instance=self, **kwargs)
