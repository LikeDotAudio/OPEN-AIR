"""3D-cloud (graph) tab for the Sample Analyzer.

    X = pitch (Hz)   ·   Y (depth) = name group   ·   Z = complexity / timbre
    point size = sample length   ·   colour = name group (legend)

All methods here become part of AnalyzerApp via the GraphMixin.
"""
import tkinter as tk
from tkinter import ttk

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d import Axes3D, proj3d  # noqa: F401 (registers the 3d projection)
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import CLOUD_PALETTE


class GraphMixin:
    def _build_cloud_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="3D Cloud")

        views = ttk.Frame(tab, padding=(10, 4))
        views.pack(fill=tk.X)
        ttk.Label(views, text="View:", foreground="#888").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(views, text="Top", width=7, command=lambda: self._set_view(90, -90)).pack(side=tk.LEFT, padx=2)
        ttk.Button(views, text="Front", width=7, command=lambda: self._set_view(0, -90)).pack(side=tk.LEFT, padx=2)
        ttk.Button(views, text="Side", width=7, command=lambda: self._set_view(0, 0)).pack(side=tk.LEFT, padx=2)
        ttk.Button(views, text="Iso", width=7, command=lambda: self._set_view(22, -60)).pack(side=tk.LEFT, padx=2)
        ttk.Label(views, text="   (scroll to zoom · drag to orbit · click a point)", foreground="#555").pack(side=tk.LEFT, padx=6)
        self.play_btn = ttk.Button(views, text="▶ Play", width=8, state=tk.DISABLED, command=self._play_selected)
        self.play_btn.pack(side=tk.RIGHT)
        self.sel_label = ttk.Label(views, text="Click a point to inspect", foreground="#c47a1a")
        self.sel_label.pack(side=tk.RIGHT, padx=8)

        body = ttk.Frame(tab)
        body.pack(fill=tk.BOTH, expand=True)

        # --- left sidebar: show/hide groups + isolated-axis picker ---
        side = ttk.Frame(body, width=196)
        side.pack(side=tk.LEFT, fill=tk.Y)
        side.pack_propagate(False)

        ttk.Label(side, text="Groups (show / hide)", font=("Helvetica", 9, "bold")).pack(anchor=tk.W, padx=6, pady=(4, 0))
        btns = ttk.Frame(side)
        btns.pack(fill=tk.X, padx=6, pady=(2, 4))
        ttk.Button(btns, text="All", width=5, command=lambda: self._set_all_groups(True)).pack(side=tk.LEFT)
        ttk.Button(btns, text="None", width=5, command=lambda: self._set_all_groups(False)).pack(side=tk.LEFT, padx=3)

        # Isolated-axis controls pinned to the bottom (own frame — no side mixing).
        bottom = ttk.Frame(side)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=4)
        ttk.Separator(bottom, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 6))
        ttk.Label(bottom, text="Isolate 1 group → axes:", justify=tk.LEFT).pack(anchor=tk.W)
        yrow = ttk.Frame(bottom); yrow.pack(fill=tk.X, pady=1)
        ttk.Label(yrow, text="Y:", width=2).pack(side=tk.LEFT)
        self.iso_axis = tk.StringVar(value="Length")
        ttk.Combobox(yrow, textvariable=self.iso_axis, state="readonly", width=15,
                     values=[lbl for lbl, _k in self.ISO_FEATURES]).pack(side=tk.LEFT)
        zrow = ttk.Frame(bottom); zrow.pack(fill=tk.X, pady=1)
        ttk.Label(zrow, text="Z:", width=2).pack(side=tk.LEFT)
        self.iso_zaxis = tk.StringVar(value="Timbre")
        ttk.Combobox(zrow, textvariable=self.iso_zaxis, state="readonly", width=15,
                     values=[lbl for lbl, _k in self.ISO_FEATURES if _k is not None]).pack(side=tk.LEFT)
        self.iso_axis.trace_add("write", lambda *_: self._redraw_cloud())
        self.iso_zaxis.trace_add("write", lambda *_: self._redraw_cloud())

        # Scrollable checkbox list fills the middle (canvas + scrollbar in their
        # own container so LEFT/RIGHT packing never collides with the sidebar).
        listwrap = ttk.Frame(side)
        listwrap.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6)
        gc = tk.Canvas(listwrap, highlightthickness=0, bg="#f0f0f0")
        gsb = ttk.Scrollbar(listwrap, orient=tk.VERTICAL, command=gc.yview)
        gc.configure(yscrollcommand=gsb.set)
        gsb.pack(side=tk.RIGHT, fill=tk.Y)
        gc.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.group_box = ttk.Frame(gc)
        self._gc_win = gc.create_window((0, 0), window=self.group_box, anchor="nw")
        self.group_box.bind("<Configure>", lambda e: gc.configure(scrollregion=gc.bbox("all")))
        gc.bind("<Configure>", lambda e: gc.itemconfigure(self._gc_win, width=e.width))

        # --- right: the 3D cloud, fills the rest ---
        right = ttk.Frame(body)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.fig = Figure(figsize=(7, 4.4), dpi=100, facecolor="#1b1b1b")
        self.ax = self.fig.add_subplot(111, projection="3d", facecolor="#0f0f0f")
        self.fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
        self._style_axes()
        self.scatter = self.ax.scatter([], [], [], depthshade=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        cw = self.canvas.get_tk_widget()
        cw.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.canvas.mpl_connect("scroll_event", self._on_scroll)
        self.canvas.mpl_connect("button_press_event", self._on_click_point)
        # Arrow keys orbit the camera (widget grabs focus on hover/click).
        cw.configure(takefocus=True)
        cw.bind("<Enter>", lambda e: cw.focus_set())
        cw.bind("<Left>", lambda e: self._orbit(-12, 0))
        cw.bind("<Right>", lambda e: self._orbit(12, 0))
        cw.bind("<Up>", lambda e: self._orbit(0, 12))
        cw.bind("<Down>", lambda e: self._orbit(0, -12))
        self.selected_rec = None

    def _style_axes(self):
        self.ax.set_xlabel("Pitch (Hz)", color="#aaa", labelpad=8)
        self.ax.set_ylabel("Name group", color="#aaa", labelpad=12)
        self.ax.set_zlabel("Complexity / Timbre", color="#aaa", labelpad=6)
        self.ax.set_title("Live 3D sample cloud — depth = name group · size = length", color="#f4902c")
        self.ax.tick_params(colors="#888")
        try:
            self.ax.set_facecolor("#0f0f0f")
            for pane in (self.ax.xaxis, self.ax.yaxis, self.ax.zaxis):
                pane.set_pane_color((0.06, 0.06, 0.06, 1.0))
                pane._axinfo["grid"]["color"] = (0.2, 0.2, 0.2, 1.0)
        except Exception:
            pass
        self._apply_zoom()

    def _color_for(self, groups, g):
        return CLOUD_PALETTE[max(0, groups.index(g)) % len(CLOUD_PALETTE)]

    # Features that can replace the Y / Z axes when a single group is isolated.
    ISO_FEATURES = [
        ("Group", None), ("Length", "length"), ("Timbre", "timbre"),
        ("Complexity", "complexity"), ("Brightness (centroid)", "centroid"),
        ("Harmonicity", "harmonicity"), ("Sustain", "sustain"), ("Attack", "attack"),
        ("Pitch", "pitch"), ("BPM", "bpm"), ("RMS", "rms"), ("ZCR", "zcr"),
        ("Roll-off", "rolloff"), ("Flatness", "flatness"),
    ]
    CATEGORICAL_AXES = {"timbre"}

    def _feat_key(self, label):
        for l, k in self.ISO_FEATURES:
            if l == label:
                return k
        return None

    def _iso_key(self):
        return self._feat_key(self.iso_axis.get())

    def _iso_zkey(self):
        return self._feat_key(self.iso_zaxis.get())

    @staticmethod
    def _deeper_sub(r):
        """The record's subgroup when it's a *curated* level (Perc→Conga,
        Keyboards→Synth) rather than the auto "group + length tier" one.
        Returns "" when the subgroup is just the group (e.g. "Kick Short")."""
        g = (r.get("group") or "").strip()
        sg = (r.get("subgroup") or "").strip()
        gl, sgl = g.lower(), sg.lower()
        if sg and sgl != gl and not sgl.startswith(gl) and not gl.startswith(sgl):
            return sg
        return ""

    def _axis_values(self, recs, key, groups):
        """Return (values, label, ticks) for an axis. key=None -> group depth;
        key in CATEGORICAL_AXES -> categorical index; else numeric feature."""
        label = next((l for l, k in self.ISO_FEATURES if k == key), key or "Name group")
        if key is None:
            # Hierarchical depth: each group, with its curated subgroups one
            # level deeper (indented) directly beneath it.
            def gof(r):
                return r.get("group", "Other") or "Other"
            per_group = {}
            for r in recs:
                per_group.setdefault(gof(r), set()).add(self._deeper_sub(r))
            levels = []
            for g in sorted(per_group):
                subs = per_group[g]
                if "" in subs:
                    levels.append((g, ""))          # samples that sit at the group level
                for s in sorted(x for x in subs if x):
                    levels.append((g, s))           # a name group deeper
            lidx = {lv: i for i, lv in enumerate(levels)}
            vals = np.array([lidx[(gof(r), self._deeper_sub(r))] for r in recs], dtype=float)
            names = [g if s == "" else f"  ↳ {s}" for g, s in levels]
            return vals, "Group / subgroup", (list(range(len(levels))), names)
        if key in self.CATEGORICAL_AXES:
            cats = sorted(set((r.get(key) or "?") for r in recs))
            cidx = {c: i for i, c in enumerate(cats)}
            vals = np.array([cidx[r.get(key) or "?"] for r in recs], dtype=float)
            return vals, label, (list(range(len(cats))), cats)
        if key == "complexity":
            # Mono files dip below zero on the complexity axis (stereo stays +).
            vals = np.array([(-1.0 if (r.get("channels", 2) or 2) == 1 else 1.0) * (r.get("complexity", 0) or 0)
                             for r in recs], dtype=float)
            return vals, "Complexity (mono = −)", None
        vals = np.array([r.get(key, 0) or 0 for r in recs], dtype=float)
        return vals, label, None

    def _sync_group_checkboxes(self, all_groups):
        """(Re)build the group show/hide checkboxes when the group set changes."""
        if all_groups == self._group_box_keys:
            return
        for w in self.group_box.winfo_children():
            w.destroy()
        for g in all_groups:
            var = self.group_vars.get(g)
            if var is None:
                var = tk.BooleanVar(value=True)
                self.group_vars[g] = var
            cb = tk.Checkbutton(self.group_box, text=g, variable=var, anchor="w",
                                bg="#f0f0f0", activebackground="#f0f0f0",
                                command=self._redraw_cloud)
            cb.pack(fill=tk.X, anchor="w")
        self._group_box_keys = list(all_groups)

    def _set_all_groups(self, on):
        for var in self.group_vars.values():
            var.set(on)
        self._redraw_cloud()

    def _apply_zoom(self):
        # Modern matplotlib: box_aspect(zoom=...); fall back to camera distance.
        try:
            self.ax.set_box_aspect(None, zoom=self._zoom)
        except Exception:
            try:
                self.ax.dist = 10.0 / max(0.2, self._zoom)
            except Exception:
                pass

    def _on_scroll(self, event):
        step = 1.15 if getattr(event, "button", "up") == "up" else 1.0 / 1.15
        self._zoom = max(0.4, min(6.0, self._zoom * step))
        self._apply_zoom()
        self.canvas.draw_idle()

    def _set_view(self, elev, azim):
        self.ax.view_init(elev=elev, azim=azim)
        self.canvas.draw_idle()

    def _orbit(self, d_azim, d_elev):
        try:
            elev = max(-89, min(89, (self.ax.elev or 0) + d_elev))
            azim = (self.ax.azim or 0) + d_azim
            self.ax.view_init(elev=elev, azim=azim)
            self.canvas.draw_idle()
        except Exception:
            pass
        return "break"

    # ---- click-to-inspect + play -----------------------------------------
    def _on_click_point(self, event):
        if event.inaxes != self.ax or self._pts is None or event.x is None:
            return
        xs, ys, zs = self._pts
        if len(xs) == 0:
            return
        # Project the 3D points to display pixels and pick the nearest.
        xp, yp, _ = proj3d.proj_transform(xs, ys, zs, self.ax.get_proj())
        disp = self.ax.transData.transform(np.column_stack([xp, yp]))
        d2 = (disp[:, 0] - event.x) ** 2 + (disp[:, 1] - event.y) ** 2
        i = int(np.argmin(d2))
        if d2[i] > 900:  # >30 px away — treat as an orbit drag, not a pick
            return
        self._select_point(i)

    def _select_point(self, i):
        if i < 0 or i >= len(self._pt_recs):
            return
        rec = self._pt_recs[i]
        self.selected_rec = rec
        self.play_btn.config(state=tk.NORMAL)
        self.sel_label.config(text=rec.get("name", "")[:40])

        # Overlay the PEAK record to the side of the graph.
        ch = rec.get("channels")
        title = rec.get("name", "") + (" (mono)" if ch == 1 else "")
        lines = [title]
        fld = rec.get("folder", "")
        if fld:
            lines.append("dir: " + fld)
        lines.append("")
        for k, label, fmt in (
            ("group", "group", "{}"), ("reason", "reason", "{}"), ("timbre", "timbre", "{}"),
            ("cluster", "cluster", "{}"), ("root", "root", "{}"), ("pitch", "pitch", "{:.0f} Hz"),
            ("centroid", "brightness", "{:.0f} Hz"), ("harmonicity", "harmonicity", "{:.2f}"),
            ("complexity", "complexity", "{:.1f}"), ("attack", "attack", "{:.3f} s"),
            ("length", "length", "{:.2f} s"), ("transients", "transients", "{}"),
            ("bpm", "bpm", "{:.1f}"), ("sample_rate", "sample rate", "{} Hz"), ("bit_depth", "bits", "{}"),
        ):
            v = rec.get(k)
            if v in (None, "", 0) and k in ("bpm", "cluster"):
                continue
            try:
                lines.append(f"{label}: " + fmt.format(v))
            except Exception:
                lines.append(f"{label}: {v}")
        lines.append("channels: " + ("mono" if ch == 1 else "stereo" if ch == 2 else str(ch)))
        if rec.get("sustained"):
            lines.append("* sustained single note")
        if rec.get("audit"):
            lines.append("! generic 'drum' tag — needs audit")
        text = "\n".join(lines)

        if self._sel_txt is not None:
            try:
                self._sel_txt.remove()
            except Exception:
                pass
        self._sel_txt = self.ax.text2D(
            0.985, 0.98, text, transform=self.ax.transAxes, ha="right", va="top",
            fontsize=8, color="#e8e8c0", family="monospace",
            bbox=dict(boxstyle="round", facecolor="#101010", edgecolor="#f4902c", alpha=0.9))

        # Highlight the picked point.
        xs, ys, zs = self._pts
        if self._sel_marker is not None:
            try:
                self._sel_marker.remove()
            except Exception:
                pass
        self._sel_marker = self.ax.scatter([xs[i]], [ys[i]], [zs[i]], s=260,
                                           facecolors="none", edgecolors="#ffffff", linewidths=1.8, depthshade=False)
        self.canvas.draw_idle()
        self._play_selected()

    def _redraw_cloud(self):
        if not self.d_rec:
            return
        # Preserve the user's current view angle across live updates.
        elev, azim = self.ax.elev, self.ax.azim

        def grp(r):
            return r.get("group", "Other") or "Other"

        all_groups = sorted(set(grp(r) for r in self.d_rec))
        self._sync_group_checkboxes(all_groups)
        visible = {g for g in all_groups if g not in self.group_vars or self.group_vars[g].get()}
        recs = [r for r in self.d_rec if grp(r) in visible]

        if not recs:
            self.scatter._offsets3d = ([], [], [])
            self._pts = (np.array([]), np.array([]), np.array([]))
            self._pt_recs = []
            self.ax.set_title("(all groups hidden)", color="#888", fontsize=9)
            self.canvas.draw_idle()
            return

        groups = sorted(set(grp(r) for r in recs))
        iso_key = self._iso_key()
        isolated = len(groups) == 1 and iso_key is not None

        xs = np.array([r.get("pitch", 0) or 0 for r in recs], dtype=float)
        if isolated:
            ys, ylabel, yticks = self._axis_values(recs, iso_key, groups)
            zs, zlabel, zticks = self._axis_values(recs, self._iso_zkey(), groups)
        else:
            ys, ylabel, yticks = self._axis_values(recs, None, groups)
            zs, zlabel, zticks = self._axis_values(recs, "complexity", groups)

        lens = [r.get("length", 0.1) or 0.1 for r in recs]
        lmin, lmax = min(lens), max(lens)
        span = (lmax - lmin) or 1.0
        sizes = np.array([25 + ((l - lmin) / span) * 260 for l in lens])
        colors = [self._color_for(groups, grp(r)) for r in recs]

        self._pts = (xs, ys, zs)
        self._pt_recs = recs
        self.scatter._offsets3d = (xs, ys, zs)
        self.scatter.set_sizes(sizes)
        self.scatter.set_color(colors)
        self.scatter.set_edgecolor("none")

        self.ax.set_xlim(0, float(xs.max()) * 1.1 + 1)

        def _apply_axis(setlim, setticks, setlabels, setlabel, vals, label, ticks):
            setlabel(label, color="#aaa", labelpad=10)
            if ticks is not None:
                positions, names = ticks
                setlim(-0.5, max(0.5, len(positions) - 0.5))
                setticks(positions)
                setlabels(names, fontsize=7, color="#bbb")
            else:
                vmin = float(vals.min())
                vmax = float(vals.max())
                lo = min(0.0, vmin * 1.1)
                hi = max(vmax * 1.1, lo + 1e-6)
                setlim(lo, hi)
                ticks = np.linspace(lo, hi, 5)
                setticks(ticks)
                setlabels([f"{v:.2g}" for v in ticks], fontsize=7, color="#bbb")

        _apply_axis(self.ax.set_ylim, self.ax.set_yticks, self.ax.set_yticklabels,
                    self.ax.set_ylabel, ys, ylabel, yticks)
        _apply_axis(self.ax.set_zlim, self.ax.set_zticks, self.ax.set_zticklabels,
                    self.ax.set_zlabel, zs, zlabel, zticks)

        # Rebuild the colour legend when the visible set / axis mode changes.
        legend_key = (tuple(groups), isolated, ylabel, zlabel)
        if legend_key != self._legend_groups:
            handles = [Line2D([0], [0], marker="o", linestyle="", markersize=6,
                              markerfacecolor=self._color_for(groups, g), markeredgecolor="none", label=g)
                       for g in groups]
            leg = self.ax.legend(handles=handles, loc="upper left", fontsize=7, ncol=1,
                                 facecolor="#1b1b1b", edgecolor="#333", labelcolor="#ccc",
                                 framealpha=0.85, bbox_to_anchor=(0.0, 1.0))
            if leg:
                leg.set_title("Name group", prop={"size": 7})
                if leg.get_title():
                    leg.get_title().set_color("#888")
            self._legend_groups = legend_key

        n = len(recs)
        extra = f" · ISOLATED {groups[0]}: Y={ylabel}, Z={zlabel}" if isolated else ""
        self.ax.set_title(
            f"{n} shown  ·  {len(groups)}/{len(all_groups)} groups  ·  size = length{extra}",
            color="#f4902c", fontsize=9)

        self.ax.view_init(elev=elev, azim=azim)
        self.canvas.draw_idle()
