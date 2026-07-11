#!/usr/bin/env python3
"""Sample Analyzer GUI.

The heavy DSP now lives in the Rust binary `oa_sample_analyzer` (see
sample_analyzer_rs/). This script is only the GUI: it picks a folder, launches
the Rust analyzer (30 parallel workers), reads its streamed JSON progress, and
draws a LIVE 3D cloud of the "magic" while the analysis runs — the same cloud
the web front-end shows in SoundBrowse ▸ THE CLOUD:

    X = pitch (Hz)   ·   Y (depth) = name group   ·   Z = complexity / timbre
    point size = sample length   ·   colour = name group (legend)

The Rust process writes `sample_cloud_data.PEAK` with each file's name + folder.
"""
import os
import sys
import csv
import json
import queue
import shutil
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d import Axes3D, proj3d  # noqa: F401 (registers the 3d projection)
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

HERE = os.path.dirname(os.path.abspath(__file__))

# Same palette the web cloud uses, so the two graphs colour groups identically.
CLOUD_PALETTE = [
    "#f4902c", "#8ab4f8", "#4caf50", "#e57373", "#ba68c8", "#4dd0e1",
    "#ffd54f", "#a1887f", "#90a4ae", "#f06292", "#aed581", "#7986cb",
    "#ff8a65", "#4db6ac", "#dce775", "#9575cd", "#ffffff",
]


def find_binary():
    """Locate the built Rust analyzer binary (build it if missing)."""
    exe = "oa_sample_analyzer" + (".exe" if os.name == "nt" else "")
    candidates = [
        os.path.join(HERE, "sample_analyzer_rs", "target", "release", exe),
        os.path.join(HERE, "sample_analyzer_rs", "target", "debug", exe),
        shutil.which("oa_sample_analyzer"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


class AnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sample Analyzer (Rust core)")
        self.root.geometry("820x640")

        self.directory = tk.StringVar(value="No directory selected")
        self.binary = find_binary()
        self.is_analyzing = False
        self.q = queue.Queue()
        self.proc = None

        # live cloud data — one entry per analyzed file
        self.d_pitch = []   # X
        self.d_cx = []      # Z (complexity)
        self.d_len = []     # size
        self.d_group = []   # name group -> Y depth + colour
        self.d_rec = []     # full streamed record per point (for click/inspect)
        self.n_loops = 0
        self._legend_groups = None  # last group set drawn in the legend
        self._zoom = 1.0            # scroll-wheel zoom factor
        self._pts = None            # (xs, ys, zs) of current cloud, for picking
        self._sel_txt = None        # overlay annotation for the selected point
        self._sel_marker = None     # highlight marker for the selected point

        # full records (from the .PEAK file) for the Groups / Examiner tabs
        self.records = []
        self.peak_path = None
        self.root_dir = None        # scanned root, to resolve sample paths

        self._build_ui()
        self.root.after(60, self._drain_queue)

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Directory:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(top, textvariable=self.directory, foreground="#c47a1a", wraplength=520).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(top, text="Browse…", command=self.browse).pack(side=tk.RIGHT)

        row = ttk.Frame(self.root, padding=(10, 0))
        row.pack(fill=tk.X)
        self.progress = ttk.Progressbar(row, orient=tk.HORIZONTAL, mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.action_btn = ttk.Button(row, text="Start Analysis", command=self.start, state=tk.DISABLED)
        self.action_btn.pack(side=tk.RIGHT)

        self.status = ttk.Label(self.root, text=("Rust binary: " + (self.binary or "NOT BUILT — run: cargo build --release in sample_analyzer_rs/")),
                                foreground=("#2a7" if self.binary else "#c33"), padding=(10, 4))
        self.status.pack(fill=tk.X)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self._build_cloud_tab()
        self._build_groups_tab()
        self._build_examiner_tab()

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

        # Live 3D cloud — fill the whole panel, minimal margins.
        self.fig = Figure(figsize=(7, 4.4), dpi=100, facecolor="#1b1b1b")
        self.ax = self.fig.add_subplot(111, projection="3d", facecolor="#0f0f0f")
        self.fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
        self._style_axes()
        self.scatter = self.ax.scatter([], [], [], depthshade=True)
        self.canvas = FigureCanvasTkAgg(self.fig, master=tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        self.canvas.mpl_connect("scroll_event", self._on_scroll)
        self.canvas.mpl_connect("button_press_event", self._on_click_point)
        self.selected_rec = None

    # ---- Groups / CSV tab -------------------------------------------------
    GROUP_COLS = ("folder", "reason", "timbre", "cluster", "pitch", "length", "tr")

    def _build_groups_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Groups / CSV")

        ctl = ttk.Frame(tab, padding=6)
        ctl.pack(fill=tk.X)
        ttk.Label(ctl, text="Group by:").pack(side=tk.LEFT, padx=(0, 4))
        self.group_by = tk.StringVar(value="Name group")
        cb = ttk.Combobox(ctl, textvariable=self.group_by, state="readonly", width=13,
                          values=["Name group", "Timbre", "Cluster"])
        cb.pack(side=tk.LEFT, padx=4)
        cb.bind("<<ComboboxSelected>>", lambda e: self._rebuild_groups())
        ttk.Button(ctl, text="Expand all", command=lambda: self._groups_expand(True)).pack(side=tk.LEFT, padx=(10, 2))
        ttk.Button(ctl, text="Collapse all", command=lambda: self._groups_expand(False)).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctl, text="Export CSV…", command=self._export_csv).pack(side=tk.LEFT, padx=(10, 2))
        self.groups_summary = ttk.Label(ctl, text="No analysis yet", foreground="#888")
        self.groups_summary.pack(side=tk.RIGHT)

        wrap = ttk.Frame(tab)
        wrap.pack(fill=tk.BOTH, expand=True)
        tv = ttk.Treeview(wrap, columns=self.GROUP_COLS, show="tree headings")
        tv.heading("#0", text="Group / File")
        tv.column("#0", width=260, stretch=True)
        heads = {"folder": ("Folder", 160), "reason": ("Reason in group", 180), "timbre": ("Timbre", 90),
                 "cluster": ("Clust", 50), "pitch": ("Pitch", 60), "length": ("Len s", 60), "tr": ("Trans", 50)}
        for c in self.GROUP_COLS:
            label, w = heads[c]
            tv.heading(c, text=label)
            tv.column(c, width=w, anchor=tk.W)
        vs = ttk.Scrollbar(wrap, orient=tk.VERTICAL, command=tv.yview)
        tv.configure(yscrollcommand=vs.set)
        vs.pack(side=tk.RIGHT, fill=tk.Y)
        tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.groups_tv = tv

    # ---- PEAK examiner tab ------------------------------------------------
    EXAM_COLS = ("group", "reason", "timbre", "cluster", "pitch", "length", "tr",
                 "centroid", "harm", "bpm", "sr", "bits")

    def _build_examiner_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="PEAK Examiner")

        ctl = ttk.Frame(tab, padding=6)
        ctl.pack(fill=tk.X)
        ttk.Button(ctl, text="Open .PEAK…", command=self._open_peak_file).pack(side=tk.LEFT)
        ttk.Label(ctl, text="Filter:").pack(side=tk.LEFT, padx=(12, 4))
        self.exam_filter = tk.StringVar()
        ent = ttk.Entry(ctl, textvariable=self.exam_filter, width=24)
        ent.pack(side=tk.LEFT)
        ent.bind("<KeyRelease>", lambda e: self._populate_examiner())
        self.exam_summary = ttk.Label(ctl, text="No PEAK loaded", foreground="#888")
        self.exam_summary.pack(side=tk.RIGHT)

        body = ttk.Panedwindow(tab, orient=tk.VERTICAL)
        body.pack(fill=tk.BOTH, expand=True)

        wrap = ttk.Frame(body)
        tv = ttk.Treeview(wrap, columns=self.EXAM_COLS, show="tree headings")
        tv.heading("#0", text="File")
        tv.column("#0", width=220, stretch=True)
        heads = {"group": ("Group", 80), "reason": ("Reason", 150), "timbre": ("Timbre", 80),
                 "cluster": ("Clust", 48), "pitch": ("Pitch", 55), "length": ("Len", 50),
                 "tr": ("Tr", 40), "centroid": ("Cntrd", 60), "harm": ("Harm", 50),
                 "bpm": ("BPM", 50), "sr": ("SR", 55), "bits": ("Bits", 40)}
        for c in self.EXAM_COLS:
            label, w = heads[c]
            tv.heading(c, text=label)
            tv.column(c, width=w, anchor=tk.W)
        vs = ttk.Scrollbar(wrap, orient=tk.VERTICAL, command=tv.yview)
        tv.configure(yscrollcommand=vs.set)
        vs.pack(side=tk.RIGHT, fill=tk.Y)
        tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tv.bind("<<TreeviewSelect>>", self._examiner_select)
        self.exam_tv = tv
        body.add(wrap, weight=3)

        self.exam_detail = tk.Text(body, height=9, bg="#0f0f0f", fg="#cfcf9f",
                                   insertbackground="#ccc", font=("Courier", 9), wrap=tk.NONE)
        body.add(self.exam_detail, weight=1)

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
        if i < 0 or i >= len(self.d_rec):
            return
        rec = self.d_rec[i]
        self.selected_rec = rec
        self.play_btn.config(state=tk.NORMAL)
        self.sel_label.config(text=rec.get("name", "")[:40])

        # Overlay the PEAK record to the side of the graph.
        lines = [rec.get("name", "")]
        fld = rec.get("folder", "")
        if fld:
            lines.append("📁 " + fld)
        lines.append("")
        for k, label, fmt in (
            ("group", "group", "{}"), ("reason", "reason", "{}"), ("timbre", "timbre", "{}"),
            ("cluster", "cluster", "{}"), ("pitch", "pitch", "{:.0f} Hz"),
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

    def _resolve_path(self, rec):
        if rec.get("path") and os.path.isfile(rec["path"]):
            return rec["path"]
        root = self.root_dir or (self.directory.get() if os.path.isdir(self.directory.get()) else None)
        if root:
            p = os.path.join(root, rec.get("folder", ""), rec.get("name", ""))
            if os.path.isfile(p):
                return p
        return None

    def _play_selected(self):
        if not self.selected_rec:
            return
        path = self._resolve_path(self.selected_rec)
        if path:
            self._play_file(path)
        else:
            self.sel_label.config(text="⚠ file not found")

    def _play_file(self, path):
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif os.name == "nt":
                import winsound
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                player = shutil.which("paplay") or shutil.which("aplay") or shutil.which("ffplay")
                if not player:
                    self.sel_label.config(text="⚠ no audio player (install pulseaudio/alsa)")
                    return
                cmd = [player, "-nodisp", "-autoexit", path] if player.endswith("ffplay") else [player, path]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            self.sel_label.config(text="⚠ " + str(e)[:30])

    # ---- Groups / CSV -----------------------------------------------------
    def _group_key(self, rec):
        by = self.group_by.get()
        if by == "Timbre":
            return rec.get("timbre") or "Other"
        if by == "Cluster":
            return "Cluster " + str(rec.get("cluster", -1))
        return rec.get("group") or "Other"

    def _rebuild_groups(self):
        tv = self.groups_tv
        tv.delete(*tv.get_children())
        buckets = {}
        for r in self.records:
            buckets.setdefault(self._group_key(r), []).append(r)
        for g in sorted(buckets):
            rows = buckets[g]
            parent = tv.insert("", "end", text=f"{g}  ({len(rows)})", open=False,
                               values=("", "", "", "", "", "", ""))
            for r in sorted(rows, key=lambda x: x.get("name", "")):
                tv.insert(parent, "end", text=r.get("name", ""), values=(
                    r.get("folder", ""), r.get("reason", ""), r.get("timbre", ""),
                    r.get("cluster", ""), f"{r.get('pitch', 0):.0f}",
                    f"{r.get('length', 0):.2f}", r.get("transients", "")))
        self.groups_summary.config(text=f"{len(self.records)} files · {len(buckets)} groups")

    def _groups_expand(self, opened):
        for item in self.groups_tv.get_children():
            self.groups_tv.item(item, open=opened)

    def _export_csv(self):
        if not self.records:
            messagebox.showinfo("Export CSV", "No analysis loaded yet.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile="sample_groups.csv",
            filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if not path:
            return
        cols = ["group_dimension", "group", "name", "folder", "reason", "timbre", "cluster",
                "pitch", "complexity", "centroid", "harmonicity", "attack", "length",
                "transients", "bpm", "sample_rate", "bit_depth"]
        by = self.group_by.get()
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(cols)
                for r in sorted(self.records, key=lambda x: (self._group_key(x), x.get("name", ""))):
                    w.writerow([by, self._group_key(r)] + [r.get(c, "") for c in
                                ["name", "folder", "reason", "timbre", "cluster", "pitch",
                                 "complexity", "centroid", "harmonicity", "attack", "length",
                                 "transients", "bpm", "sample_rate", "bit_depth"]])
            messagebox.showinfo("Export CSV", f"Wrote {len(self.records)} rows to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export CSV", str(e))

    # ---- PEAK examiner ----------------------------------------------------
    def _open_peak_file(self):
        path = filedialog.askopenfilename(
            title="Open .PEAK file",
            filetypes=[("PEAK / JSON", "*.PEAK *.peak *.json"), ("All", "*.*")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self.exam_records = data if isinstance(data, list) else []
            self.exam_path = path
            self._populate_examiner()
        except Exception as e:
            messagebox.showerror("Open PEAK", str(e))

    def _populate_examiner(self):
        tv = self.exam_tv
        tv.delete(*tv.get_children())
        recs = getattr(self, "exam_records", [])
        flt = (self.exam_filter.get() or "").lower()
        shown = 0
        for r in recs:
            if flt and flt not in (r.get("name", "") + " " + r.get("folder", "") + " "
                                   + str(r.get("group", "")) + " " + str(r.get("timbre", ""))).lower():
                continue
            tv.insert("", "end", text=r.get("name", ""), values=(
                r.get("group", ""), r.get("reason", ""), r.get("timbre", ""), r.get("cluster", ""),
                f"{r.get('pitch', 0):.0f}", f"{r.get('length', 0):.2f}", r.get("transients", ""),
                f"{r.get('centroid', 0):.0f}", f"{r.get('harmonicity', 0):.2f}",
                f"{r.get('bpm', 0):.0f}", r.get("sample_rate", ""), r.get("bit_depth", "")))
            shown += 1
        groups = len({r.get("group") for r in recs})
        self.exam_summary.config(text=f"{getattr(self, 'exam_path', '')}  —  {shown}/{len(recs)} shown · {groups} groups")

    def _examiner_select(self, event):
        tv = self.exam_tv
        sel = tv.selection()
        if not sel:
            return
        name = tv.item(sel[0], "text")
        rec = next((r for r in getattr(self, "exam_records", []) if r.get("name") == name), None)
        self.exam_detail.delete("1.0", tk.END)
        if rec:
            self.exam_detail.insert(tk.END, json.dumps(rec, indent=2))

    def browse(self):
        if self.is_analyzing:
            return
        d = filedialog.askdirectory(title="Select Folder to Analyze")
        if d:
            self.directory.set(d)
            self.action_btn.config(state=(tk.NORMAL if self.binary else tk.DISABLED))

    def start(self):
        if self.is_analyzing or not self.binary:
            return
        directory = self.directory.get()
        if not os.path.isdir(directory):
            messagebox.showerror("Error", "Invalid directory.")
            return
        self.is_analyzing = True
        self.root_dir = directory
        self.action_btn.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.d_pitch, self.d_cx, self.d_len, self.d_group, self.d_rec = [], [], [], [], []
        self.n_loops = 0
        self._legend_groups = None
        self._pts = None
        self.selected_rec = None
        self._sel_txt = None
        self._sel_marker = None
        self.play_btn.config(state=tk.DISABLED)
        self.ax.clear(); self._style_axes()
        self.scatter = self.ax.scatter([], [], [], depthshade=True)
        if self.ax.get_legend():
            self.ax.get_legend().remove()
        self.canvas.draw_idle()
        threading.Thread(target=self._run, args=(directory,), daemon=True).start()

    def _run(self, directory):
        try:
            self.proc = subprocess.Popen(
                [self.binary, directory, "--workers", "30"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1,
            )
            for line in self.proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    self.q.put(json.loads(line))
                except json.JSONDecodeError:
                    pass
            self.proc.wait()
        except Exception as e:
            self.q.put({"type": "error", "msg": str(e)})
        finally:
            self.q.put({"type": "finished"})

    def _drain_queue(self):
        redraw = False
        try:
            for _ in range(2000):
                msg = self.q.get_nowait()
                t = msg.get("type")
                if t == "start":
                    self.progress.config(maximum=max(1, msg.get("total", 1)))
                elif t in ("result", "skip"):
                    self.progress["value"] = msg.get("done", 0)
                    if t == "result":
                        self.d_pitch.append(msg.get("pitch", 0.0) or 0.0)
                        self.d_cx.append(msg.get("complexity", 0.0) or 0.0)
                        self.d_len.append(msg.get("length", 0.1) or 0.1)
                        self.d_group.append(msg.get("group", "Other") or "Other")
                        self.d_rec.append(msg)
                        if (msg.get("transients", 1) or 1) > 1:
                            self.n_loops += 1
                        redraw = True
                elif t == "done":
                    out = msg.get("out", "")
                    self.status.config(text=f"Done — {msg.get('count', 0)} samples → {out}", foreground="#2a7")
                    self._load_records(out)
                elif t == "error":
                    self.status.config(text="Error: " + msg.get("msg", ""), foreground="#c33")
                elif t == "finished":
                    self.is_analyzing = False
                    self.action_btn.config(state=tk.NORMAL)
        except queue.Empty:
            pass
        if redraw and self.d_pitch:
            self._redraw_cloud()
        self.root.after(120, self._drain_queue)

    def _redraw_cloud(self):
        # Preserve the user's current view angle across live updates.
        elev, azim = self.ax.elev, self.ax.azim

        groups = sorted(set(self.d_group))
        gidx = {g: i for i, g in enumerate(groups)}
        xs = np.array(self.d_pitch, dtype=float)
        ys = np.array([gidx[g] for g in self.d_group], dtype=float)  # depth = name group
        zs = np.array(self.d_cx, dtype=float)

        # size = length (bigger file span -> bigger dot).
        lmin = min(self.d_len); lmax = max(self.d_len)
        span = (lmax - lmin) or 1.0
        sizes = np.array([25 + ((l - lmin) / span) * 260 for l in self.d_len])
        colors = [self._color_for(groups, g) for g in self.d_group]

        self._pts = (xs, ys, zs)  # remember for click-picking
        # Update the single collection in place (keeps it fast + smooth).
        self.scatter._offsets3d = (xs, ys, zs)
        self.scatter.set_sizes(sizes)
        self.scatter.set_color(colors)
        self.scatter.set_edgecolor("none")

        self.ax.set_xlim(0, float(xs.max()) * 1.1 + 1)
        self.ax.set_zlim(0, float(zs.max()) * 1.1 + 1)
        self.ax.set_ylim(-0.5, len(groups) - 0.5)
        self.ax.set_yticks(range(len(groups)))
        self.ax.set_yticklabels(groups, fontsize=7, color="#bbb")

        # Rebuild the colour legend only when the set of groups changes.
        if groups != self._legend_groups:
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
            self._legend_groups = groups

        n = len(self.d_pitch)
        self.ax.set_title(
            f"{n} samples  ·  {len(groups)} groups  ·  {self.n_loops} loops  ·  size = length",
            color="#f4902c", fontsize=9)

        self.ax.view_init(elev=elev, azim=azim)
        self.canvas.draw_idle()

    def _load_records(self, out_path):
        """Load the full .PEAK records (all fields) for the Groups + Examiner tabs."""
        try:
            with open(out_path, encoding="utf-8") as f:
                data = json.load(f)
            self.records = data if isinstance(data, list) else []
            self.peak_path = out_path
            # Prefer the authoritative full records for click-inspect too.
            if self.records and len(self.records) == len(self.d_rec):
                self.d_rec = self.records
            self._rebuild_groups()
            # Auto-load the same file into the examiner.
            self.exam_records = self.records
            self.exam_path = out_path
            self._populate_examiner()
        except Exception as e:
            self.status.config(text="Loaded but could not read PEAK: " + str(e), foreground="#c33")


def main():
    root = tk.Tk()
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    AnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
