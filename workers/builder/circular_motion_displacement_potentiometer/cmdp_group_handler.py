# workers/builder/circular_motion_displacement_potentiometer/cmdp_group_handler.py
import tkinter as tk
from tkinter import colorchooser, simpledialog

class CMDPGroupHandler:
    """Handles group metadata, sidebar UI, and group-level actions."""
    def __init__(self, widget_ref):
        self.w = widget_ref # CMDPWidget reference
        self.group_mute_vars = {} # group_name -> BooleanVar
        
        # UI Element storage moved here to ensure consistency
        self.group_buttons = {}      # Visibility buttons (Eye)
        self.group_mute_buttons = {}   # Mute buttons (Speaker)
        self.group_labels = {}       # Group name labels
        
        # Initialize context menu
        self.groups_menu = tk.Menu(self.w, tearoff=0, bg="#333", fg="white", activebackground="#f4902c")
        self.groups_menu.add_command(label="Add Group", command=self.add_new_group_dialog)

    def add_new_group_dialog(self):
        name = simpledialog.askstring("Add Group", "Group Name:")
        if name: self.add_group_ui(name, "#00FF00")

    def add_group_ui(self, group_name, color, initial_visible=True, initial_mute=False):
        if group_name in self.w.group_vars: return
        
        bp = f"{self.w.path}/groups/{group_name}"
        fr = tk.Frame(self.w.groups_container)
        fr.pack(fill=tk.X, padx=1, pady=1)
        
        # Sync bg immediately
        fr.config(bg=self.w.groups_container.cget("bg"))
        
        iv = tk.BooleanVar(value=initial_visible)
        im = tk.BooleanVar(value=initial_mute)
        cv = tk.StringVar(value=color)
        nv = tk.StringVar(value=group_name)
        
        self.w.group_vars[group_name] = iv
        self.group_mute_vars[group_name] = im
        self.w.group_color_vars[group_name] = cv
        self.w.group_name_vars[group_name] = nv
        
        # SME Registration
        if self.w.mixin_ref.state_mirror_engine:
            sme = self.w.mixin_ref.state_mirror_engine
            sme.register_widget(f"{bp}/visible", iv, self.w.base_mqtt_topic, {"type": "_CMDP_GrpVis"})
            sme.register_widget(f"{bp}/mute", im, self.w.base_mqtt_topic, {"type": "_CMDP_GrpMute"})
            sme.register_widget(f"{bp}/color", cv, self.w.base_mqtt_topic, {"type": "_CMDP_GrpCol"})
            sme.register_widget(f"{bp}/name", nv, self.w.base_mqtt_topic, {"type": "_CMDP_GrpName"})
            def _bc(p):
                if not getattr(sme, "_silent_update", False): sme.broadcast_gui_change_to_mqtt(p)
            iv.trace_add("write", lambda *a: _bc(f"{bp}/visible"))
            im.trace_add("write", lambda *a: _bc(f"{bp}/mute"))
            cv.trace_add("write", lambda *a: _bc(f"{bp}/color"))
            nv.trace_add("write", lambda *a: _bc(f"{bp}/name"))
            for p, v in [("visible", iv), ("mute", im), ("color", cv), ("name", nv)]:
                t = sme.get_widget_topic(f"{bp}/{p}")
                if self.w.mixin_ref.subscriber_router and t: self.w.mixin_ref.subscriber_router.subscribe_to_topic(t, sme.sync_incoming_mqtt_to_gui)
                sme.initialize_widget_state(f"{bp}/{p}")

        # UI Elements
        b_vis = tk.Button(fr, text="👁", bg="#f4902c", fg="black", width=1, bd=0, font=("Arial", 7), command=lambda: iv.set(not iv.get()))
        b_vis.pack(side=tk.LEFT, padx=1)
        b_vis.bind("<Alt-Button-1>", lambda e: self.solo_group_visibility(group_name))
        b_vis.bind("<Control-Button-1>", lambda e: self.show_all_groups())
        self.group_buttons[group_name] = b_vis
        
        b_mute = tk.Button(fr, text="🔊", bg="#f4902c", fg="black", width=1, bd=0, font=("Arial", 7), command=lambda: self.toggle_group_mute(group_name))
        b_mute.pack(side=tk.LEFT, padx=1)
        b_mute.bind("<Alt-Button-1>", lambda e: self.solo_group_mute(group_name))
        b_mute.bind("<Control-Button-1>", lambda e: self.unmute_all_groups())
        self.group_mute_buttons[group_name] = b_mute
        
        lbl = tk.Label(fr, textvariable=nv, fg=color, anchor="w", cursor="hand2", font=("Arial", 8, "bold"))
        lbl.config(bg=fr.cget("bg"))
        lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        self.group_labels[group_name] = lbl
        
        def sync_row_bg():
            bg = self.w.groups_container.cget("bg")
            fr.config(bg=bg)
            lbl.config(bg=bg)
            
        # Hook into main draw if possible, or just rely on initial set. 
        # Since rows are added dynamically, we need a way to update them if the main bg changes.
        # We can monkey-patch a 'sync_bg' method on the frame and call it from the main widget loop if we iterate children.
        fr.sync_bg = sync_row_bg
        
        iv.trace_add("write", lambda *a: self._apply_vis(group_name))
        im.trace_add("write", lambda *a: self._apply_group_mute(group_name))
        cv.trace_add("write", lambda *a: self._sync_col(group_name))
        nv.trace_add("write", lambda *a: lbl.config(fg=cv.get() if cv.get() else "#FFFFFF"))
        
        lbl.bind("<Button-1>", lambda e: self.rename_group(group_name))
        lbl.bind("<Double-Button-1>", lambda e: self.pick_group_color(group_name))
        lbl.bind("<Button-2>", lambda e: self.on_group_drag_start(e, group_name))
        lbl.bind("<B2-Motion>", self.on_group_drag_move)
        
        self._apply_vis(group_name)
        self._apply_group_mute(group_name)
        self.w.refresh_pop_tree()

    def solo_group_visibility(self, target_name):
        for gn in self.w.group_vars: self.w.group_vars[gn].set(gn == target_name)

    def show_all_groups(self):
        for gn in self.w.group_vars: self.w.group_vars[gn].set(True)

    def solo_group_mute(self, target_name):
        for gn in self.group_mute_vars: self.group_mute_vars[gn].set(gn != target_name)

    def unmute_all_groups(self):
        for gn in self.group_mute_vars: self.group_mute_vars[gn].set(False)

    def toggle_group_mute(self, group_name):
        self.group_mute_vars[group_name].set(not self.group_mute_vars[group_name].get())

    def _apply_group_mute(self, group_name):
        muted = self.group_mute_vars[group_name].get()
        if group_name in self.group_mute_buttons:
            self.group_mute_buttons[group_name].config(text="🔈" if muted else "🔊", bg="#444" if muted else "#f4902c", fg="white" if muted else "black")
        for f in self.w.faders:
            if f.group_name == group_name:
                f.mute_var.set(muted)
                if self.w.mixin_ref.state_mirror_engine:
                    idx = self.w.faders.index(f)
                    self.w.mixin_ref.state_mirror_engine.broadcast_gui_change_to_mqtt(f"{self.w.path}/ch{idx}/mute")
        self.w.refresh_pop_tree()

    def _sync_col(self, name):
        c = self.w.group_color_vars[name].get(); self.group_labels[name].config(fg=c)
        for f in self.w.faders:
            if f.group_name == name: f.color_highlight = c; f.render()

    def _apply_vis(self, name):
        v = self.w.group_vars[name].get()
        if name in self.group_buttons: self.group_buttons[name].config(bg="#f4902c" if v else "#444", fg="black" if v else "white")
        for f in self.w.faders:
            if f.group_name == name: f.visible = v; f.render()
        self.w.refresh_pop_tree()

    def rename_group(self, old):
        new = simpledialog.askstring("Rename", f"New name for '{old}':", initialvalue=self.w.group_name_vars[old].get())
        if new and new != old: self.w.group_name_vars[old].set(new); self.w.refresh_pop_tree()

    def pick_group_color(self, name):
        c = colorchooser.askcolor(initialcolor=self.w.group_color_vars[name].get(), title=f"Color for {name}")
        if c[1]: self.w.group_color_vars[name].set(c[1])

    def on_group_drag_start(self, event, group_name): self.w._group_drag_data = {"name": group_name, "x": event.x_root}

    def on_group_drag_move(self, event):
        if hasattr(self.w, "_group_drag_data"):
            gn = self.w._group_drag_data["name"]
            dx = event.x_root - self.w._group_drag_data["x"]; rot_delta = dx * 0.5
            for f in self.w.faders:
                if f.group_name == gn: f.angle_var.set(float(f.angle_var.get()) + rot_delta); self.w.update_tree(f)
            self.w._group_drag_data["x"] = event.x_root
